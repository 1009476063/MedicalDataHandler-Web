from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import nrrd
import io
import numpy as np
import gzip
import asyncio

from app.models.response import ApiResponse
from app.services.dicom_service import dicom_service
from app.services.image_builder import ImageBuilder

router = APIRouter()
image_builder = ImageBuilder()


class ExportRequest(BaseModel):
    session_id: str
    patient_id: str
    series_uid: Optional[str] = None
    format: str = "nrrd"
    anonymize: bool = False
    include_metadata: bool = True


def _build_nrrd_buffer(session_id: str, patient_id: str, series_uid: Optional[str]) -> Optional[io.BytesIO]:
    volume_data = image_builder.get_volume(session_id, patient_id, series_uid)
    if volume_data is None:
        return None
    spacing = [float(x) for x in volume_data["spacing"]]
    origin = [float(x) for x in volume_data["origin"]]
    header = {
        "space directions": [
            [spacing[0], 0.0, 0.0],
            [0.0, spacing[1], 0.0],
            [0.0, 0.0, spacing[2]],
        ],
        "space origin": origin,
    }
    buf = io.BytesIO()
    nrrd.write(buf, volume_data["array"], header)
    buf.seek(0)
    return buf


@router.post("/nrrd")
async def export_nrrd(req: ExportRequest):
    buf = await asyncio.to_thread(
        _build_nrrd_buffer, req.session_id, req.patient_id, req.series_uid,
    )
    if buf is None:
        raise HTTPException(status_code=404, detail="Volume not found")
    filename = f"{req.patient_id}_{'all' if not req.series_uid else req.series_uid}.nrrd"
    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/nrrd/{session_id}/{patient_id}/{series_uid}")
async def export_nrrd_get(session_id: str, patient_id: str, series_uid: str, format: str = "ct"):
    buf = await asyncio.to_thread(_build_nrrd_buffer, session_id, patient_id, series_uid)
    if buf is None:
        raise HTTPException(status_code=404, detail="Volume not found")
    filename = f"{patient_id}_{series_uid[:8]}.nrrd"
    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
