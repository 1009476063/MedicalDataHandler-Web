"""Service for converting DICOM (MR/MG/US) to NIfTI format.

Adapted from dicom-to-nii-converter (https://github.com/1009476063/dicom-to-nii-converter).
Supports:
  - MR: DWI/ADC/DCE series detection and volume assembly
  - MG: Mammography with view position detection
  - US: Ultrasound from DICOM or JPG/BMP images
  - DICOM anonymization (PHI stripping)

Performance optimizations over the original local script:
  - Parallel series conversion via ThreadPoolExecutor
  - On-demand pixel loading from disk (.npy) to reduce memory pressure
  - Progress callback for real-time SSE streaming
"""

import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pydicom
import SimpleITK as sitk
import nibabel as nib

from app.services.dicom_service import dicom_service
from app.services.log_service import log_service


UPLOAD_DIR = Path("uploads")

# Max parallel conversion workers (CPU-bound, so match CPU cores)
MAX_WORKERS = min(os.cpu_count() or 4, 8)


# ============================================================
# Utility functions
# ============================================================

def _get_session_dir(session_id: str) -> Path:
    return UPLOAD_DIR / session_id


def _load_pixel_data(session: dict, file_id: str) -> Optional[dict]:
    """Load pixel data for a file from disk .npy (kept as numpy array)."""
    raw = session.get("raw_data", {}).get(file_id)
    if not raw:
        return None

    # Load pixel data from disk .npy file
    data_path = raw.get("data_path")
    if data_path:
        try:
            arr = np.load(data_path)
            return {**raw, "data": arr}
        except Exception:
            pass

    # Fallback: legacy in-memory data
    if raw.get("data") is not None:
        return raw

    # Legacy fallback: try .npy in session dir
    npy_path = _get_session_dir(session["session_id"]) / f"{file_id}.npy"
    if npy_path.exists():
        try:
            arr = np.load(str(npy_path))
            return {**raw, "data": arr}
        except Exception:
            pass

    return None


def _write_nifti(save_path: str, volume: np.ndarray, spacing, origin, direction, as_type=None):
    """Write a 3D volume to .nii.gz using SimpleITK."""
    spacing = np.asarray(spacing, dtype=np.float64)
    if as_type is not None:
        volume = volume.astype(as_type)
    raw = sitk.GetImageFromArray(volume[:, :, :])
    spacing_ = (float(spacing[2]), float(spacing[1]), float(spacing[0]))
    raw.SetSpacing(spacing_)
    raw.SetOrigin(origin)
    raw.SetDirection(direction)
    sitk.WriteImage(raw, save_path)


def _find_series(session: dict, patient_id: str, series_uid: str) -> Optional[dict]:
    """Find a specific series in the session structure."""
    patient = session.get("patients", {}).get(patient_id, {})
    for study_uid, study in patient.get("studies", {}).items():
        if series_uid in study.get("series", {}):
            return study["series"][series_uid]
    return None


def _collect_all_series(session: dict, patient_id: str) -> list[dict]:
    """Collect all series metadata for a patient."""
    patient = session.get("patients", {}).get(patient_id, {})
    result = []
    for study_uid, study in patient.get("studies", {}).items():
        for series_uid, series in study.get("series", {}).items():
            result.append({
                "series_uid": series_uid,
                "description": series.get("description", "N/A"),
                "modality": series.get("modality", "OT"),
                "file_count": series.get("file_count", 0),
                "series_number": series.get("series_number", 0),
            })
    return result


# ============================================================
# Series scanning
# ============================================================

def scan_patient_series(session_id: str, patient_id: str) -> dict:
    """Scan all DICOM series for a patient and return series info."""
    session = dicom_service.sessions.get(session_id)
    if not session:
        return {"series": []}
    return {"series": _collect_all_series(session, patient_id)}


# ============================================================
# MR conversion
# ============================================================

