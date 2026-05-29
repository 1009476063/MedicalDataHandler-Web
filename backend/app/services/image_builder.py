import numpy as np
from typing import Optional
import pydicom
import SimpleITK as sitk
from collections import defaultdict


class ImageBuilder:
    def __init__(self):
        self._cache: dict[str, dict] = {}

    def _build_volume(self, session, patient_id: str, series_uid: Optional[str] = None) -> Optional[dict]:
        cache_key = f"{session.get('session_id', '')}_{patient_id}_{series_uid or 'all'}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        files = []
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] != patient_id:
                continue
            if finfo["modality"] not in ("CT", "MR", "PT", "NM", "OT"):
                continue
            if series_uid and finfo["series_uid"] != series_uid:
                continue
            if fid in session["raw_data"] and session["raw_data"][fid] is not None:
                raw = session["raw_data"][fid]
                # Load from disk if data_path is available (disk-based storage)
                if "data_path" in raw and raw["data_path"]:
                    try:
                        pixel_array = np.load(raw["data_path"])
                        raw = {**raw, "data": pixel_array}
                    except Exception:
                        continue
                if "data" in raw:
                    files.append((fid, raw))

        if not files:
            return None

        files.sort(key=lambda x: x[1].get("slice_location", x[1].get("instance_number", 0)))

        slices = []
        for fid, data in files:
            slices.append(data)

        if not slices:
            return None

        pixel_data = np.stack([s["data"] for s in slices], axis=0)

        # Calculate spacing - ensure all values are plain Python floats
        if len(slices) > 1:
            spacing_z = float(abs(slices[1]["slice_location"] - slices[0]["slice_location"]))
        else:
            spacing_z = 1.0
        spacing_y = float(slices[0]["spacing"][0])
        spacing_x = float(slices[0]["spacing"][1])

        # Ensure origin is a list of plain Python floats
        raw_origin = slices[0]["position"]
        if hasattr(raw_origin, 'tolist'):
            origin = [float(x) for x in raw_origin.tolist()]
        elif isinstance(raw_origin, (list, tuple)):
            origin = [float(x) for x in raw_origin]
        else:
            origin = [0.0, 0.0, 0.0]

        result = {
            "array": pixel_data,
            "shape": list(pixel_data.shape),
            "spacing": [spacing_z, spacing_y, spacing_x],
            "origin": origin,
            "dtype": str(pixel_data.dtype),
            "min": float(pixel_data.min()),
            "max": float(pixel_data.max()),
            "mean": float(pixel_data.mean()),
        }

        self._cache[cache_key] = result
        return result

    def get_slice(
        self, session_id: str, patient_id: str, series_uid: str,
        orientation: str, slice_index: int,
        window_center: Optional[float] = None,
        window_width: Optional[float] = None
    ) -> Optional[dict]:
        from app.services.dicom_service import dicom_service
        session = dicom_service.sessions.get(session_id)
        if not session:
            return None

        volume = self._build_volume(session, patient_id, series_uid)
        if volume is None:
            return None

        arr = volume["array"]

        if orientation == "axial":
            max_idx = arr.shape[0]
            if slice_index < 0 or slice_index >= max_idx:
                slice_index = max_idx // 2
            slice_data = arr[slice_index, :, :]
        elif orientation == "sagittal":
            max_idx = arr.shape[2]
            if slice_index < 0 or slice_index >= max_idx:
                slice_index = max_idx // 2
            slice_data = arr[:, :, slice_index]
        elif orientation == "coronal":
            max_idx = arr.shape[1]
            if slice_index < 0 or slice_index >= max_idx:
                slice_index = max_idx // 2
            slice_data = arr[:, slice_index, :]
        else:
            return None

        if window_center is not None and window_width is not None:
            min_val = window_center - window_width / 2
            max_val = window_center + window_width / 2
            slice_data = np.clip(slice_data, min_val, max_val)
            if max_val > min_val:
                slice_data = ((slice_data - min_val) / (max_val - min_val) * 255).astype(np.uint8)
            else:
                slice_data = np.zeros_like(slice_data, dtype=np.uint8)
        else:
            p_min, p_max = np.percentile(slice_data, [1, 99])
            if p_max > p_min:
                slice_data = ((slice_data - p_min) / (p_max - p_min) * 255).astype(np.uint8)
            else:
                slice_data = np.zeros_like(slice_data, dtype=np.uint8)

        return {
            "data": slice_data.tolist(),
            "shape": list(slice_data.shape),
            "orientation": orientation,
            "slice_index": slice_index,
            "max_slice": arr.shape[0] if orientation == "axial" else (arr.shape[2] if orientation == "sagittal" else arr.shape[1]),
            "spacing": volume["spacing"],
            "window_center": window_center,
            "window_width": window_width,
        }

    def get_series_info(self, session_id: str, patient_id: str, series_uid: str) -> Optional[dict]:
        from app.services.dicom_service import dicom_service
        session = dicom_service.sessions.get(session_id)
        if not session:
            return None

        volume = self._build_volume(session, patient_id, series_uid)
        if volume is None:
            return None

        return {
            "shape": volume["shape"],
            "spacing": volume["spacing"],
            "origin": volume["origin"],
            "min": volume["min"],
            "max": volume["max"],
            "mean": volume["mean"],
        }

    def get_volume(self, session_id: str, patient_id: str, series_uid: Optional[str] = None) -> Optional[dict]:
        from app.services.dicom_service import dicom_service
        session = dicom_service.sessions.get(session_id)
        if not session:
            return None
        return self._build_volume(session, patient_id, series_uid)

    def get_volume_binary(self, session_id: str, patient_id: str, series_uid: Optional[str] = None) -> Optional[dict]:
        """Return raw 3D volume as bytes with metadata headers for Cornerstone3D."""
        from app.services.dicom_service import dicom_service
        session = dicom_service.sessions.get(session_id)
        if not session:
            return None
        volume = self._build_volume(session, patient_id, series_uid)
        if volume is None:
            return None
        arr = volume["array"]
        return {
            "data": arr.tobytes(),
            "shape": list(arr.shape),
            "spacing": volume["spacing"],
            "origin": volume["origin"],
            "dtype": str(arr.dtype),
        }
