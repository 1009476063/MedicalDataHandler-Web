"""DICOM Structured Reporting (SR) router — parse, create, manage SR documents."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services.sr_service import sr_service, _sr_to_dict

router = APIRouter()


class SrCreateRequest(BaseModel):
    session_id: str
    patient_id: str
    patient_name: str = ""
    study_date: str = ""
    findings: list[dict[str, str]]
    template: str = "126000"
    institution: str = ""


@router.get("/documents")
async def list_documents(session_id: str, patient_id: str = ""):
    docs = sr_service.list_documents(session_id, patient_id)
    return ApiResponse(success=True, data=[_sr_to_dict(d) for d in docs])


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = sr_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="SR document not found")
    return ApiResponse(success=True, data=_sr_to_dict(doc))


@router.get("/documents/{doc_id}/tree")
async def get_content_tree(doc_id: str):
    tree = sr_service.get_content_tree(doc_id)
    if not tree and not sr_service.get_document(doc_id):
        raise HTTPException(status_code=404, detail="SR document not found")
    from app.services.sr_service import _node_to_dict
    return ApiResponse(success=True, data=[_node_to_dict(n) for n in tree])


@router.post("/create")
async def create_from_findings(req: SrCreateRequest):
    doc = sr_service.create_from_findings(
        session_id=req.session_id,
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        study_date=req.study_date,
        findings=req.findings,
        template=req.template,
        institution=req.institution,
    )
    return ApiResponse(success=True, data=_sr_to_dict(doc))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    if not sr_service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="SR document not found")
    return ApiResponse(success=True, data=None)
