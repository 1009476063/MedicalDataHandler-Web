from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from typing import Optional
import pydicom
import numpy as np
import io
import json
import asyncio
from pathlib import Path

from app.models.response import ApiResponse
from app.utils.rate_limit import limiter
from app.services.dicom_service import dicom_service, MAX_CONCURRENT_UPLOADS
from app.services.image_builder import ImageBuilder
from app.services.rt_struct_builder import RTStructBuilder
from app.services.rt_dose_builder import RTDoseBuilder

router = APIRouter()
image_builder = ImageBuilder()
struct_builder = RTStructBuilder()
dose_builder = RTDoseBuilder()


class UploadResponse(BaseModel):
    session_id: str
    patients: list[dict]
    file_count: int


class PatientData(BaseModel):
    session_id: str
    patient_id: str


class SliceRequest(BaseModel):
    session_id: str
    patient_id: str
    series_uid: str
    orientation: str  # axial, sagittal, coronal
    slice_index: int = Field(ge=0)
    window_center: Optional[float] = None
    window_width: Optional[float] = None


class VolumeRequest(BaseModel):
    session_id: str
    patient_id: str
    series_uid: str


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_dicom(request: Request, files: list[UploadFile] = File(...)):
    if dicom_service._upload_slots <= 0:
        raise HTTPException(status_code=429, detail="Server busy, too many concurrent uploads. Try again later.")
    await dicom_service.upload_semaphore.acquire()
    dicom_service._upload_slots -= 1
    try:
        result = await dicom_service.process_upload(files)
        if result.get("error"):
            raise HTTPException(status_code=413, detail=result["error"])
        return result
    finally:
        dicom_service._upload_slots += 1
        dicom_service.upload_semaphore.release()


@router.get("/patients/{session_id}")
async def get_patients(session_id: str):
    patients = await asyncio.to_thread(dicom_service.get_patients, session_id)
    if not patients:
        raise HTTPException(status_code=404, detail="Session not found")
    return ApiResponse(success=True, data={"patients": patients})


