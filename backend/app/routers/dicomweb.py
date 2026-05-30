"""DICOMweb router for PACS connectivity."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import ipaddress
import socket
import tempfile
import os

from app.models.response import ApiResponse
from app.services.dicomweb_service import DicomwebService

router = APIRouter()

# Active connections keyed by name
_connections: dict[str, DicomwebService] = {}


def _is_private_url(url: str) -> bool:
    """Check if URL resolves to a private/reserved IP address (SSRF protection)."""
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    if not host:
        return True
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except (ValueError, socket.gaierror):
        return True


class ConnectRequest(BaseModel):
    name: str
    base_url: str
    auth_token: Optional[str] = None


class ConnectResponse(BaseModel):
    name: str
    base_url: str
    status: str


class SearchParams(BaseModel):
    connection: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    study_date: Optional[str] = None
    modality: Optional[str] = None


@router.post("/connect", response_model=ConnectResponse)
async def connect_pacs(req: ConnectRequest):
    from urllib.parse import urlparse
    parsed = urlparse(req.base_url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL scheme")
    if _is_private_url(req.base_url):
        raise HTTPException(status_code=400, detail="Connections to private/reserved IP addresses are not allowed")
    svc = DicomwebService(req.base_url, req.auth_token)
    try:
        await svc.search_studies({"limit": 1})
    except Exception:
        await svc.close()
        raise HTTPException(status_code=502, detail="PACS connection failed")
    _connections[req.name] = svc
    return ConnectResponse(name=req.name, base_url=req.base_url, status="connected")


@router.get("/connections")
async def list_connections():
    return ApiResponse(success=True, data=[{"name": k, "base_url": v.base_url} for k, v in _connections.items()])


@router.delete("/connections/{name}")
async def disconnect_pacs(name: str):
    svc = _connections.pop(name, None)
    if not svc:
        raise HTTPException(status_code=404, detail="Connection not found")
    await svc.close()
    return ApiResponse(success=True, data={"status": "disconnected"})


@router.get("/studies")
async def search_studies(connection: str, patient_name: Optional[str] = None, patient_id: Optional[str] = None, study_date: Optional[str] = None, modality: Optional[str] = None):
    svc = _connections.get(connection)
    if not svc:
        raise HTTPException(status_code=404, detail="Connection not found")
    params = {}
    if patient_name:
        params["PatientName"] = patient_name
    if patient_id:
        params["PatientID"] = patient_id
    if study_date:
        params["StudyDate"] = study_date
    if modality:
        params["Modality"] = modality
    return ApiResponse(success=True, data=await svc.search_studies(params))


@router.get("/studies/{study_uid}/series")
async def search_series(connection: str, study_uid: str):
    svc = _connections.get(connection)
    if not svc:
        raise HTTPException(status_code=404, detail="Connection not found")
    return ApiResponse(success=True, data=await svc.search_series(study_uid))


@router.get("/studies/{study_uid}/series/{series_uid}/instances")
async def search_instances(connection: str, study_uid: str, series_uid: str):
    svc = _connections.get(connection)
    if not svc:
        raise HTTPException(status_code=404, detail="Connection not found")
    return ApiResponse(success=True, data=await svc.search_instances(study_uid, series_uid))


@router.get("/studies/{study_uid}/retrieve")
async def retrieve_study(connection: str, study_uid: str):
    svc = _connections.get(connection)
    if not svc:
        raise HTTPException(status_code=404, detail="Connection not found")
    data = await svc.retrieve_study(study_uid)
    return ApiResponse(success=True, data={"size": len(data), "status": "retrieved"})


@router.get("/studies/{study_uid}/series/{series_uid}/retrieve")
async def retrieve_series(connection: str, study_uid: str, series_uid: str):
    svc = _connections.get(connection)
    if not svc:
        raise HTTPException(status_code=404, detail="Connection not found")
    data = await svc.retrieve_series(study_uid, series_uid)
    return ApiResponse(success=True, data={"size": len(data), "status": "retrieved"})
