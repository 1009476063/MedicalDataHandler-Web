import numpy as np
from typing import Optional
import pydicom

from app.utils.cache import LRUCache


# 14-color dose colormap (blue → green → yellow → red)
DOSE_COLORMAP = [
    (0.00, [0, 0, 128]),
    (0.07, [0, 0, 255]),
    (0.14, [0, 128, 255]),
    (0.21, [0, 255, 255]),
    (0.28, [0, 255, 128]),
    (0.35, [0, 255, 0]),
    (0.42, [128, 255, 0]),
    (0.50, [255, 255, 0]),
    (0.57, [255, 192, 0]),
    (0.64, [255, 128, 0]),
    (0.71, [255, 64, 0]),
    (0.78, [255, 0, 0]),
    (0.85, [224, 0, 0]),
    (1.00, [128, 0, 0]),
]


class RTDoseBuilder:
    def __init__(self):
        self._cache = LRUCache(maxsize=3)

    def _get_session(self, session_id: str) -> Optional[dict]:
        from app.services.dicom_service import dicom_service
        return dicom_service.sessions.get(session_id)

    def _find_rtdose_ds(self, session_id: str, session: dict, patient_id: str, dose_uid: str):
        """Find and parse the RTDOSE dataset."""
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] != patient_id or finfo["modality"] != "RTDOSE":
                continue
            if finfo.get("file_id") != dose_uid and fid != dose_uid and finfo.get("series_uid") != dose_uid:
                continue
            raw_bytes = dicom_service.load_raw_dicom(session_id, fid)
            if not raw_bytes:
                continue
            try:
                ds = pydicom.dcmread(
                    pydicom.filebase.DicomBytesIO(raw_bytes),
                    force=True
                )
                return ds, fid
            except Exception:
                continue
        return None, None

    def get_dose_info(self, session_id: str, patient_id: str) -> list[dict]:
        session = self._get_session(session_id)
        if not session:
            return []

        doses = []
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] == patient_id and finfo["modality"] == "RTDOSE":
                dose_units = "GY"
                dose_type = "PHYSICAL"
                raw_bytes = dicom_service.load_raw_dicom(session_id, fid)
                if raw_bytes:
                    try:
                        ds = pydicom.dcmread(
                            pydicom.filebase.DicomBytesIO(raw_bytes),
                            force=True
                        )
                        dose_units = str(getattr(ds, "DoseUnits", "GY"))
                        dose_type = str(getattr(ds, "DoseType", "PHYSICAL"))
                    except Exception:
                        pass
                doses.append({
                    "file_id": fid,
                    "filename": finfo["filename"],
                    "metadata": finfo["metadata"],
                    "dose_units": dose_units,
                    "dose_type": dose_type,
                })
        return doses

    def get_dose_slice(
        self, session_id: str, patient_id: str,
        dose_uid: str, slice_index: int, orientation: str = "axial"
    ) -> Optional[dict]:
        session = self._get_session(session_id)
        if not session:
            return None

        ds, fid = self._find_rtdose_ds(session_id, session, patient_id, dose_uid)
        if ds is None:
            return None

        dose_grid = self._extract_dose_grid(ds)
        if dose_grid is None:
            return None

        # Apply DoseGridScaling
        scale = float(getattr(ds, "DoseGridScaling", 1.0))
        dose_grid = dose_grid * scale

        # Validate dose metadata
        dose_units = str(getattr(ds, "DoseUnits", "GY"))
        dose_type = str(getattr(ds, "DoseType", "PHYSICAL"))

        if orientation == "axial":
            if slice_index >= dose_grid.shape[0]:
                slice_index = dose_grid.shape[0] // 2
            slice_data = dose_grid[slice_index, :, :]
        elif orientation == "sagittal":
            if slice_index >= dose_grid.shape[2]:
                slice_index = dose_grid.shape[2] // 2
            slice_data = dose_grid[:, :, slice_index]
        else:
            if slice_index >= dose_grid.shape[1]:
                slice_index = dose_grid.shape[1] // 2
            slice_data = dose_grid[:, slice_index, :]

        # Compute DMax-based range
        d_max = float(dose_grid.max())
        d_min_display = 0.0
        d_max_display = d_max

        return {
            "data": slice_data.tolist(),
            "shape": list(slice_data.shape),
            "min": float(slice_data.min()),
            "max": float(slice_data.max()),
            "d_max": d_max,
            "d_min_display": d_min_display,
            "d_max_display": d_max_display,
            "dose_units": dose_units,
            "dose_type": dose_type,
            "scale": scale,
            "slice_index": slice_index,
            "orientation": orientation,
        }

    def get_dose_colormap(self) -> list[list]:
        """Return the 14-color dose colormap."""
        return [[pos, r, g, b] for pos, (r, g, b) in DOSE_COLORMAP]

    def _extract_dose_grid(self, ds) -> Optional[np.ndarray]:
        try:
            pixel_array = ds.pixel_array
            if hasattr(ds, "NumberOfFrames"):
                n_frames = int(ds.NumberOfFrames)
                if pixel_array.ndim == 3 and pixel_array.shape[0] == n_frames:
                    return pixel_array.astype(np.float64)
                elif pixel_array.ndim == 2:
                    return pixel_array.reshape(1, *pixel_array.shape).astype(np.float64)
            return pixel_array.astype(np.float64)
        except Exception:
            return None