@router.get("/patient/{session_id}/{patient_id}")
async def get_patient_detail(session_id: str, patient_id: str):
    detail = await asyncio.to_thread(dicom_service.get_patient_detail, session_id, patient_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Patient not found")
    return ApiResponse(success=True, data=detail)


@router.get("/metadata/{session_id}/{file_id}")
async def get_dicom_metadata(session_id: str, file_id: str):
    metadata = await asyncio.to_thread(dicom_service.get_file_metadata, session_id, file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return ApiResponse(success=True, data=metadata)


@router.post("/slice")
async def get_slice(req: SliceRequest):
    slice_data = await asyncio.to_thread(
        image_builder.get_slice,
        req.session_id, req.patient_id, req.series_uid,
        req.orientation, req.slice_index,
        req.window_center, req.window_width,
    )
    if slice_data is None:
        raise HTTPException(status_code=404, detail="Slice not found")

    # Prefetch adjacent slices in background (non-blocking)
    max_slice = slice_data.get("max_slice", 0)
    if max_slice > 1:
        asyncio.get_running_loop().run_in_executor(
            None,
            image_builder.prefetch_adjacent_slices,
            req.session_id, req.patient_id, req.series_uid,
            req.orientation, req.slice_index, max_slice,
            req.window_center, req.window_width,
        )

    return ApiResponse(success=True, data=slice_data)


@router.get("/series-info/{session_id}/{patient_id}/{series_uid}")
async def get_series_info(session_id: str, patient_id: str, series_uid: str):
    info = await asyncio.to_thread(image_builder.get_series_info, session_id, patient_id, series_uid)
    if not info:
        raise HTTPException(status_code=404, detail="Series not found")
    return ApiResponse(success=True, data=info)


@router.get("/structs/{session_id}/{patient_id}")
async def get_rt_structs(session_id: str, patient_id: str):
    structs = await asyncio.to_thread(struct_builder.get_structs, session_id, patient_id)
    return ApiResponse(success=True, data={"structures": structs or []})


@router.get("/struct-mask/{session_id}/{patient_id}/{struct_key}/{slice_index}")
async def get_struct_mask(
    session_id: str, patient_id: str, struct_key: str, slice_index: int,
    orientation: str = "axial"
):
    mask = await asyncio.to_thread(
        struct_builder.get_mask,
        session_id, patient_id, struct_key, slice_index, orientation,
    )
    if mask is None:
        raise HTTPException(status_code=404, detail="Mask not found")
    return ApiResponse(success=True, data=mask)


@router.get("/dose/{session_id}/{patient_id}/{dose_uid}/{slice_index}")
async def get_dose_slice(
    session_id: str, patient_id: str, dose_uid: str, slice_index: int,
    orientation: str = "axial"
):
    dose = await asyncio.to_thread(
        dose_builder.get_dose_slice,
        session_id, patient_id, dose_uid, slice_index, orientation,
    )
    if dose is None:
        raise HTTPException(status_code=404, detail="Dose not found")
    return ApiResponse(success=True, data=dose)


@router.get("/dose-info/{session_id}/{patient_id}")
async def get_dose_info(session_id: str, patient_id: str):
    info = await asyncio.to_thread(dose_builder.get_dose_info, session_id, patient_id)
    return ApiResponse(success=True, data={"doses": info or []})


@router.get("/roi-bounds/{session_id}/{patient_id}/{struct_key}")
async def get_roi_bounds(session_id: str, patient_id: str, struct_key: str):
    bounds = await asyncio.to_thread(
        struct_builder.get_roi_bounds, session_id, patient_id, struct_key,
    )
    if bounds is None:
        raise HTTPException(status_code=404, detail="ROI not found")
    return ApiResponse(success=True, data=bounds)


@router.get("/plans/{session_id}/{patient_id}")
async def get_rt_plans(session_id: str, patient_id: str):
    plans = await asyncio.to_thread(dicom_service.get_rt_plans, session_id, patient_id)
    return ApiResponse(success=True, data={"plans": plans or []})


@router.get("/suv-info/{session_id}/{patient_id}/{series_uid}")
async def get_suv_info(session_id: str, patient_id: str, series_uid: str):
    """Extract SUV parameters from PET series DICOM headers."""
    info = await asyncio.to_thread(
        dicom_service.get_suv_info, session_id, patient_id, series_uid,
    )
    if info is None:
        raise HTTPException(status_code=404, detail="Series not found or not a PET series")
    return ApiResponse(success=True, data=info)


@router.get("/find-pt-series/{session_id}/{patient_id}")
async def find_pt_series(session_id: str, patient_id: str):
    """Find CT+PT series pairs within the same study for PET-CT fusion."""
    pairs = await asyncio.to_thread(
        dicom_service.find_pt_series, session_id, patient_id,
    )
    return ApiResponse(success=True, data={"pairs": pairs})


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    cleaned = dicom_service.cleanup_session(session_id)
    if not cleaned:
        raise HTTPException(status_code=404, detail="Session not found")
    return ApiResponse(success=True, data={"status": "cleaned", "session_id": session_id})


@router.post("/slice-binary")
async def get_slice_binary(req: SliceRequest):
    """Return slice as binary data with metadata in headers (~60% smaller than JSON)."""
    slice_data = await asyncio.to_thread(
        image_builder.get_slice,
        req.session_id, req.patient_id, req.series_uid,
        req.orientation, req.slice_index,
        req.window_center, req.window_width,
    )
    if slice_data is None:
        raise HTTPException(status_code=404, detail="Slice not found")

    # Convert to binary
    arr = np.array(slice_data["data"], dtype=np.uint8)
    binary_data = arr.tobytes()

    return Response(
        content=binary_data,
        media_type="application/octet-stream",
        headers={
            "X-Slice-Shape": json.dumps(slice_data["shape"]),
            "X-Slice-Orientation": slice_data["orientation"],
            "X-Slice-Index": str(slice_data["slice_index"]),
            "X-Slice-MaxSlice": str(slice_data["max_slice"]),
            "X-Slice-Spacing": json.dumps(slice_data["spacing"]),
            "X-Slice-WindowCenter": str(slice_data.get("window_center", "")),
            "X-Slice-WindowWidth": str(slice_data.get("window_width", "")),
        },
    )


@router.post("/volume-binary")
async def get_volume_binary(req: VolumeRequest):
    """Return raw 3D volume as binary for Cornerstone3D rendering.

    Uses chunked streaming for volumes >100MB to avoid single-response timeouts.
    """
    result = await asyncio.to_thread(
        image_builder.get_volume_binary,
        req.session_id, req.patient_id, req.series_uid,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Volume not found")

    data = result["data"]
    total_size = len(data)
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks

    headers = {
        "X-Volume-Shape": json.dumps(result["shape"]),
        "X-Volume-Spacing": json.dumps(result["spacing"]),
        "X-Volume-Origin": json.dumps(result["origin"]),
        "X-Volume-Dtype": result["dtype"],
        "Content-Length": str(total_size),
    }

    if total_size <= CHUNK_SIZE:
        # Small volume: send as single response
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers=headers,
        )

    # Large volume: stream in chunks
    async def chunk_generator():
        offset = 0
        while offset < total_size:
            end = min(offset + CHUNK_SIZE, total_size)
            yield data[offset:end]
            offset = end

    return StreamingResponse(
        chunk_generator(),
        media_type="application/octet-stream",
        headers=headers,
    )
