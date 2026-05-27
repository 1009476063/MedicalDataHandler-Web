import numpy as np
from typing import Optional
import pydicom
from PIL import Image, ImageDraw


class RTStructBuilder:
    def __init__(self):
        self._cache: dict[str, dict] = {}

    def _get_session(self, session_id: str) -> Optional[dict]:
        from app.services.dicom_service import dicom_service
        return dicom_service.sessions.get(session_id)

    def _find_rtstruct_ds(self, session: dict, patient_id: str, struct_key: str):
        """Find and parse the RTSTRUCT dataset containing the given ROI."""
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] != patient_id or finfo["modality"] != "RTSTRUCT":
                continue
            raw_info = session["raw_data"].get(fid)
            if not raw_info or "raw_bytes" not in raw_info:
                continue
            try:
                ds = pydicom.dcmread(
                    pydicom.filebase.DicomBytesIO(raw_info["raw_bytes"]),
                    force=True
                )
                if not hasattr(ds, "StructureSetROISequence"):
                    continue
                for roi in ds.StructureSetROISequence:
                    if str(roi.ROINumber) == struct_key:
                        return ds, roi, fid
            except Exception:
                continue
        return None, None, None

    def get_structs(self, session_id: str, patient_id: str) -> Optional[list[dict]]:
        session = self._get_session(session_id)
        if not session:
            return None

        structs = []
        for fid, finfo in session["files"].items():
            if finfo["patient_id"] != patient_id or finfo["modality"] != "RTSTRUCT":
                continue
            raw_info = session["raw_data"].get(fid)
            if not raw_info or "raw_bytes" not in raw_info:
                continue
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
            except Exception:
                continue

        return structs if structs else None

    def get_mask(
        self, session_id: str, patient_id: str,
        struct_key: str, slice_index: int, orientation: str = "axial",
        image_shape: Optional[tuple[int, int]] = None,
    ) -> Optional[dict]:
        session = self._get_session(session_id)
        if not session:
            return None

        ds, roi, fid = self._find_rtstruct_ds(session, patient_id, struct_key)
        if ds is None:
            return None

        contour_data = self._get_roi_contours(ds, roi.ROINumber)
        if not contour_data:
            return None

        # Use actual CT dimensions or fallback to 256x256
        h, w = image_shape if image_shape else (256, 256)
        mask = self._contour_to_mask(contour_data, slice_index, orientation, h, w)

        return {
            "mask": mask.tolist() if mask is not None else None,
            "shape": list(mask.shape) if mask is not None else [h, w],
            "name": str(roi.ROIName),
        }

    def _get_roi_contours(self, ds, roi_number) -> Optional[list]:
        if not hasattr(ds, "ROIContourSequence"):
            return None
        for contour in ds.ROIContourSequence:
            if hasattr(contour, "ROINumber") and str(contour.ROINumber) == str(roi_number):
                if hasattr(contour, "ContourSequence"):
                    contours = []
                    for c in contour.ContourSequence:
                        if hasattr(c, "ContourData"):
                            data = [float(x) for x in c.ContourData]
                            contours.append(data)
                    return contours
        return None

    def _contour_to_mask(
        self, contour_data: list, slice_index: int, orientation: str,
        height: int, width: int
    ) -> Optional[np.ndarray]:
        mask = np.zeros((height, width), dtype=np.uint8)
        for points in contour_data:
            if len(points) < 9:
                continue
            coords = np.array(points).reshape(-1, 3)
            if orientation == "axial":
                xs = coords[:, 0]
                ys = coords[:, 1]
            elif orientation == "sagittal":
                xs = coords[:, 1]
                ys = coords[:, 2]
            else:
                xs = coords[:, 0]
                ys = coords[:, 2]

            # Densify contour: interpolate between consecutive points
            xs, ys = self._densify_contour(xs, ys)

            img = Image.fromarray(mask)
            draw = ImageDraw.Draw(img)
            polygon = list(zip(xs.astype(int), ys.astype(int)))
            if len(polygon) >= 3:
                draw.polygon(polygon, fill=1)
            mask = np.array(img)

        return mask

    def _densify_contour(self, xs: np.ndarray, ys: np.ndarray, spacing: float = 1.0):
        """Add intermediate points along the contour for smoother rendering."""
        if len(xs) < 3:
            return xs, ys

        new_xs = [xs[0]]
        new_ys = [ys[0]]

        for i in range(1, len(xs)):
            dx = xs[i] - xs[i - 1]
            dy = ys[i] - ys[i - 1]
            dist = np.sqrt(dx * dx + dy * dy)
            if dist > spacing:
                n_steps = int(dist / spacing)
                for j in range(1, n_steps):
                    t = j / n_steps
                    new_xs.append(xs[i - 1] + t * dx)
                    new_ys.append(ys[i - 1] + t * dy)
            new_xs.append(xs[i])
            new_ys.append(ys[i])

        return np.array(new_xs), np.array(new_ys)

    def get_center_of_mass(
        self, session_id: str, patient_id: str, struct_key: str,
        orientation: str = "axial", image_shape: Optional[tuple[int, int]] = None,
    ) -> Optional[dict]:
        """Compute the center of mass of a structure across all slices."""
        session = self._get_session(session_id)
        if not session:
            return None

        ds, roi, fid = self._find_rtstruct_ds(session, patient_id, struct_key)
        if ds is None:
            return None

        contour_data = self._get_roi_contours(ds, roi.ROINumber)
        if not contour_data:
            return None

        h, w = image_shape if image_shape else (256, 256)
        all_coords = []
        for points in contour_data:
            if len(points) < 9:
                continue
            coords = np.array(points).reshape(-1, 3)
            all_coords.append(coords)

        if not all_coords:
            return None

        combined = np.vstack(all_coords)
        if orientation == "axial":
            center = combined.mean(axis=0)
            return {"x": float(center[0]), "y": float(center[1]), "z": float(center[2])}
        elif orientation == "sagittal":
            center = combined.mean(axis=0)
            return {"x": float(center[1]), "y": float(center[2]), "z": float(center[0])}
        else:
            center = combined.mean(axis=0)
            return {"x": float(center[0]), "y": float(center[2]), "z": float(center[1])}

    def get_roi_bounds(
        self, session_id: str, patient_id: str, struct_key: str,
    ) -> Optional[dict]:
        """Compute bounding box and center slice indices for a structure.

        Returns the min/max coordinates across all contour points and the
        center slice index for each orientation (axial, sagittal, coronal).
        """
        session = self._get_session(session_id)
        if not session:
            return None

        ds, roi, fid = self._find_rtstruct_ds(session, patient_id, struct_key)
        if ds is None:
            return None

        contour_data = self._get_roi_contours(ds, roi.ROINumber)
        if not contour_data:
            return None

        all_coords = []
        for points in contour_data:
            if len(points) < 9:
                continue
            coords = np.array(points).reshape(-1, 3)
            all_coords.append(coords)

        if not all_coords:
            return None

        combined = np.vstack(all_coords)
        # DICOM coordinates: X (left-right), Y (anterior-posterior), Z (superior-inferior)
        x_min, x_max = float(combined[:, 0].min()), float(combined[:, 0].max())
        y_min, y_max = float(combined[:, 1].min()), float(combined[:, 1].max())
        z_min, z_max = float(combined[:, 2].min()), float(combined[:, 2].max())

        return {
            "name": str(roi.ROIName),
            "bounds": {
                "x": [x_min, x_max],
                "y": [y_min, y_max],
                "z": [z_min, z_max],
            },
            "center": {
                "x": (x_min + x_max) / 2,
                "y": (y_min + y_max) / 2,
                "z": (z_min + z_max) / 2,
            },
        }
