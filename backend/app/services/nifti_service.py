"""Service for loading NIfTI (.nii, .nii.gz), NRRD (.nrrd, .nhdr), and ITK (.mha, .mhd) files."""

import numpy as np
import tempfile
import os
from pathlib import Path
from typing import Optional


class MedicalVolumeData:
    """Standardized container for medical image volume data."""

    def __init__(
        self,
        pixel_data: np.ndarray,
        spacing: list[float],
        origin: list[float],
        orientation: str,
        dtype: str,
        filename: str,
    ):
        self.pixel_data = pixel_data
        self.spacing = spacing  # [z, y, x] in mm
        self.origin = origin  # [x, y, z] in mm
        self.orientation = orientation
        self.dtype = dtype
        self.filename = filename

    @property
    def shape(self) -> list[int]:
        return list(self.pixel_data.shape)

    def to_raw_data(self) -> dict:
        """Convert to the format expected by ImageBuilder._build_volume.

        Returns a dict matching the structure that dicom_service stores in
        session["raw_data"], so the existing image builder can consume it
        without modification.
        """
        return {
            "data": self.pixel_data.astype(np.float64),
            "shape": list(self.pixel_data.shape),
            "spacing": self.spacing,
            "origin": self.origin,
            "orientation": self.orientation,
            "dtype": self.dtype,
            "position": [0.0, 0.0, 0.0],
            "slice_location": 0.0,
            "instance_number": 0,
        }


def load_nifti(file_bytes: bytes, filename: str) -> MedicalVolumeData:
    """Load a NIfTI file (.nii or .nii.gz) using nibabel.

    nibabel requires a file path, so we write to a temp file first.

    Args:
        file_bytes: Raw file content.
        filename: Original filename (used for metadata hints and temp suffix).

    Returns:
        MedicalVolumeData with extracted pixel data and metadata.

    Raises:
        ValueError: If the file cannot be parsed as NIfTI.
    """
    import nibabel as nib

    suffix = ".nii.gz" if filename.lower().endswith(".nii.gz") else ".nii"
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        img = nib.load(tmp_path)
        pixel_data = np.asarray(img.dataobj)

        affine = img.affine
        header = img.header

        # Voxel sizes from header
        pixdim = header.get_zooms()
        spacing = [float(pixdim[i]) if i < len(pixdim) else 1.0 for i in range(3)]

        # Origin from affine (last column, first 3 rows)
        origin = [float(affine[i, 3]) for i in range(3)]

        # Orientation as string (e.g., "RAS", "LPI")
        try:
            axes_codes = nib.aff2axcodes(affine)
            orientation = "".join(axes_codes)
        except Exception:
            orientation = "RAS"

        # Slope/intercept for HU conversion (CT data)
        if hasattr(header, "get_slope_intercept"):
            slope, intercept = header.get_slope_intercept()
            slope = float(slope) if slope is not None else 1.0
            intercept = float(intercept) if intercept is not None else 0.0
        else:
            slope = 1.0
            intercept = 0.0
        if slope != 1.0 or intercept != 0.0:
            pixel_data = pixel_data.astype(np.float64) * slope + intercept

        dtype = str(pixel_data.dtype)

        return MedicalVolumeData(
            pixel_data=pixel_data,
            spacing=spacing,
            origin=origin,
            orientation=orientation,
            dtype=dtype,
            filename=filename,
        )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to parse NIfTI file '{filename}': {e}") from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_nrrd(file_bytes: bytes, filename: str) -> MedicalVolumeData:
    """Load a NRRD file (.nrrd or .nhdr) using pynrrd.

    pynrrd requires a file path, so we write to a temp file first.

    Args:
        file_bytes: Raw file content.
        filename: Original filename.

    Returns:
        MedicalVolumeData with extracted pixel data and metadata.

    Raises:
        ValueError: If the file cannot be parsed as NRRD.
    """
    import nrrd

    suffix = ".nhdr" if filename.lower().endswith(".nhdr") else ".nrrd"
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        pixel_data, header = nrrd.read(tmp_path)

        # Spacing from space directions
        spacing = [1.0, 1.0, 1.0]
        if "space directions" in header:
            dirs = header["space directions"]
            for i in range(min(3, len(dirs))):
                d = dirs[i]
                if d is not None and hasattr(d, "__len__"):
                    spacing[i] = float(np.linalg.norm(d))
                elif d is not None:
                    spacing[i] = float(abs(d))

        # Origin from space origin
        origin = [0.0, 0.0, 0.0]
        if "space origin" in header:
            try:
                origin = [float(x) for x in header["space origin"][:3]]
            except Exception:
                pass

        # Orientation
        orientation = "RAS"
        if "space" in header:
            space = header["space"]
            if len(space) >= 3:
                orientation = space[:3].upper()

        # Apply slope/intercept if present
        slope = float(header.get("pixel energy scaling slope", 1.0))
        intercept = float(header.get("pixel energy scaling intercept", 0.0))
        if slope != 1.0 or intercept != 0.0:
            pixel_data = pixel_data.astype(np.float64) * slope + intercept

        dtype = str(pixel_data.dtype)

        return MedicalVolumeData(
            pixel_data=pixel_data,
            spacing=spacing,
            origin=origin,
            orientation=orientation,
            dtype=dtype,
            filename=filename,
        )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to parse NRRD file '{filename}': {e}") from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_itk(file_bytes: bytes, filename: str) -> MedicalVolumeData:
    """Load an ITK file (.mha, .mhd) using SimpleITK.

    SimpleITK requires a file path, so we write to a temp file first.

    Args:
        file_bytes: Raw file content.
        filename: Original filename.

    Returns:
        MedicalVolumeData with extracted pixel data and metadata.

    Raises:
        ValueError: If the file cannot be parsed as ITK format.
    """
    import SimpleITK as sitk

    suffix = ".mhd" if filename.lower().endswith(".mhd") else ".mha"
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        img = sitk.ReadImage(tmp_path)
        pixel_data = sitk.GetArrayFromImage(img)

        # Spacing: SimpleITK returns [x, y, z], we store as [z, y, x]
        itk_spacing = img.GetSpacing()
        spacing = [float(itk_spacing[2]), float(itk_spacing[1]), float(itk_spacing[0])]

        # Origin: SimpleITK returns [x, y, z]
        itk_origin = img.GetOrigin()
        origin = [float(itk_origin[0]), float(itk_origin[1]), float(itk_origin[2])]

        # Orientation from direction matrix
        direction = img.GetDirection()
        dim = img.GetDimension()
        orientation = "RAS"
        if dim >= 3:
            signs = []
            for col in range(3):
                col_start = col * dim
                for row in range(dim):
                    val = direction[col_start + row]
                    if abs(val) > 0.5:
                        axis_label = ["R", "A", "S"][row] if val > 0 else ["L", "P", "I"][row]
                        signs.append(axis_label)
                        break
            if len(signs) == 3:
                orientation = "".join(signs)

        dtype = str(pixel_data.dtype)

        return MedicalVolumeData(
            pixel_data=pixel_data,
            spacing=spacing,
            origin=origin,
            orientation=orientation,
            dtype=dtype,
            filename=filename,
        )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to parse ITK file '{filename}': {e}") from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_medical_file(file_bytes: bytes, filename: str) -> MedicalVolumeData:
    """Load a medical image file by detecting its format from the extension.

    Supported formats:
    - .nii, .nii.gz (NIfTI)
    - .nrrd, .nhdr (NRRD)
    - .mha, .mhd (ITK/SimpleITK)

    Args:
        file_bytes: Raw file content.
        filename: Original filename (used for format detection).

    Returns:
        MedicalVolumeData with extracted pixel data and metadata.

    Raises:
        ValueError: If the format is unsupported or the file is malformed.
    """
    name_lower = filename.lower()

    if name_lower.endswith(".nii") or name_lower.endswith(".nii.gz"):
        return load_nifti(file_bytes, filename)
    elif name_lower.endswith(".nrrd") or name_lower.endswith(".nhdr"):
        return load_nrrd(file_bytes, filename)
    elif name_lower.endswith(".mha") or name_lower.endswith(".mhd"):
        return load_itk(file_bytes, filename)
    else:
        raise ValueError(
            f"Unsupported file format: '{filename}'. "
            "Supported formats: .nii, .nii.gz, .nrrd, .nhdr, .mha, .mhd"
        )


