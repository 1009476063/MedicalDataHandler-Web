"""DICOM anonymization router with profiles, preview, and audit log."""

import os
from typing import Optional

import pydicom
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services import anonymization_service, dicom_service, log_service

router = APIRouter()


class PreviewRequest(BaseModel):
    session_id: str
    patient_id: str
    file_id: Optional[str] = None
    profile: str = "research"
    custom_rules: Optional[dict[str, str]] = None
    date_offset_days: Optional[int] = None
    seed: str = ""


class AnonymizeRequest(BaseModel):
    session_id: str
    patient_id: str
    profile: str = "research"
    custom_rules: Optional[dict[str, str]] = None
    date_offset_days: Optional[int] = None
    seed: Optional[str] = None


@router.get("/profiles")
async def list_profiles():
    """List available anonymization profiles."""
    return ApiResponse(success=True, data=anonymization_service.get_available_profiles())


@router.get("/profiles/{profile_name}")
async def get_profile(profile_name: str):
    """Get details of a specific anonymization profile."""
    try:
        return ApiResponse(success=True, data=anonymization_service.get_profile(profile_name))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/preview")
async def preview_anonymization(req: PreviewRequest):
    """Preview anonymization changes on a single DICOM file."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    patient = session.get("patients", {}).get(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Auto-pick first file if not specified
    file_id = req.file_id
    if not file_id:
        for fid in session.get("files", {}):
            finfo = session["files"][fid]
            if finfo.get("patient_id") == req.patient_id:
                file_id = fid
                break
    if not file_id:
        raise HTTPException(status_code=404, detail="No files found for patient")

    file_info = session.get("files", {}).get(file_id)
    raw = dicom_service._load_pixel_data(session, file_id)
    if not file_info or not raw:
        raise HTTPException(status_code=404, detail="File not found")

    meta = file_info.get("metadata", {})
    dcm = pydicom.Dataset()
    dcm.PatientName = meta.get("PatientName", "")
    dcm.PatientID = meta.get("PatientID", "")
    dcm.Modality = meta.get("Modality", "OT")
    dcm.SOPClassUID = meta.get("SOPClassUID", "")
    dcm.SOPInstanceUID = file_id
    dcm.StudyInstanceUID = meta.get("StudyInstanceUID", "")
    dcm.SeriesInstanceUID = meta.get("SeriesInstanceUID", "")
    dcm.StudyDate = meta.get("StudyDate", "")
    dcm.StudyTime = meta.get("StudyTime", "")
    dcm.PatientBirthDate = meta.get("PatientBirthDate", "")
    dcm.InstitutionName = meta.get("InstitutionName", "")

    import asyncio
    result = await asyncio.to_thread(
        anonymization_service.preview_anonymization,
        dcm, req.profile, req.custom_rules, req.date_offset_days, req.seed,
    )
    return ApiResponse(success=True, data=result)


@router.post("/apply")
async def apply_anonymization(req: AnonymizeRequest):
    """Apply anonymization to all files for a patient."""
    import asyncio
    result = await asyncio.to_thread(
        anonymization_service.anonymize_patient_files,
        req.session_id, req.patient_id, req.profile,
        req.custom_rules, req.date_offset_days, req.seed,
    )
    return ApiResponse(success=True, data=result)


@router.get("/audit/{session_id}/{patient_id}")
async def get_audit_log(session_id: str, patient_id: str):
    """Retrieve the audit log for a previous anonymization."""
    audit_path = os.path.join(
        str(dicom_service._get_session_dir(session_id)),
        "anonymized", patient_id, "audit_log.json"
    )
    if not os.path.exists(audit_path):
        raise HTTPException(status_code=404, detail="No audit log found")

    import json
    with open(audit_path) as f:
        return ApiResponse(success=True, data=json.load(f))


@router.get("/download/{session_id}/{patient_id}/{filename}")
async def download_anonymized(session_id: str, patient_id: str, filename: str):
    """Download an anonymized DICOM file."""
    import re as _re
    if not _re.fullmatch(r'[0-9a-f]{8}', session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")

    file_path = os.path.join(
        str(dicom_service._get_session_dir(session_id)),
        "anonymized", patient_id, filename
    )
    resolved = os.path.realpath(file_path)
    uploads_root = os.path.realpath("uploads")
    if not resolved.startswith(uploads_root):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        resolved,
        media_type="application/dicom",
        filename=filename,
    )
