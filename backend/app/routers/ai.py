"""AI analysis router — /api/ai endpoints."""

import asyncio
import json
import time

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services.ai_service import ai_service
from app.utils.rate_limit import limiter

router = APIRouter()


class AnalyzeRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    session_id: str
    patient_id: str
    series_uid: str
    model_id: str = "gpt-4o"
    prompt: str = ""
    slice_strategy: str = "middle"  # middle | multi | mip


class AIConfigRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    api_base: str | None = None
    api_key: str | None = None
    default_model: str | None = None


class SummaryRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    findings: list[dict]
    model_id: str = "gpt-4o-mini"
    patient_context: str = ""


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
@router.get("/config")
@limiter.limit("30/minute")
async def get_ai_config(request: Request):
    """Get current AI configuration (API key is masked)."""
    cfg = ai_service.get_config()
    key = cfg.get("api_key", "")
    cfg["api_key"] = ("*" * (len(key) - 4) + key[-4:]) if len(key) > 4 else ("*" * len(key) if key else "")
    return ApiResponse(success=True, data=cfg)


@router.put("/config")
@limiter.limit("10/minute")
async def update_ai_config(req: AIConfigRequest, request: Request):
    """Update AI configuration (saved to disk)."""
    cfg = ai_service.update_config(req.api_base, req.api_key, req.default_model)
    return ApiResponse(success=True, data=cfg)


# ------------------------------------------------------------------
# Connectivity check
# ------------------------------------------------------------------
@router.post("/check")
@limiter.limit("10/minute")
async def check_ai_connection(req: AIConfigRequest, request: Request):
    """Test connectivity to the AI endpoint. Accepts inline config for pre-save testing."""
    # Use request body values if provided, fall back to saved config
    saved = ai_service.get_config()
    api_base = (req.api_base or saved.get("api_base", "")).rstrip("/")
    api_key = req.api_key or saved.get("api_key", "")

    if not api_base:
        return ApiResponse(success=False, error="API Base URL not configured")

    from app.routers.dicomweb import _is_private_url
    if _is_private_url(api_base):
        return ApiResponse(success=False, error="Private/reserved URLs are not allowed")

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{api_base}/models",
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == 200:
                model_count = len(resp.json().get("data", []))
                return ApiResponse(
                    success=True,
                    data={"status": "ok", "model_count": model_count, "latency_ms": latency_ms},
                )
            # Parse error message from response
            error_msg = f"HTTP {resp.status_code}"
            try:
                body = resp.json()
                # Handle {"error": {"message": "..."}} and {"message": "..."} and {"detail": "..."}
                err_obj = body.get("error") if isinstance(body.get("error"), dict) else None
                msg = (err_obj or {}).get("message") or body.get("message") or body.get("detail")
                if msg and isinstance(msg, str):
                    error_msg = f"HTTP {resp.status_code}: {msg[:120]}"
                else:
                    error_msg = f"HTTP {resp.status_code}: {resp.text[:120]}"
            except Exception:
                error_msg = f"HTTP {resp.status_code}: {resp.text[:120]}"
            return ApiResponse(success=False, error=error_msg)
    except httpx.ConnectError:
        return ApiResponse(success=False, error="Cannot connect to the API endpoint")
    except httpx.TimeoutException:
        return ApiResponse(success=False, error="Connection timed out (10s)")
    except Exception as e:
        return ApiResponse(success=False, error=str(e)[:200])


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
@router.post("/models")
@limiter.limit("30/minute")
async def list_models(req: AIConfigRequest, request: Request):
    """List available AI models. Accepts inline config for pre-save testing."""
    saved = ai_service.get_config()
    api_base = req.api_base or saved.get("api_base", "")
    api_key = req.api_key or saved.get("api_key", "")
    models = await ai_service.list_models_with_config(api_base, api_key)
    return ApiResponse(success=True, data=models)


# ------------------------------------------------------------------
# Summary generation
# ------------------------------------------------------------------
@router.post("/summary")
@limiter.limit("10/minute")
async def generate_summary(req: SummaryRequest, request: Request):
    """Generate a natural language study summary from findings."""
    result = await ai_service.generate_summary(
        req.findings, req.model_id, req.patient_context,
    )
    return ApiResponse(success=True, data=result)


# ------------------------------------------------------------------
# Start analysis job
# ------------------------------------------------------------------
@router.post("/analyze")
@limiter.limit("10/minute")
async def start_analysis(req: AnalyzeRequest, request: Request):
    """Start an AI analysis job. Returns job_id for polling/streaming."""
    job = ai_service.create_job(req.model_id)
    asyncio.create_task(
        ai_service.run_analysis(
            job, req.session_id, req.patient_id, req.series_uid, req.prompt,
            slice_strategy=req.slice_strategy,
        )
    )
    return ApiResponse(success=True, data={"job_id": job.job_id, "status": "pending"})


# ------------------------------------------------------------------
# Job status
# ------------------------------------------------------------------
@router.get("/jobs/{job_id}")
@limiter.limit("60/minute")
async def get_job_status(job_id: str, request: Request):
    """Get current status of an analysis job."""
    job = ai_service.get_job(job_id)
    if not job:
        return ApiResponse(success=False, error="Job not found")
    return ApiResponse(
        success=True,
        data={
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "model_id": job.model_id,
            "error": job.error,
        },
    )


# ------------------------------------------------------------------
# SSE progress stream
# ------------------------------------------------------------------
@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str, request: Request):
    """SSE endpoint for real-time job progress updates."""
    job = ai_service.get_job(job_id)
    if not job:
        return ApiResponse(success=False, error="Job not found")

    async def event_generator():
        if not job.progress_queue:
            return
        while True:
            try:
                msg = await asyncio.wait_for(job.progress_queue.get(), timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("done"):
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield f": keepalive\n\n"
            except Exception:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ------------------------------------------------------------------
# Results
# ------------------------------------------------------------------
@router.get("/results/{job_id}")
@limiter.limit("30/minute")
async def get_results(job_id: str, request: Request):
    """Get analysis results for a completed job."""
    job = ai_service.get_job(job_id)
    if not job:
        return ApiResponse(success=False, error="Job not found")
    if job.status == "pending" or job.status == "running":
        return ApiResponse(success=False, error="Job not completed yet")
    if job.status == "failed":
        return ApiResponse(success=False, error=job.error or "Analysis failed")
    return ApiResponse(
        success=True,
        data={
            "job_id": job.job_id,
            "model_id": job.model_id,
            "result": job.result,
        },
    )
