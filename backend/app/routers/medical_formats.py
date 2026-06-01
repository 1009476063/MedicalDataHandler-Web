"""Router for uploading non-DICOM medical image formats (NIfTI, NRRD, MHA/MHD)."""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.dicom_service import dicom_service
from app.services.nifti_service import load_medical_file, extract_synthetic_metadata
from app.services.log_service import log_service


router = APIRouter()


class MedicalUploadResponse(BaseModel):
    session_id: str
    patients: list[dict]
    file_count: int


SUPPORTED_EXTENSIONS = (".nii", ".nii.gz", ".nrrd", ".nhdr", ".mha", ".mhd")


def _is_supported_format(filename: str) -> bool:
    name_lower = filename.lower()
    return any(name_lower.endswith(ext) for ext in SUPPORTED_EXTENSIONS)


@router.post("/upload/medical", response_model=MedicalUploadResponse)
async def upload_medical_files(files: list[UploadFile] = File(...)):
    """Upload NIfTI, NRRD, or MHA/MHD medical image files.

    Accepts multipart form data with one or more files. Each file is parsed
    using the appropriate library (nibabel, pynrrd, or SimpleITK) and stored
    in the same session format as DICOM uploads, so the existing frontend
    viewer works without modification.
    """
    file_bytes_list = []
    for f in files:
        if not _is_supported_format(f.filename or ""):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file format: '{f.filename}'. "
                    f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
                ),
            )
        content = await f.read()
        file_bytes_list.append((f.filename, content))

    result = await _process_uploads(file_bytes_list)
    return result


async def _process_uploads(file_bytes_list: list[tuple[str, bytes]]) -> dict:
    """Parse medical files and create a session compatible with the DICOM viewer."""
    dicom_service._cleanup_expired()
    session_id = uuid.uuid4().hex

    # Initialize session in the shared dicom_service so all viewers can access it
    dicom_service.sessions[session_id] = {
        "files": {},
        "patients": {},
        "series": {},
        "studies": {},
        "raw_data": {},
    }
    dicom_service._touch_session(session_id)

    log_service.info(
        f"Medical format upload started: {len(file_bytes_list)} file(s)", "upload"
    )

    success_count = 0
    for filename, content in file_bytes_list:
        try:
            volume = load_medical_file(content, filename)
            _store_volume(session_id, volume, filename)
            success_count += 1
        except Exception as e:
            log_service.warning(f"Failed to parse {filename}: {e}", "upload")
            continue

    patients = dicom_service._build_patient_list(session_id)
    log_service.success(
        f"Medical format upload complete: {success_count}/{len(file_bytes_list)} files, "
        f"{len(patients)} patient(s)",
        "upload",
    )
    return {
        "session_id": session_id,
        "patients": patients,
        "file_count": len(dicom_service.sessions[session_id]["files"]),
    }


def _store_volume(session_id: str, volume, filename: str) -> None:
    """Store a MedicalVolumeData in the session, splitting 3D volumes into slices.

    The existing ImageBuilder expects individual 2D slices stored in raw_data,
    each with a matching file entry in session["files"]. For a 3D volume of
    shape (D, H, W), we create D file+raw_data entries so the image builder
    can sort by slice_location and stack them without modification.
    """
    session = dicom_service.sessions[session_id]
    metadata = extract_synthetic_metadata(volume)
    modality = metadata["Modality"]

    # Generate stable IDs for the patient, study, and series
    patient_id = metadata["PatientID"]
    study_uid = f"1.2.826.0.1.3680043.8.1.{session_id}.1"
    series_uid = f"1.2.826.0.1.3680043.8.2.{session_id}.1"

    # Create patient entry if not exists
    if patient_id not in session["patients"]:
        session["patients"][patient_id] = {
            "patient_id": patient_id,
            "name": metadata["PatientName"],
            "birth_date": metadata["PatientBirthDate"],
            "sex": metadata["PatientSex"],
            "studies": {},
        }

    patient = session["patients"][patient_id]
    if study_uid not in patient["studies"]:
        patient["studies"][study_uid] = {
            "study_uid": study_uid,
            "description": metadata["StudyDescription"],
            "date": metadata["StudyDate"],
            "series": {},
        }

    study = patient["studies"][study_uid]
    if series_uid not in study["series"]:
        study["series"][series_uid] = {
            "series_uid": series_uid,
            "description": metadata["SeriesDescription"],
            "modality": modality,
            "series_number": metadata["SeriesNumber"],
            "files": [],
            "file_count": 0,
        }

    pixel_data = volume.pixel_data

    # For 3D volumes, split into individual 2D axial slices
    if pixel_data.ndim == 3:
        num_slices = pixel_data.shape[0]
        z_spacing = volume.spacing[0] if len(volume.spacing) > 0 else 1.0
        y_spacing = volume.spacing[1] if len(volume.spacing) > 1 else 1.0
        x_spacing = volume.spacing[2] if len(volume.spacing) > 2 else 1.0

        for i in range(num_slices):
            file_id = str(uuid.uuid4())[:8]
            slice_data = pixel_data[i]

            file_info = {
                "id": file_id,
                "filename": filename,
                "modality": modality,
                "patient_id": patient_id,
                "study_uid": study_uid,
                "series_uid": series_uid,
                "metadata": metadata,
                "all_tags": {},
            }
            session["files"][file_id] = file_info
            study["series"][series_uid]["files"].append(file_id)
            study["series"][series_uid]["file_count"] += 1

            # Store pixel data in the format ImageBuilder._build_volume expects
            slice_location = i * z_spacing
            session["raw_data"][file_id] = {
                "data": slice_data.astype(np.float64),
                "shape": list(slice_data.shape),
                "position": [
                    float(volume.origin[0]),
                    float(volume.origin[1]),
                    float(volume.origin[2]) + slice_location,
                ],
                "spacing": [float(y_spacing), float(x_spacing)],
                "slice_location": float(slice_location),
                "instance_number": i + 1,
            }

    elif pixel_data.ndim == 2:
        # Single 2D image (e.g., a single slice)
        file_id = str(uuid.uuid4())[:8]
        file_info = {
            "id": file_id,
            "filename": filename,
            "modality": modality,
            "patient_id": patient_id,
            "study_uid": study_uid,
            "series_uid": series_uid,
            "metadata": metadata,
            "all_tags": {},
        }
        session["files"][file_id] = file_info
        study["series"][series_uid]["files"].append(file_id)
        study["series"][series_uid]["file_count"] += 1

        y_spacing = volume.spacing[1] if len(volume.spacing) > 1 else 1.0
        x_spacing = volume.spacing[2] if len(volume.spacing) > 2 else 1.0

        session["raw_data"][file_id] = {
            "data": pixel_data.astype(np.float64),
            "shape": list(pixel_data.shape),
            "position": [float(v) for v in volume.origin],
            "spacing": [float(y_spacing), float(x_spacing)],
            "slice_location": 0.0,
            "instance_number": 1,
        }

    else:
        raise ValueError(
            f"Unexpected number of dimensions ({pixel_data.ndim}) for '{filename}'. "
            "Expected 2D or 3D data."
        )


# numpy import needed by _store_volume
import numpy as np
