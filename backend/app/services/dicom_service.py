import pydicom
import uuid
import asyncio
import numpy as np
import shutil
import time
from pathlib import Path
from typing import Optional
from collections import defaultdict
from fastapi import UploadFile
import json
import re

from app.services.log_service import log_service

SESSION_TTL = 900  # 15 minutes
CLEANUP_INTERVAL = 120  # 2 minutes
MAX_FILES_PER_SESSION = 10000
MAX_SESSION_SIZE_MB = 2000  # 2 GB

MIN_FREE_DISK_MB = 500          # Reject upload if < 500MB free
DISK_SAFETY_MULTIPLIER = 2      # Require 2x upload size free
MAX_CONCURRENT_UPLOADS = 2
MAX_CONCURRENT_CONVERSIONS = 2

UPLOAD_DIR = Path("uploads")

# Validate session_id format (8-char hex from uuid4[:8]) and patient_id (alphanumeric + dots/hyphens)
_SESSION_ID_RE = re.compile(r'^[0-9a-f]{8}$')
_PATH_SAFE_RE = re.compile(r'^[a-zA-Z0-9._-]+$')

DICOM_TAGS = {
    "PatientName": "00100010",
    "PatientID": "00100020",
    "PatientBirthDate": "00100030",
    "PatientSex": "00100040",
    "StudyDescription": "00081030",
    "StudyDate": "00080020",
    "StudyTime": "00080030",
    "StudyInstanceUID": "0020000D",
    "SeriesDescription": "0008103E",
    "Modality": "00080060",
    "SeriesInstanceUID": "0020000E",
    "SeriesNumber": "00200011",
    "InstanceNumber": "00200013",
    "ImagePositionPatient": "00200032",
    "SliceLocation": "00201041",
    "PixelSpacing": "00280030",
    "Rows": "00280010",
    "Columns": "00280011",
    "BitsAllocated": "00280100",
    "BitsStored": "00280101",
    "NumberOfFrames": "00280008",
    "PhotometricInterpretation": "00280004",
    # Sequence analysis tags
    "DiffusionBValue": "00189087",
    "TemporalPositionIdentifier": "00200100",
    "ContrastBolusAgent": "00180010",
    "ImageType": "00080008",
    "ScanningSequence": "00180020",
    "AcquisitionTime": "00080032",
    "ViewPosition": "00185101",
    "ImageLaterality": "00200062",
}


