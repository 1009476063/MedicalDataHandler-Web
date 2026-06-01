"""DICOM Modality Worklist (MWL) router — local CRUD + remote DICOMweb query."""

import csv
import io
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services.mwl_service import mwl_service, MwlItem

router = APIRouter()


class MwlItemRequest(BaseModel):
    session_id: str
    patient_name: str = ""
    patient_id: str = ""
    accession_number: str = ""
    study_date: str = ""
    modality: str = ""
    referring_physician: str = ""
    scheduled_step_status: str = ""
    study_instance_uid: str = ""
    scheduled_station_ae_title: str = ""
    requested_procedure_description: str = ""
    institution_name: str = ""
    station_name: str = ""


class MwlUpdateRequest(BaseModel):
    session_id: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    accession_number: Optional[str] = None
    study_date: Optional[str] = None
    modality: Optional[str] = None
    referring_physician: Optional[str] = None
    scheduled_step_status: Optional[str] = None
    study_instance_uid: Optional[str] = None
    scheduled_station_ae_title: Optional[str] = None
    requested_procedure_description: Optional[str] = None
    institution_name: Optional[str] = None
    station_name: Optional[str] = None


class RemoteQueryRequest(BaseModel):
    base_url: str
    auth_token: Optional[str] = None
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    accession_number: Optional[str] = None
    study_date: Optional[str] = None


def _item_dict(item: MwlItem) -> dict:
    return {
        "id": item.id,
        "patient_name": item.patient_name,
        "patient_id": item.patient_id,
        "accession_number": item.accession_number,
        "study_date": item.study_date,
        "modality": item.modality,
        "referring_physician": item.referring_physician,
        "scheduled_step_status": item.scheduled_step_status,
        "study_instance_uid": item.study_instance_uid,
        "scheduled_station_ae_title": item.scheduled_station_ae_title,
        "requested_procedure_description": item.requested_procedure_description,
        "institution_name": item.institution_name,
        "station_name": item.station_name,
    }


@router.get("/search")
async def search_worklist(session_id: str, q: str = ""):
    items = mwl_service.search_local(session_id, q)
    return ApiResponse(success=True, data=[_item_dict(i) for i in items])


@router.post("/import")
async def import_csv(session_id: str, file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    items = mwl_service.import_csv(session_id, text)
    return ApiResponse(success=True, data={"count": len(items)})


@router.get("/export")
async def export_csv(session_id: str):
    csv_data = mwl_service.export_csv(session_id)
    return ApiResponse(success=True, data={"csv": csv_data})


@router.post("/items")
async def add_item(req: MwlItemRequest):
    item = MwlItem(
        patient_name=req.patient_name,
        patient_id=req.patient_id,
        accession_number=req.accession_number,
        study_date=req.study_date,
        modality=req.modality,
        referring_physician=req.referring_physician,
        scheduled_step_status=req.scheduled_step_status,
        study_instance_uid=req.study_instance_uid,
        scheduled_station_ae_title=req.scheduled_station_ae_title,
        requested_procedure_description=req.requested_procedure_description,
        institution_name=req.institution_name,
        station_name=req.station_name,
    )
    result = mwl_service.add_item(req.session_id, item)
    return ApiResponse(success=True, data=_item_dict(result))


@router.put("/items/{item_id}")
async def update_item(item_id: str, req: MwlUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if k != "session_id" and v is not None}
    try:
        result = mwl_service.update_item(req.session_id, item_id, updates)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")
    return ApiResponse(success=True, data=_item_dict(result))


@router.delete("/items/{item_id}")
async def delete_item(session_id: str, item_id: str):
    deleted = mwl_service.delete_item(session_id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return ApiResponse(success=True, data={"deleted": True})


@router.post("/remote-query")
async def remote_query(req: RemoteQueryRequest):
    """Query a remote DICOMweb MWL endpoint via QIDO-RS."""
    from app.routers.dicomweb import _is_private_url

    if _is_private_url(req.base_url):
        raise HTTPException(status_code=400, detail="Private/reserved URLs are not allowed")

    params: dict[str, str] = {}
    if req.patient_name:
        params["0010,0010"] = req.patient_name
    if req.patient_id:
        params["0010,0020"] = req.patient_id
    if req.accession_number:
        params["0008,0050"] = req.accession_number
    if req.study_date:
        params["0008,0020"] = req.study_date

    headers = {"Accept": "application/dicom+json"}
    if req.auth_token:
        headers["Authorization"] = f"Bearer {req.auth_token}"

    url = req.base_url.rstrip("/") + "/worklist"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Remote error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection failed: {e}")

    items = []
    for entry in data:
        def _get(tag: str) -> str:
            v = entry.get(tag, {})
            if isinstance(v, dict):
                return v.get("Value", [""])[0] if v.get("Value") else ""
            return ""

        item = MwlItem(
            patient_name=_get("0010,0010"),
            patient_id=_get("0010,0020"),
            accession_number=_get("0008,0050"),
            study_date=_get("0008,0020"),
            modality=_get("0008,0060"),
            referring_physician=_get("0008,0090"),
            study_instance_uid=_get("0020,000D"),
            institution_name=_get("0008,0080"),
        )
        items.append(item)

    return ApiResponse(success=True, data=[_item_dict(i) for i in items])
