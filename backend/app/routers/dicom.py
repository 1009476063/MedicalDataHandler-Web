from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import pydicom
import numpy as np
import io
import json
import asyncio
from pathlib import Path

from app.services.dicom_service import dicom_service
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
    slice_index: int
    window_center: Optional[float] = None
    window_width: Optional[float] = None


@router.post("/upload", response_model=UploadResponse)
async def upload_dicom(files: list[UploadFile] = File(...)):
    result = await dicom_service.process_upload(files)
    if result.get("error"):
        raise HTTPException(status_code=413, detail=result["error"])
    return result


@router.get("/patients/{session_id}")
async def get_patients(session_id: str):
    patients = dicom_service.get_patients(session_id)
    if not patients:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"patients": patients}


@router.get("/patient/{session_id}/{patient_id}")
async def get_patient_detail(session_id: str, patient_id: str):
    detail = dicom_service.get_patient_detail(session_id, patient_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Patient not found")
    return detail


@router.get("/metadata/{session_id}/{file_id}")
async def get_dicom_metadata(session_id: str, file_id: str):
    metadata = dicom_service.get_file_metadata(session_id, file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return metadata


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
    return slice_data


@router.get("/series-info/{session_id}/{patient_id}/{series_uid}")
async def get_series_info(session_id: str, patient_id: str, series_uid: str):
    info = image_builder.get_series_info(session_id, patient_id, series_uid)
    if not info:
        raise HTTPException(status_code=404, detail="Series not found")
    return info


@router.get("/structs/{session_id}/{patient_id}")
async def get_rt_structs(session_id: str, patient_id: str):
    structs = await asyncio.to_thread(struct_builder.get_structs, session_id, patient_id)
    return {"structures": structs or []}


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
    return mask


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
    return dose


@router.get("/dose-info/{session_id}/{patient_id}")
async def get_dose_info(session_id: str, patient_id: str):
    info = dose_builder.get_dose_info(session_id, patient_id)
    return {"doses": info or []}


@router.get("/roi-bounds/{session_id}/{patient_id}/{struct_key}")
async def get_roi_bounds(session_id: str, patient_id: str, struct_key: str):
    bounds = await asyncio.to_thread(
        struct_builder.get_roi_bounds, session_id, patient_id, struct_key,
    )
    if bounds is None:
        raise HTTPException(status_code=404, detail="ROI not found")
    return bounds


@router.get("/plans/{session_id}/{patient_id}")
async def get_rt_plans(session_id: str, patient_id: str):
    plans = dicom_service.get_rt_plans(session_id, patient_id)
    return {"plans": plans or []}