class DicomService:
    def __init__(self):
        self.sessions: dict[str, dict] = {}
        self._session_timestamps: dict[str, float] = {}
        self.upload_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)
        self.conversion_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CONVERSIONS)
        self._upload_slots = MAX_CONCURRENT_UPLOADS
        self._conversion_slots = MAX_CONCURRENT_CONVERSIONS

    async def _periodic_cleanup(self):
        """Background task: clean up expired sessions every CLEANUP_INTERVAL."""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            self._cleanup_expired()

    def _cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, ts in self._session_timestamps.items()
                   if now - ts > SESSION_TTL]
        for sid in expired:
            self.sessions.pop(sid, None)
            self._session_timestamps.pop(sid, None)
            # Remove session files from disk (only valid session IDs)
            if _SESSION_ID_RE.match(sid):
                session_dir = (UPLOAD_DIR / sid).resolve()
                if str(session_dir).startswith(str(UPLOAD_DIR.resolve())) and session_dir.exists():
                    try:
                        shutil.rmtree(session_dir, ignore_errors=True)
                    except Exception:
                        pass
        if expired:
            log_service.info(f"Cleaned up {len(expired)} expired session(s)", "session")

    def _touch_session(self, session_id: str):
        self._session_timestamps[session_id] = time.time()

    def cleanup_session(self, session_id: str) -> bool:
        """Explicitly clean up a session and its disk files. Returns True if cleaned."""
        if session_id not in self.sessions:
            return False
        self.sessions.pop(session_id, None)
        self._session_timestamps.pop(session_id, None)
        if _SESSION_ID_RE.match(session_id):
            session_dir = (UPLOAD_DIR / session_id).resolve()
            if str(session_dir).startswith(str(UPLOAD_DIR.resolve())) and session_dir.exists():
                try:
                    shutil.rmtree(session_dir, ignore_errors=True)
                except Exception:
                    pass
        log_service.info(f"Session {session_id} cleaned up explicitly", "session")
        return True

    async def process_upload(self, files: list[UploadFile]) -> dict:
        file_bytes_list = []
        for f in files:
            content = await f.read()
            file_bytes_list.append((f.filename, content))
        return await asyncio.to_thread(self.process_upload_bytes, file_bytes_list)

    def process_upload_bytes(self, file_bytes_list: list[tuple[str, bytes]]) -> dict:
        self._cleanup_expired()

        if len(file_bytes_list) > MAX_FILES_PER_SESSION:
            return {
                "session_id": "",
                "patients": [],
                "file_count": 0,
                "error": f"Too many files: {len(file_bytes_list)} exceeds limit of {MAX_FILES_PER_SESSION}",
            }

        total_size_mb = sum(len(content) for _, content in file_bytes_list) / (1024 * 1024)
        if total_size_mb > MAX_SESSION_SIZE_MB:
            return {
                "session_id": "",
                "patients": [],
                "file_count": 0,
                "error": f"Upload too large: {total_size_mb:.0f} MB exceeds limit of {MAX_SESSION_SIZE_MB} MB",
            }

        # Check available disk space
        disk = shutil.disk_usage(UPLOAD_DIR)
        free_mb = disk.free / (1024 * 1024)
        if free_mb < MIN_FREE_DISK_MB:
            return {
                "session_id": "",
                "patients": [],
                "file_count": 0,
                "error": f"Insufficient disk space: {free_mb:.0f} MB free, need at least {MIN_FREE_DISK_MB} MB",
            }
        if free_mb < total_size_mb * DISK_SAFETY_MULTIPLIER:
            return {
                "session_id": "",
                "patients": [],
                "file_count": 0,
                "error": f"Insufficient disk space for upload: {free_mb:.0f} MB free, need {total_size_mb * DISK_SAFETY_MULTIPLIER:.0f} MB ({DISK_SAFETY_MULTIPLIER}x upload size)",
            }

        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = {
            "files": {},
            "patients": {},
            "series": {},
            "studies": {},
            "raw_data": {},
            "session_id": session_id,
        }
        # Create pixel data directory for this session
        pixel_dir = UPLOAD_DIR / session_id / "pixels"
        pixel_dir.mkdir(parents=True, exist_ok=True)
        self._touch_session(session_id)

        log_service.info(f"Upload started: {len(file_bytes_list)} files", "upload")

        success_count = 0
        for filename, content in file_bytes_list:
            try:
                ds = pydicom.dcmread(pydicom.filebase.DicomBytesIO(content), force=True)
                self._process_dicom(session_id, ds, filename, content)
                success_count += 1
            except Exception as e:
                log_service.warning(f"Failed to parse {filename}: {e}", "upload")
                continue

        patients = self._build_patient_list(session_id)
        log_service.success(
            f"Upload complete: {success_count}/{len(file_bytes_list)} files, {len(patients)} patient(s)",
            "upload",
        )
        return {
            "session_id": session_id,
            "patients": patients,
            "file_count": len(self.sessions[session_id]["files"]),
        }

    def _process_dicom(self, session_id: str, ds, filename: str, raw_bytes: bytes):
        session = self.sessions[session_id]
        file_id = str(uuid.uuid4())[:8]

        patient_id = str(getattr(ds, "PatientID", "unknown"))
        study_uid = str(getattr(ds, "StudyInstanceUID", "unknown"))
        series_uid = str(getattr(ds, "SeriesInstanceUID", "unknown"))
        modality = str(getattr(ds, "Modality", "OT"))

        metadata = {}
        for tag_name, tag_hex in DICOM_TAGS.items():
            try:
                tag = pydicom.tag.Tag(tag_hex)
                if tag in ds:
                    value = ds[tag].value
                    if hasattr(value, "original_string"):
                        value = str(value.original_string)
                    elif isinstance(value, pydicom.multival.MultiValue):
                        value = [str(v) for v in value]
                    else:
                        value = str(value)
                    metadata[tag_name] = value
            except Exception:
                continue

        all_tags = {}
        for elem in ds:
            try:
                tag_str = str(elem.tag)
                all_tags[tag_str] = {
                    "name": str(elem.keyword) if elem.keyword else tag_str,
                    "value": str(elem.value)[:500],
                    "vr": str(elem.VR) if elem.VR else "",
                }
            except Exception:
                continue

        file_info = {
            "id": file_id,
            "filename": filename,
            "modality": modality,
            "patient_id": patient_id,
            "study_uid": study_uid,
            "series_uid": series_uid,
            "metadata": metadata,
            "all_tags": all_tags,
        }

        session["files"][file_id] = file_info

        if patient_id not in session["patients"]:
            session["patients"][patient_id] = {
                "patient_id": patient_id,
                "name": str(getattr(ds, "PatientName", "Unknown")),
                "birth_date": str(getattr(ds, "PatientBirthDate", "")),
                "sex": str(getattr(ds, "PatientSex", "")),
                "studies": {},
            }

        patient = session["patients"][patient_id]
        if study_uid not in patient["studies"]:
            patient["studies"][study_uid] = {
                "study_uid": study_uid,
                "description": str(getattr(ds, "StudyDescription", "")),
                "date": str(getattr(ds, "StudyDate", "")),
                "series": {},
            }

        study = patient["studies"][study_uid]
        if series_uid not in study["series"]:
            study["series"][series_uid] = {
                "series_uid": series_uid,
                "description": str(getattr(ds, "SeriesDescription", "")),
                "modality": modality,
                "series_number": str(getattr(ds, "SeriesNumber", "")),
                "files": [],
                "file_count": 0,
            }

        series = study["series"][series_uid]
        series["files"].append(file_id)
        series["file_count"] += 1

        if modality in ("CT", "MR", "PT", "NM", "US", "XA"):
            session["raw_data"][file_id] = self._extract_pixel_data(ds, session_id, file_id)

        # Store raw bytes for RT files so builders can re-parse them
        if modality in ("RTSTRUCT", "RTDOSE", "RTPLAN"):
            session["raw_data"][file_id] = {"raw_bytes": raw_bytes}

    def _extract_pixel_data(self, ds, session_id: str, file_id: str) -> Optional[dict]:
        try:
            pixel_array = ds.pixel_array.astype(np.float64)
            if hasattr(ds, "RescaleSlope") and hasattr(ds, "RescaleIntercept"):
                pixel_array = pixel_array * float(ds.RescaleSlope) + float(ds.RescaleIntercept)

            # Save pixel data to disk to avoid holding large arrays in memory
            npy_path = UPLOAD_DIR / session_id / "pixels" / f"{file_id}.npy"
            try:
                np.save(str(npy_path), pixel_array)
            except Exception:
                npy_path = None

            return {
                "data_path": str(npy_path) if npy_path else None,
                "shape": list(pixel_array.shape),
                "position": [float(v) for v in getattr(ds, "ImagePositionPatient", [0, 0, 0])],
                "spacing": [float(v) for v in getattr(ds, "PixelSpacing", [1, 1])],
                "slice_location": float(getattr(ds, "SliceLocation", 0)),
                "instance_number": int(getattr(ds, "InstanceNumber", 0)),
            }
        except Exception as e:
            log_service.warning(
                f"Pixel data extraction failed for {getattr(ds, 'SOPInstanceUID', 'unknown')}: "
                f"{type(e).__name__}: {e}",
                "pixel_data"
            )
            return None

    def _build_patient_list(self, session_id: str) -> list[dict]:
        session = self.sessions[session_id]
        patients = []
        for pid, pdata in session["patients"].items():
            studies = []
            for suid, sdata in pdata["studies"].items():
                series_list = []
                for seruid, serdata in sdata["series"].items():
                    series_list.append({
                        "series_uid": seruid,
                        "description": serdata["description"],
                        "modality": serdata["modality"],
                        "series_number": serdata["series_number"],
                        "file_count": serdata["file_count"],
                    })
                studies.append({
                    "study_uid": suid,
                    "description": sdata["description"],
                    "date": sdata["date"],
                    "series": series_list,
                })
            patients.append({
                "patient_id": pid,
                "name": pdata["name"],
                "birth_date": pdata["birth_date"],
                "sex": pdata["sex"],
                "studies": studies,
            })
        return patients

    def get_patients(self, session_id: str) -> list[dict]:
        if session_id not in self.sessions:
            return []
        self._touch_session(session_id)
        return self._build_patient_list(session_id)

    def get_patient_detail(self, session_id: str, patient_id: str) -> Optional[dict]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        self._touch_session(session_id)
        patient = session["patients"].get(patient_id)
        if not patient:
            return None

        file_list = []
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] == patient_id:
                file_list.append({
                    "id": fid,
                    "filename": finfo["filename"],
                    "modality": finfo["modality"],
                    "series_uid": finfo["series_uid"],
                })

        return {
            "patient": patient,
            "files": file_list,
        }

    def get_file_metadata(self, session_id: str, file_id: str) -> Optional[dict]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        self._touch_session(session_id)
        return session["files"].get(file_id)

    def get_rt_plans(self, session_id: str, patient_id: str) -> list[dict]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        self._touch_session(session_id)
        plans = []
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] == patient_id and finfo["modality"] == "RTPLAN":
                plans.append({
                    "file_id": fid,
                    "filename": finfo["filename"],
                    "metadata": finfo["metadata"],
                })
        return plans

    def get_structs(self, session_id: str, patient_id: str) -> list[dict]:
        """Get RT structure sets for a patient."""
        session = self.sessions.get(session_id)
        if not session:
            return []

        structs = []
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] == patient_id and finfo["modality"] == "RTSTRUCT":
                # Parse ROI names from the raw DICOM data
                raw_info = session["raw_data"].get(fid)
                if raw_info and "raw_bytes" in raw_info:
                    try:
                        ds = pydicom.dcmread(
                            pydicom.filebase.DicomBytesIO(raw_info["raw_bytes"]),
                            force=True
                        )
                        if hasattr(ds, "StructureSetROISequence"):
                            for roi in ds.StructureSetROISequence:
                                structs.append({
                                    "key": str(roi.ROINumber),
                                    "name": str(roi.ROIName),
                                    "file_id": fid,
                                })
                            continue
                    except Exception:
                        pass
                # Fallback: use filename
                structs.append({
                    "key": fid,
                    "name": finfo.get("filename", fid),
                    "file_id": fid,
                })

        return structs

    def rename_struct(self, session_id: str, patient_id: str, struct_key: str, new_name: str) -> Optional[dict]:
        """Rename an RT structure."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        file_info = session["files"].get(struct_key)
        if not file_info or file_info["patient_id"] != patient_id:
            return None

        # Update the filename which serves as the display name
        file_info["filename"] = new_name

        # Update metadata if it has a StructureName field
        if "metadata" in file_info and isinstance(file_info["metadata"], dict):
            if "StructureName" in file_info["metadata"]:
                file_info["metadata"]["StructureName"] = new_name

        return {"key": struct_key, "name": new_name}


# Shared singleton instance so all services access the same sessions dict
dicom_service = DicomService()
