"""DICOM SEG (Segmentation) router.

Endpoints for listing, previewing, and retrieving segmentation masks
from uploaded DICOM SEG objects.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services import seg_service, dicom_service

router = APIRouter()


class SegmentMaskRequest(BaseModel):
    session_id: str
    file_id: str
    segment_number: int


class SegmentVolumeRequest(BaseModel):
    session_id: str
    patient_id: str
    segment_number: Optional[int] = None


@router.get("/list/{session_id}/{patient_id}")
async def list_segments(session_id: str, patient_id: str):
    """List all SEG objects and their segments for a patient."""
    session = dicom_service.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    import asyncio
    result = await asyncio.to_thread(
        seg_service.list_segments, session_id, patient_id,
    )
    return ApiResponse(success=True, data={"segments": result, "count": len(result)})


@router.get("/check/{session_id}/{patient_id}")
async def check_seg(session_id: str, patient_id: str):
    """Check if a patient has any SEG files."""
    session = dicom_service.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    import asyncio
    has_seg = await asyncio.to_thread(
        seg_service.detect_seg_in_session, session_id, patient_id,
    )
    return ApiResponse(success=True, data={"has_seg": has_seg})


@router.post("/mask")
async def get_mask(req: SegmentMaskRequest):
    """Get binary mask for a specific segment in a SEG file."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    import asyncio
    result = await asyncio.to_thread(
        seg_service.get_segment_mask,
        req.session_id, req.file_id, req.segment_number,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return ApiResponse(success=True, data=result)


@router.post("/volume")
async def get_volume(req: SegmentVolumeRequest):
    """Get 3D volume data for segments of a patient."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    import asyncio
    result = await asyncio.to_thread(
        seg_service.get_segment_volume,
        req.session_id, req.patient_id, req.segment_number,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No segmentation data found")
    return ApiResponse(success=True, data=result)
