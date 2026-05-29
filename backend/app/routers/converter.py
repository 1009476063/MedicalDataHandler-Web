"""Router for DICOM to NIfTI conversion and DICOM anonymization.

Provides both synchronous and streaming (SSE) conversion endpoints.
The streaming endpoint pushes real-time progress updates to the frontend.
"""

import asyncio
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.services import dicom_converter_service as converter
from app.services.dicom_service import dicom_service, MAX_CONCURRENT_UPLOADS, MAX_CONCURRENT_CONVERSIONS
from app.services.log_service import log_service

router = APIRouter()


class ScanRequest(BaseModel):
    session_id: str
    patient_id: str


class ConvertRequest(BaseModel):
    session_id: str
    patient_id: str
    modality: str = "auto"
    selected_series: list[str] | None = None


class AnonymizeRequest(BaseModel):
    session_id: str
    patient_id: str


@router.post("/scan")
async def scan_series(req: ScanRequest):
    """Scan all DICOM series for a patient and return series info."""
    result = converter.scan_patient_series(req.session_id, req.patient_id)
    return result


@router.post("/convert")
async def convert_to_nifti(req: ConvertRequest):
    """Convert DICOM series to NIfTI format (synchronous).

    Triggers conversion in a background thread and returns the results
    when complete. For large batches, consider using /convert-stream
    for real-time progress updates.
    """
    result = await asyncio.to_thread(
        converter.convert_session_to_nifti,
        req.session_id,
        req.patient_id,
        req.modality,
        req.selected_series,
    )
    return result


@router.post("/convert-stream")
async def convert_to_nifti_stream(req: ConvertRequest):
    """Convert DICOM series to NIfTI format with real-time progress via SSE.

    Returns a Server-Sent Events stream. Each event is a JSON object:
      {"type": "progress", "current": 1, "total": 5, "description": "...", "status": "done"}
      {"type": "complete", "files": [...], "errors": [...]}
    """
    if dicom_service.conversion_semaphore.locked():
        raise HTTPException(status_code=429, detail="Server busy, conversion queue full. Try again later.")

    import queue
    import threading

    progress_queue: queue.Queue = queue.Queue()
    done_event = threading.Event()

    def progress_callback(msg: dict):
        progress_queue.put(msg)
        if msg.get("type") == "complete":
            done_event.set()

    async def run_conversion():
        async with dicom_service.conversion_semaphore:
            await asyncio.to_thread(
                converter.convert_session_to_nifti,
                req.session_id,
                req.patient_id,
                req.modality,
                req.selected_series,
                progress_callback,
            )

    # Start conversion in background
    conversion_task = asyncio.create_task(run_conversion())

    async def event_generator():
        while not done_event.is_set() or not progress_queue.empty():
            try:
                msg = progress_queue.get(timeout=0.5)
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            except queue.Empty:
                # Send keepalive comment to prevent connection timeout
                yield ": keepalive\n\n"
        # Drain remaining messages
        while not progress_queue.empty():
            msg = progress_queue.get()
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
        await conversion_task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/anonymize")
async def anonymize_dicoms(req: AnonymizeRequest):
    """Anonymize DICOM files for a patient (strip PHI)."""
    import asyncio
    result = await asyncio.to_thread(
        converter.anonymize_session,
        req.session_id,
        req.patient_id,
    )
    return result


@router.get("/download/{session_id}/{filename}")
async def download_nifti(session_id: str, filename: str):
    """Download a converted NIfTI file."""
    output_dir = Path("uploads") / session_id / "nifti_output"
    for root, _dirs, files in os.walk(output_dir):
        for f in files:
            if f == filename:
                file_path = os.path.join(root, f)
                return FileResponse(
                    file_path,
                    media_type="application/gzip",
                    filename=filename,
                )
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/results/{session_id}/{patient_id}")
async def get_results(session_id: str, patient_id: str):
    """List converted NIfTI files for a patient."""
    output_dir = Path("uploads") / session_id / "nifti_output" / patient_id
    if not output_dir.exists():
        return {"files": []}

    files = []
    for f in sorted(output_dir.iterdir()):
        if f.suffix == ".gz" or f.suffix == ".nii":
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
            })
    return {"files": files}


@router.get("/queue-status")
async def queue_status():
    """Return available concurrency slots for uploads and conversions."""
    return {
        "uploads_available": MAX_CONCURRENT_UPLOADS - dicom_service.upload_semaphore._value,
        "conversions_available": MAX_CONCURRENT_CONVERSIONS - dicom_service.conversion_semaphore._value,
        "max_uploads": MAX_CONCURRENT_UPLOADS,
        "max_conversions": MAX_CONCURRENT_CONVERSIONS,
    }
