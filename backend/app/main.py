import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.rate_limit import limiter

from app.routers import dicom, export, config, postprocessing
from app.routers import logging as logging_router
from app.routers import medical_formats, converter, analysis, annotations, dicomweb, anonymization, seg, four_d, auth, system, ai, mwl, sr, print as print_router
from app.services.dicom_service import dicom_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    loop = asyncio.get_running_loop()
    loop.create_task(dicom_service._periodic_cleanup())
    yield

app = FastAPI(title="MedVista", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: allow specific origins from env, or same-origin only when unset
_cors_origins = os.environ.get("CORS_ORIGINS", "").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "data": None},
    )

app.include_router(dicom.router, prefix="/api/dicom", tags=["DICOM"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(postprocessing.router, prefix="/api/postprocessing", tags=["Post-Processing"])
app.include_router(logging_router.router, prefix="/api/logging", tags=["Logging"])
app.include_router(medical_formats.router, prefix="/api", tags=["Medical Formats"])
app.include_router(converter.router, prefix="/api/converter", tags=["Converter"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(annotations.router, tags=["Annotations"])
app.include_router(dicomweb.router, prefix="/api/dicomweb", tags=["DICOMweb"])
app.include_router(anonymization.router, prefix="/api/anonymization", tags=["Anonymization"])
app.include_router(seg.router, prefix="/api/seg", tags=["Segmentation"])
app.include_router(four_d.router, prefix="/api/4d", tags=["4D"])
app.include_router(auth.router)
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(mwl.router, prefix="/api/mwl", tags=["MWL"])
app.include_router(sr.router, prefix="/api/sr", tags=["Structured Reporting"])
app.include_router(print_router.router, prefix="/api/print", tags=["DICOM Print"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/api/health")
@limiter.limit("60/minute")
async def health(request: Request):
    return {"status": "ok"}