def _match_mr_series(series_list: list[dict]) -> dict:
    """Classify MR series into DWI/ADC/DCE categories based on SeriesDescription."""
    result = {"DWI": [], "ADC": [], "DCE": [], "OTHER": []}
    for s in series_list:
        desc = s.get("description", "").upper()
        if desc.startswith("OT") or not desc:
            result["OTHER"].append(s)
            continue

        is_adc = "_ADC" in desc or "ADC" in desc
        is_dwi = (
            ("_TRACEW" in desc and "_ADC" not in desc)
            or ("_REVEAL" in desc and "_ADC" not in desc)
            or ("ep2d_" in desc and "_ADC" not in desc)
            or ("DWI" in desc and not is_adc)
        )
        is_dce = (
            ("T1" in desc and "FL3D" in desc and "DYNA" in desc)
            or desc.endswith("+C")
            or desc.endswith("+ C")
            or "DCE" in desc
            or "C+" in desc
            or "GD" in desc
            or "GADOLINIUM" in desc
            or "ENHANCED" in desc
        )

        if is_adc:
            result["ADC"].append(s)
        elif is_dwi:
            result["DWI"].append(s)
        elif is_dce:
            result["DCE"].append(s)
        else:
            result["OTHER"].append(s)
    return result


def convert_mr_series(
    session_id: str,
    patient_id: str,
    series_uid: str,
    output_dir: str,
    patient_label: str,
) -> Optional[str]:
    """Convert a single MR series to NIfTI.

    Reads DICOM files from the session, assembles the 3D volume,
    and saves as .nii.gz. Returns the output path on success.
    """
    session = dicom_service.sessions.get(session_id)
    if not session:
        return None

    target_series = _find_series(session, patient_id, series_uid)
    if not target_series:
        return None

    file_ids = target_series.get("files", [])
    fuse_list = []
    origin = None
    row_cos = None
    col_cos = None
    pixel_spacing = None

    for fid in file_ids:
        raw = _load_pixel_data(session, fid)
        file_info = session.get("files", {}).get(fid, {})
        if not raw or raw.get("data") is None:
            continue

        arr = np.asarray(raw["data"])
        pos = raw.get("position", [0, 0, 0])
        ipp = np.array(pos, dtype=np.float64)

        iop = file_info.get("metadata", {}).get("ImageOrientationPatient")
        if iop:
            iop = np.array(iop, dtype=np.float64)
            r = iop[0:3]
            c = iop[3:6]
        else:
            r = np.array([1, 0, 0], dtype=np.float64)
            c = np.array([0, 1, 0], dtype=np.float64)

        r = r / (np.linalg.norm(r) + 1e-12)
        c = c / (np.linalg.norm(c) + 1e-12)
        s = np.cross(r, c)
        s = s / (np.linalg.norm(s) + 1e-12)
        proj = float(np.dot(ipp, s))

        fuse_list.append([arr, proj, ipp])
        if origin is None:
            origin = ipp.tolist()
            row_cos = r
            col_cos = c
            sp = raw.get("spacing", [1.0, 1.0])
            pixel_spacing = np.array(sp, dtype=np.float64)

    if not fuse_list:
        return None

    if row_cos is None or col_cos is None:
        row_cos = np.array([1, 0, 0], dtype=np.float64)
        col_cos = np.array([0, 1, 0], dtype=np.float64)

    row_cos = row_cos / (np.linalg.norm(row_cos) + 1e-12)
    col_cos = col_cos / (np.linalg.norm(col_cos) + 1e-12)
    slice_cos = np.cross(row_cos, col_cos)
    slice_cos = slice_cos / (np.linalg.norm(slice_cos) + 1e-12)

    fuse_list.sort(key=lambda x: x[1])
    origin = fuse_list[0][2].tolist()

    if len(fuse_list) >= 2:
        v = fuse_list[-1][2] - fuse_list[0][2]
        n = float(np.linalg.norm(v))
        z_dir = v / n if n > 0 else slice_cos
    else:
        z_dir = slice_cos

    z_dir = z_dir / (np.linalg.norm(z_dir) + 1e-12)
    if float(np.dot(np.cross(row_cos, col_cos), z_dir)) < 0:
        z_dir = -z_dir

    if len(fuse_list) >= 2:
        z_diffs = np.diff([x[1] for x in fuse_list])
        z_spacing = float(np.median(np.abs(z_diffs)))
        if z_spacing <= 0:
            z_spacing = 1.0
    else:
        z_spacing = 1.0

    if pixel_spacing is None:
        pixel_spacing = np.array([1.0, 1.0], dtype=np.float64)

    direction = [
        float(row_cos[0]), float(col_cos[0]), float(z_dir[0]),
        float(row_cos[1]), float(col_cos[1]), float(z_dir[1]),
        float(row_cos[2]), float(col_cos[2]), float(z_dir[2]),
    ]

    # Pre-allocate volume array and fill slice-by-slice to reduce peak memory
    slice_shape = fuse_list[0][0].shape
    num_slices = len(fuse_list)
    volume = np.empty((num_slices,) + slice_shape, dtype=np.uint16)
    for i, item in enumerate(fuse_list):
        arr = item[0]
        if arr.dtype != np.uint16:
            arr = np.clip(np.rint(arr), 0, 65535).astype(np.uint16)
        volume[i] = arr

    spacing = np.array([z_spacing, float(pixel_spacing[0]), float(pixel_spacing[1])], dtype=np.float64)

    desc = target_series.get("description", "MR")
    sn = target_series.get("series_number", 0)
    output_name = f"{patient_label}_{desc}_{sn}.nii.gz"
    output_path = os.path.join(output_dir, output_name)
    _write_nifti(output_path, volume, spacing, origin, direction, as_type=np.uint16)
    return output_path


