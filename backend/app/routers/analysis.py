"""Router for DICOM sequence analysis and smart selection."""

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services.dicom_service import dicom_service
from app.services.sequence_analysis_service import analyze_patient_sequences
from app.services.log_service import log_service

router = APIRouter()


class AnalyzeRequest(BaseModel):
    session_id: str
    patient_id: str
    confidence_threshold: float = 0.5
    dce_min_file_count: int = 10


@router.post("/analyze")
async def analyze_sequences(req: AnalyzeRequest):
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if req.patient_id not in session.get("patients", {}):
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        result = await asyncio.to_thread(
            analyze_patient_sequences, session, req.patient_id,
            confidence_threshold=req.confidence_threshold,
            dce_min_file_count=req.dce_min_file_count,
        )
        log_service.info(
            f"Sequence analysis complete for patient {req.patient_id}: "
            f"{len(result.get('all_series', []))} series analyzed",
            "analysis",
        )
        return ApiResponse(success=True, data=result)
    except Exception as e:
        log_service.error(f"Sequence analysis failed: {e}", "analysis")
        raise HTTPException(status_code=500, detail="Analysis failed")
