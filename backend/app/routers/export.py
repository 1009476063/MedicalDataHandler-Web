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
    format: str = "ct"
    dtype: str = "float32"
    unit: str = "native"
    anonymize: bool = False
    include_metadata: bool = True


_DTYPE_MAP = {
    "float32": np.float32,
    "float64": np.float64,
    "int16": np.int16,
    "int32": np.int32,
}


def _build_nrrd_buffer(
    session_id: str,
    patient_id: str,
    series_uid: Optional[str],
    fmt: str = "ct",
    dtype: str = "float32",
    unit: str = "native",
) -> Optional[io.BytesIO]:
    volume_data = image_builder.get_volume(session_id, patient_id, series_uid)
    if volume_data is None:
        return None

    array = volume_data["array"]
    target_dtype = _DTYPE_MAP.get(dtype, np.float32)

    # Apply format/unit conversion
    if fmt == "red" or unit == "red":
        array = np.where(array > -1000, (array + 1000) / 1000.0, 0.0)

    array = array.astype(target_dtype)

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
    nrrd.write(buf, array, header)
    buf.seek(0)
    return buf


@router.post("/nrrd")
async def export_nrrd(req: ExportRequest):
    buf = await asyncio.to_thread(
        _build_nrrd_buffer, req.session_id, req.patient_id, req.series_uid,
        req.format, req.dtype, req.unit,
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
async def export_nrrd_get(
    session_id: str, patient_id: str, series_uid: str,
    format: str = "ct", dtype: str = "float32", unit: str = "native",
):
    buf = await asyncio.to_thread(
        _build_nrrd_buffer, session_id, patient_id, series_uid, format, dtype, unit,
    )
    if buf is None:
        raise HTTPException(status_code=404, detail="Volume not found")
    filename = f"{patient_id}_{series_uid[:8]}.nrrd"
    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