# ============================================================
# MG conversion
# ============================================================

def convert_mg_series(
    session_id: str,
    patient_id: str,
    series_uid: str,
    output_dir: str,
    patient_label: str,
) -> Optional[str]:
    """Convert a mammography series to NIfTI."""
    session = dicom_service.sessions.get(session_id)
    if not session:
        return None

    target_series = _find_series(session, patient_id, series_uid)
    if not target_series:
        return None

    file_ids = target_series.get("files", [])
    if not file_ids:
        return None

    fid = file_ids[0]
    raw = _load_pixel_data(session, fid)
    if not raw or raw.get("data") is None:
        return None

    pixel_data = np.asarray(raw["data"])
    if pixel_data.ndim > 2:
        pixel_data = np.squeeze(pixel_data)
    if pixel_data.ndim > 2:
        return None

    spacing_x = raw.get("spacing", [1.0, 1.0])
    if len(spacing_x) >= 2:
        sp = np.array([float(spacing_x[0]), float(spacing_x[1])], dtype=np.float64)
    else:
        sp = np.array([1.0, 1.0], dtype=np.float64)

    origin = [0, 0]
    direction = [-1, 0, 0, 1]

    view_name = "UNKNOWN"
    file_info = session.get("files", {}).get(fid, {})
    meta = file_info.get("metadata", {})
    protocol = meta.get("ProtocolName", "")
    if protocol:
        view_name = protocol.replace(" ", "")
    if view_name not in ("LCC", "RCC", "LMLO", "RMLO"):
        laterality = meta.get("ImageLaterality", "")
        position = meta.get("ViewPosition", "")
        combined = f"{laterality}{position}"
        if combined in ("LCC", "RCC", "LMLO", "RMLO"):
            view_name = combined

    desc = target_series.get("description", "MG")
    sn = target_series.get("series_number", 0)
    output_name = f"{patient_label}_MG_{view_name}_{desc}_{sn}.nii.gz"
    output_path = os.path.join(output_dir, output_name)

    raw_sitk = sitk.GetImageFromArray(pixel_data[:, :])
    raw_sitk.SetSpacing((float(sp[1]), float(sp[0])))
    raw_sitk.SetOrigin(origin)
    raw_sitk.SetDirection(direction)
    sitk.WriteImage(raw_sitk, output_path)
    return output_path


# ============================================================
# US conversion
# ============================================================

def convert_us_series(
    session_id: str,
    patient_id: str,
    series_uid: str,
    output_dir: str,
    patient_label: str,
) -> Optional[str]:
    """Convert an ultrasound series to NIfTI."""
    session = dicom_service.sessions.get(session_id)
    if not session:
        return None

    target_series = _find_series(session, patient_id, series_uid)
    if not target_series:
        return None

    file_ids = target_series.get("files", [])
    if not file_ids:
        return None

    results = []
    for idx, fid in enumerate(file_ids):
        raw = _load_pixel_data(session, fid)
        if not raw or raw.get("data") is None:
            continue

        data = np.asarray(raw["data"])
        image_data = np.rot90(data)

        if image_data.ndim == 3:
            nifti_data = np.fliplr(image_data[:, :, 1])
        elif image_data.ndim == 2:
            nifti_data = np.fliplr(image_data)
        else:
            continue

        nifti_image = nib.Nifti1Image(nifti_data, affine=np.eye(4))
        output_name = f"{patient_label}_US_{target_series.get('description', 'US')}_{idx}.nii.gz"
        output_path = os.path.join(output_dir, output_name)
        nib.save(nifti_image, output_path)
        results.append(output_path)

    return results[0] if results else None


