"""DICOM Print router — manage printers and send print jobs."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services.print_service import print_service, _printer_to_dict, _job_to_dict

router = APIRouter()


class PrinterRequest(BaseModel):
    name: str = "Untitled Printer"
    ae_title: str = "MEDVISTA"
    host: str = "localhost"
    port: int = 104
    film_size: str = "8X10"
    orientation: str = "PORTRAIT"
    density: int = 15


class PrinterUpdateRequest(BaseModel):
    name: str | None = None
    ae_title: str | None = None
    host: str | None = None
    port: int | None = None
    film_size: str | None = None
    orientation: str | None = None
    density: int | None = None


class PrintJobRequest(BaseModel):
    printer_id: str
    image_data: str
    film_size: str = "8X10"
    orientation: str = "PORTRAIT"


@router.get("/printers")
async def list_printers():
    printers = print_service.list_printers()
    return ApiResponse(success=True, data=[_printer_to_dict(p) for p in printers])


@router.post("/printers")
async def add_printer(req: PrinterRequest):
    printer = print_service.add_printer(req.model_dump())
    return ApiResponse(success=True, data=_printer_to_dict(printer))


@router.put("/printers/{printer_id}")
async def update_printer(printer_id: str, req: PrinterUpdateRequest):
    updates = req.model_dump(exclude_none=True)
    printer = print_service.update_printer(printer_id, updates)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return ApiResponse(success=True, data=_printer_to_dict(printer))


@router.delete("/printers/{printer_id}")
async def delete_printer(printer_id: str):
    if not print_service.delete_printer(printer_id):
        raise HTTPException(status_code=404, detail="Printer not found")
    return ApiResponse(success=True, data=None)


@router.post("/send")
async def send_print(req: PrintJobRequest):
    try:
        job = print_service.send_print(
            printer_id=req.printer_id,
            image_data=req.image_data,
            options={"film_size": req.film_size, "orientation": req.orientation},
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid print request")
    return ApiResponse(success=True, data=_job_to_dict(job))


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = print_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")
    return ApiResponse(success=True, data=_job_to_dict(job))
