import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import dicom, export, config, postprocessing, logging, medical_formats, converter, analysis, annotations, dicomweb, anonymization, seg, four_d, auth
from app.services.dicom_service import dicom_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background session cleanup on app startup
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(dicom_service._periodic_cleanup())
    yield

app = FastAPI(title="MedVista", version="1.0.0", lifespan=lifespan)

# CORS: allow specific origins from env, or same-origin only when unset
_cors_origins = os.environ.get("CORS_ORIGINS", "").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dicom.router, prefix="/api/dicom", tags=["DICOM"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(postprocessing.router, prefix="/api/postprocessing", tags=["Post-Processing"])
app.include_router(logging.router, prefix="/api/logging", tags=["Logging"])
app.include_router(medical_formats.router, prefix="/api", tags=["Medical Formats"])
app.include_router(converter.router, prefix="/api/converter", tags=["Converter"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(annotations.router, tags=["Annotations"])
app.include_router(dicomweb.router, prefix="/api/dicomweb", tags=["DICOMweb"])
app.include_router(anonymization.router, prefix="/api/anonymization", tags=["Anonymization"])
app.include_router(seg.router, prefix="/api/seg", tags=["Segmentation"])
app.include_router(four_d.router, prefix="/api/4d", tags=["4D"])
app.include_router(auth.router)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
