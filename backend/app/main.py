from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import dicom, export, config, postprocessing, logging, medical_formats

app = FastAPI(title="MedicalDataHandler Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