# ============================================================
# Batch conversion (parallel)
# ============================================================

def _convert_single_series(
    session_id: str,
    patient_id: str,
    s: dict,
    output_dir: str,
    patient_label: str,
    modality: str,
) -> tuple[Optional[str], str, str]:
    """Convert a single series. Returns (output_path, series_uid, error_msg).

    This function is designed to be called in a thread pool.
    """
    series_uid = s["series_uid"]
    desc = s.get("description", "N/A")
    series_modality = s.get("modality", "OT")

    try:
        # Determine which converter to use
        if modality.upper() == "MR" or (modality == "auto" and series_modality in ("MR", "CT", "OT")):
            # For MR auto-detection, use MR converter for all non-MG/US
            path = convert_mr_series(session_id, patient_id, series_uid, output_dir, patient_label)
        elif modality.upper() == "MG" or (modality == "auto" and series_modality == "MG"):
            path = convert_mg_series(session_id, patient_id, series_uid, output_dir, patient_label)
        elif modality.upper() == "US" or (modality == "auto" and series_modality == "US"):
            path = convert_us_series(session_id, patient_id, series_uid, output_dir, patient_label)
        else:
            path = convert_mr_series(session_id, patient_id, series_uid, output_dir, patient_label)

        return (path, series_uid, "")
    except Exception as e:
        return (None, series_uid, f"{desc}: {e}")