def extract_synthetic_metadata(volume: MedicalVolumeData) -> dict:
    """Extract DICOM-like metadata from a medical volume for frontend compatibility.

    NIfTI/NRRD/MHA files lack DICOM tags, so we generate synthetic metadata
    that the frontend can display.
    """
    name_stem = Path(volume.filename).stem
    # Handle .nii.gz -> stem is "file.nii", need to strip further
    if name_stem.endswith(".nii"):
        name_stem = name_stem[:-4]

    # Try to guess modality from filename hints
    modality = "OT"  # Other
    name_lower = name_stem.lower()
    if any(kw in name_lower for kw in ("ct", "computed", "attenuation")):
        modality = "CT"
    elif any(kw in name_lower for kw in ("mr", "mri", "t1", "t2", "flair", "dwi")):
        modality = "MR"
    elif any(kw in name_lower for kw in ("pet", "pt")):
        modality = "PT"
    elif any(kw in name_lower for kw in ("rt", "dose", "struct")):
        modality = "RT"

    return {
        "PatientName": name_stem,
        "PatientID": f"NIFTI-{name_stem}",
        "PatientBirthDate": "",
        "PatientSex": "",
        "StudyDescription": f"Imported from {volume.filename}",
        "StudyDate": "",
        "StudyTime": "",
        "StudyInstanceUID": "",
        "SeriesDescription": name_stem,
        "Modality": modality,
        "SeriesInstanceUID": "",
        "SeriesNumber": "1",
        "InstanceNumber": "1",
        "ImagePositionPatient": [str(v) for v in volume.origin],
        "SliceLocation": "0",
        "PixelSpacing": [str(volume.spacing[1]), str(volume.spacing[2])],
        "Rows": str(volume.shape[-2]),
        "Columns": str(volume.shape[-1]),
        "BitsAllocated": "32" if volume.dtype in ("float32", "float64") else "16",
        "BitsStored": "32" if volume.dtype in ("float32", "float64") else "16",
        "NumberOfFrames": str(volume.shape[0]) if volume.pixel_data.ndim == 3 else "1",
        "PhotometricInterpretation": "MONOCHROME2",
    }
