"""DICOM anonymization router with profiles, preview, and audit log."""

import os
from typing import Optional

import pydicom
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.utils.rate_limit import limiter
from app.services import anonymization_service, dicom_service, log_service
from app.services.dicom_converter_service import _get_session_dir, _load_pixel_data
from app.services.dicom_service import _PATH_SAFE_RE

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


class ValidateRequest(BaseModel):
    session_id: str
    patient_id: str
    file_id: Optional[str] = None
    profile: str = "research"


class BurnedInRequest(BaseModel):
    session_id: str
    patient_id: str
    file_id: Optional[str] = None


class AIBurnedInRequest(BaseModel):
    session_id: str
    patient_id: str
    file_id: Optional[str] = None
    model_id: str = "gpt-4o-mini"


class AIComplianceRequest(BaseModel):
    session_id: str
    patient_id: str
    profile: str = "research"
    model_id: str = "gpt-4o-mini"


@router.get("/profiles")
async def list_profiles():
    """List available anonymization profiles."""
    return ApiResponse(success=True, data=anonymization_service.get_available_profiles())


@router.get("/profiles/{profile_name}")
async def get_profile(profile_name: str):
    """Get details of a specific anonymization profile."""
    try:
        return ApiResponse(success=True, data=anonymization_service.get_profile(profile_name))
    except ValueError:
        raise HTTPException(status_code=404, detail="Profile not found")


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
    raw = _load_pixel_data(session, file_id)
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
@limiter.limit("10/minute")
async def apply_anonymization(request: Request, req: AnonymizeRequest):
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
    import re as _re
    if not _re.fullmatch(r'[0-9a-f]{32}', session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    if not _PATH_SAFE_RE.match(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient ID")

    audit_path = os.path.join(
        str(_get_session_dir(session_id)),
        "anonymized", patient_id, "audit_log.json"
    )
    if not os.path.exists(audit_path):
        raise HTTPException(status_code=404, detail="No audit log found")

    import json
    with open(audit_path) as f:
        return ApiResponse(success=True, data=json.load(f))


@router.post("/validate")
async def validate_compliance(req: ValidateRequest):
    """Validate a DICOM file against a compliance profile."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    patient = session.get("patients", {}).get(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

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
    if not file_info:
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
    dcm.AccessionNumber = meta.get("AccessionNumber", "")
    dcm.StationName = meta.get("StationName", "")
    dcm.ReferringPhysicianName = meta.get("ReferringPhysicianName", "")
    dcm.PerformingPhysicianName = meta.get("PerformingPhysicianName", "")
    dcm.OperatorsName = meta.get("OperatorsName", "")

    import asyncio
    result = await asyncio.to_thread(
        anonymization_service.validate_compliance, dcm, req.profile,
    )
    return ApiResponse(success=True, data=result)


@router.post("/detect-burned-in")
@limiter.limit("10/minute")
async def detect_burned_in(request: Request, req: BurnedInRequest):
    """Detect burned-in annotations in a DICOM file."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    patient = session.get("patients", {}).get(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

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
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    meta = file_info.get("metadata", {})
    dcm = pydicom.Dataset()
    dcm.PatientName = meta.get("PatientName", "")
    dcm.Modality = meta.get("Modality", "OT")
    dcm.SOPClassUID = meta.get("SOPClassUID", "")
    dcm.SOPInstanceUID = file_id
    dcm.PatientID = meta.get("PatientID", "")
    dcm.StudyInstanceUID = meta.get("StudyInstanceUID", "")
    dcm.SeriesInstanceUID = meta.get("SeriesInstanceUID", "")

    import asyncio
    result = await asyncio.to_thread(
        anonymization_service.detect_burned_in_annotations, dcm,
    )
    return ApiResponse(success=True, data=result)


@router.post("/detect-burned-in-ai")
@limiter.limit("5/minute")
async def detect_burned_in_ai(request: Request, req: AIBurnedInRequest):
    """Use vision AI to detect burned-in annotations in a DICOM file."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    patient = session.get("patients", {}).get(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

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
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    raw = _load_pixel_data(session, file_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Cannot load pixel data")

    result = await anonymization_service.detect_burned_in_annotations_ai(
        raw, req.model_id,
    )
    return ApiResponse(success=True, data=result)


@router.post("/validate-ai")
async def validate_compliance_ai(req: AIComplianceRequest):
    """Use AI to review DICOM tag values for compliance risks."""
    session = dicom_service.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    patient = session.get("patients", {}).get(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    file_id = None
    for fid in session.get("files", {}):
        finfo = session["files"][fid]
        if finfo.get("patient_id") == req.patient_id:
            file_id = fid
            break
    if not file_id:
        raise HTTPException(status_code=404, detail="No files found for patient")

    file_info = session.get("files", {}).get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    meta = file_info.get("metadata", {})
    tag_values = {}
    for key in ["PatientName", "PatientID", "PatientBirthDate", "StudyDate",
                "StudyTime", "InstitutionName", "AccessionNumber", "StationName",
                "ReferringPhysicianName", "PerformingPhysicianName", "OperatorsName",
                "Modality", "StudyDescription", "SeriesDescription"]:
        val = meta.get(key, "")
        if val:
            tag_values[key] = str(val)

    result = await anonymization_service.validate_compliance_ai(
        tag_values, req.profile,
    )
    return ApiResponse(success=True, data=result)


@router.get("/download/{session_id}/{patient_id}/{filename}")
async def download_anonymized(session_id: str, patient_id: str, filename: str):
    """Download an anonymized DICOM file."""
    import re as _re
    if not _re.fullmatch(r'[0-9a-f]{32}', session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")

    file_path = os.path.join(
        str(_get_session_dir(session_id)),
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