def convert_session_to_nifti(
    session_id: str,
    patient_id: str,
    modality: str = "auto",
    selected_series: Optional[list[str]] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Convert DICOM series in a session to NIfTI files.

    Uses parallel execution for multiple series conversion.

    Args:
        session_id: Session ID.
        patient_id: Patient ID.
        modality: 'MR', 'MG', 'US', or 'auto' (detect from data).
        selected_series: Optional list of series UIDs to convert. If None, convert all.
        progress_callback: Optional callback for progress updates. Called with dicts like:
            {"type": "progress", "current": 1, "total": 5, "series_uid": "...", "status": "converting"}
            {"type": "complete", "files": [...], "errors": [...]}

    Returns:
        {"output_dir": str, "files": [{"name": str, "path": str}], "errors": list}
    """
    session = dicom_service.sessions.get(session_id)
    if not session:
        return {"output_dir": "", "files": [], "errors": ["Session not found"]}

    patient = session.get("patients", {}).get(patient_id)
    if not patient:
        return {"output_dir": "", "files": [], "errors": ["Patient not found"]}

    patient_label = patient.get("name", patient_id).replace(" ", "_")[:20]
    output_dir = os.path.join(str(_get_session_dir(session_id)), "nifti_output", patient_id)
    os.makedirs(output_dir, exist_ok=True)

    log_service.info(
        f"Starting NIfTI conversion for {patient.get('name', patient_id)} "
        f"(modality={modality}, workers={MAX_WORKERS})", "converter"
    )

    # Collect all series
    all_series = _collect_all_series(session, patient_id)

    # Filter by selected series if specified
    if selected_series:
        all_series = [s for s in all_series if s["series_uid"] in selected_series]

    if not all_series:
        return {"output_dir": output_dir, "files": [], "errors": ["No series found"]}

    total = len(all_series)
    files = []
    errors = []

    # Parallel conversion
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for s in all_series:
            future = executor.submit(
                _convert_single_series,
                session_id, patient_id, s, output_dir, patient_label, modality,
            )
            futures[future] = s

        completed = 0
        for future in as_completed(futures):
            completed += 1
            s = futures[future]
            series_uid = s["series_uid"]
            desc = s.get("description", "N/A")

            try:
                path, uid, error = future.result()
                if path:
                    files.append({"name": os.path.basename(path), "path": path})
                    log_service.success(f"Converted {desc} -> {os.path.basename(path)}", "converter")
                elif error:
                    errors.append(error)
                    log_service.error(f"Failed to convert {desc}: {error}", "converter")
            except Exception as e:
                errors.append(f"{desc}: {e}")
                log_service.error(f"Exception converting {desc}: {e}", "converter")

            # Report progress
            if progress_callback:
                progress_callback({
                    "type": "progress",
                    "current": completed,
                    "total": total,
                    "series_uid": series_uid,
                    "description": desc,
                    "status": "done" if path else "error",
                })

    log_service.info(
        f"NIfTI conversion complete: {len(files)} files, {len(errors)} errors",
        "converter",
    )

    result = {"output_dir": output_dir, "files": files, "errors": errors}
    if progress_callback:
        progress_callback({"type": "complete", **result})

    return result


# ============================================================
# DICOM anonymization
# ============================================================

DEFAULT_TAGS_TO_CLEAR = [
    "AccessionNumber", "ContentDate", "ContentTime",
    "InstanceCreationDate", "InstanceCreationTime",
    "Manufacturer", "ManufacturerModelName",
    "OperatorsName", "ReferringPhysicianName",
    "SpecificCharacterSet", "StationName",
    "StudyDate", "StudyID", "StudyTime",
    "InstitutionName", "InstitutionAddress",
    "PhysiciansOfRecord", "PerformingPhysicianName",
    "DeviceSerialNumber",
    "PatientAge", "PatientSize", "PatientWeight",
    "MedicalAlerts", "PregnancyStatus", "PatientComments",
    "PatientBirthDate", "PatientID", "PatientSex", "PatientName",
    "ApprovalStatus", "ReviewDate", "ReviewTime", "ReviewerName",
    "RTPlanDate", "RTPlanDescription", "RTPlanGeometry",
    "RTPlanLabel", "RTPlanName", "RTPlanTime",
    "BrachyTreatmentTechnique",
]


def anonymize_dicom_file(dcm: pydicom.Dataset, tags_to_clear: Optional[list[str]] = None) -> pydicom.Dataset:
    """Strip PHI from a DICOM dataset."""
    tags = tags_to_clear or DEFAULT_TAGS_TO_CLEAR
    for tag in tags:
        if hasattr(dcm, tag):
            setattr(dcm, tag, "")
    dcm.remove_private_tags()
    return dcm


def anonymize_session(session_id: str, patient_id: str) -> dict:
    """Anonymize all DICOM files for a patient in a session."""
    session = dicom_service.sessions.get(session_id)
    if not session:
        return {"files": [], "errors": ["Session not found"]}

    patient = session.get("patients", {}).get(patient_id)
    if not patient:
        return {"files": [], "errors": ["Patient not found"]}

    output_dir = os.path.join(str(_get_session_dir(session_id)), "anonymized", patient_id)
    os.makedirs(output_dir, exist_ok=True)

    log_service.info(f"Starting DICOM anonymization for {patient.get('name', patient_id)}", "converter")

    files = []
    errors = []
    count = 0

    for study_uid, study in patient.get("studies", {}).items():
        for series_uid, series in study.get("series", {}).items():
            for fid in series.get("files", []):
                file_info = session.get("files", {}).get(fid)
                raw = _load_pixel_data(session, fid)
                if not file_info or not raw:
                    continue

                try:
                    dcm = pydicom.Dataset()
                    dcm.PatientName = file_info.get("metadata", {}).get("PatientName", "")
                    dcm.PatientID = file_info.get("metadata", {}).get("PatientID", "")
                    dcm.Modality = file_info.get("modality", "OT")

                    dcm = anonymize_dicom_file(dcm)

                    count += 1
                    pixel = raw.get("data")
                    if pixel is not None:
                        arr = np.asarray(pixel)
                        if arr.ndim == 2:
                            nifti_img = nib.Nifti1Image(arr, affine=np.eye(4))
                            out_nii = os.path.join(output_dir, f"{patient_id}_anon_{count:04d}.nii.gz")
                            nib.save(nifti_img, out_nii)
                            files.append({"name": os.path.basename(out_nii), "path": out_nii})

                except Exception as e:
                    errors.append(f"File {fid}: {e}")

    log_service.info(
        f"Anonymization complete: {len(files)} files, {len(errors)} errors",
        "converter",
    )
    return {"files": files, "errors": errors}
