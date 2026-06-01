"""ROI (Region of Interest) label-map service.

Manages 3D label maps for manual and AI-assisted ROI drawing.
Supports painting, shape fill, magic-wand region growing,
morphological post-processing, undo/redo, and NIfTI/DICOM SEG export.
"""

import io
import zlib
import uuid
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import nibabel as nib
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence as DicomSequence
from scipy import ndimage

logger = logging.getLogger(__name__)

# Maximum undo history depth
MAX_UNDO_DEPTH = 30

# Orientation → axis mapping (volume stored as Z, Y, X)
ORIENTATION_AXIS = {
    "axial": 0,
    "coronal": 1,
    "sagittal": 2,
}


@dataclass
class LabelEntry:
    """Single label definition."""
    id: int
    name: str
    color: str  # "#RRGGBB"
    visible: bool = True
    opacity: float = 0.4
    locked: bool = False


@dataclass
class LabelMap:
    """3D label map with undo history."""
    id: str
    session_id: str
    patient_id: str
    series_uid: str
    volume: np.ndarray  # uint8, shape (Z, Y, X), values = label id
    shape: list
    spacing: list
    origin: list
    labels: list = field(default_factory=list)  # list of LabelEntry dicts
    undo_stack: list = field(default_factory=list)  # list of compressed snapshots
    redo_stack: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


class ROIService:
    """Singleton managing all ROI label maps."""

    def __init__(self):
        self._rois: dict[str, LabelMap] = {}

    def create_label_map(
        self,
        session_id: str,
        patient_id: str,
        series_uid: str,
        shape: list,
        spacing: list,
        origin: list,
        name: str = "",
    ) -> str:
        """Create an empty label map and return its ID."""
        label_map_id = str(uuid.uuid4())
        volume = np.zeros(shape, dtype=np.uint8)

        lm = LabelMap(
            id=label_map_id,
            session_id=session_id,
            patient_id=patient_id,
            series_uid=series_uid,
            volume=volume,
            shape=shape,
            spacing=spacing,
            origin=origin,
        )
        self._rois[label_map_id] = lm
        logger.info(f"Created label map {label_map_id} shape={shape}")
        return label_map_id

    def get_label_map(self, label_map_id: str) -> Optional[LabelMap]:
        return self._rois.get(label_map_id)

    def list_label_maps(self, session_id: str, patient_id: str) -> list[dict]:
        """List metadata for all label maps of a patient."""
        results = []
        for lm in self._rois.values():
            if lm.session_id == session_id and lm.patient_id == patient_id:
                results.append({
                    "id": lm.id,
                    "name": lm.id[:8],
                    "shape": lm.shape,
                    "spacing": lm.spacing,
                    "labels": lm.labels,
                    "created_at": lm.created_at,
                    "updated_at": lm.updated_at,
                })
        return results

    def delete_label_map(self, label_map_id: str) -> bool:
        if label_map_id in self._rois:
            del self._rois[label_map_id]
            return True
        return False

    # ─── Label Management ─────────────────────────────────────────

    def add_label(
        self,
        label_map_id: str,
        label_id: int,
        name: str,
        color: str = "#FF0000",
        opacity: float = 0.4,
    ) -> bool:
        """Add a new label entry to the label map."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        # Remove existing label with same id if present
        lm.labels = [l for l in lm.labels if (l["id"] if isinstance(l, dict) else l.id) != label_id]
        lm.labels.append({
            "id": label_id,
            "name": name,
            "color": color,
            "visible": True,
            "opacity": opacity,
            "locked": False,
        })
        return True

    def remove_label(self, label_map_id: str, label_id: int) -> bool:
        """Remove a label entry and clear its voxels."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        lm.labels = [l for l in lm.labels if (l["id"] if isinstance(l, dict) else l.id) != label_id]
        # Clear voxels for this label
        lm.volume[lm.volume == label_id] = 0
        return True

    def rename_label(self, label_map_id: str, label_id: int, name: str) -> bool:
        """Rename a label."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        for l in lm.labels:
            lid = l["id"] if isinstance(l, dict) else l.id
            if lid == label_id:
                if isinstance(l, dict):
                    l["name"] = name
                else:
                    l.name = name
                return True
        return False

    # ─── Undo / Redo ──────────────────────────────────────────────

    def _push_undo(self, lm: LabelMap) -> None:
        """Compress and push current volume state onto undo stack."""
        raw = lm.volume.tobytes()
        compressed = zlib.compress(raw, level=6)
        lm.undo_stack.append(compressed)
        if len(lm.undo_stack) > MAX_UNDO_DEPTH:
            lm.undo_stack.pop(0)
        lm.redo_stack.clear()

    def undo(self, label_map_id: str) -> bool:
        lm = self.get_label_map(label_map_id)
        if not lm or not lm.undo_stack:
            return False
        # Push current state to redo
        current_compressed = zlib.compress(lm.volume.tobytes(), level=6)
        lm.redo_stack.append(current_compressed)
        # Restore previous state
        compressed = lm.undo_stack.pop()
        raw = zlib.decompress(compressed)
        lm.volume = np.frombuffer(raw, dtype=np.uint8).reshape(lm.shape).copy()
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def redo(self, label_map_id: str) -> bool:
        lm = self.get_label_map(label_map_id)
        if not lm or not lm.redo_stack:
            return False
        current_compressed = zlib.compress(lm.volume.tobytes(), level=6)
        lm.undo_stack.append(current_compressed)
        compressed = lm.redo_stack.pop()
        raw = zlib.decompress(compressed)
        lm.volume = np.frombuffer(raw, dtype=np.uint8).reshape(lm.shape).copy()
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    # ─── Drawing Operations ───────────────────────────────────────

    def paint_stroke(
        self,
        label_map_id: str,
        label: int,
        slice_index: int,
        orientation: str,
        points: list[list[int]],
        radius: int,
    ) -> bool:
        """Paint a brush stroke: points are [[y, x], ...] in slice space."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        axis = ORIENTATION_AXIS.get(orientation)
        if axis is None:
            return False

        slice_shape = self._get_slice_shape(lm, axis)
        for pt in points:
            sy, sx = int(pt[0]), int(pt[1])
            # Build a disk mask around each point
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dy * dy + dx * dx > radius * radius:
                        continue
                    ny, nx = sy + dy, sx + dx
                    if ny < 0 or ny >= slice_shape[0] or nx < 0 or nx >= slice_shape[1]:
                        continue
                    self._set_voxel(lm, axis, slice_index, ny, nx, label)

        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def paint_shape(
        self,
        label_map_id: str,
        label: int,
        slice_index: int,
        orientation: str,
        shape_type: str,
        points: list[list[int]],
    ) -> bool:
        """Fill a shape (polygon, rectangle, ellipse) on a slice."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        axis = ORIENTATION_AXIS.get(orientation)
        if axis is None:
            return False

        slice_shape = self._get_slice_shape(lm, axis)
        mask = np.zeros(slice_shape, dtype=bool)

        if shape_type == "rectangle" and len(points) >= 2:
            y1, x1 = int(points[0][0]), int(points[0][1])
            y2, x2 = int(points[1][0]), int(points[1][1])
            y_min, y_max = max(0, min(y1, y2)), min(slice_shape[0], max(y1, y2) + 1)
            x_min, x_max = max(0, min(x1, x2)), min(slice_shape[1], max(x1, x2) + 1)
            mask[y_min:y_max, x_min:x_max] = True

        elif shape_type == "ellipse" and len(points) >= 2:
            y1, x1 = int(points[0][0]), int(points[0][1])
            y2, x2 = int(points[1][0]), int(points[1][1])
            cy, cx = (y1 + y2) // 2, (x1 + x2) // 2
            ry, rx = max(1, abs(y2 - y1) // 2), max(1, abs(x2 - x1) // 2)
            yy, xx = np.ogrid[:slice_shape[0], :slice_shape[1]]
            mask[((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1] = True

        elif shape_type == "polygon" and len(points) >= 3:
            mask = self._polygon_mask(
                [(int(p[0]), int(p[1])) for p in points], slice_shape
            )

        if mask.any():
            self._apply_mask_to_volume(lm, axis, slice_index, mask, label)

        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def magic_wand(
        self,
        label_map_id: str,
        label: int,
        slice_index: int,
        orientation: str,
        seed_y: int,
        seed_x: int,
        pixel_data: list[list[int]],
        threshold: int = 30,
    ) -> bool:
        """Region-growing magic wand on a 2D pixel slice."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        axis = ORIENTATION_AXIS.get(orientation)
        if axis is None:
            return False

        arr = np.array(pixel_data, dtype=np.float32)
        if seed_y < 0 or seed_y >= arr.shape[0] or seed_x < 0 or seed_x >= arr.shape[1]:
            return False

        # BFS flood fill based on intensity similarity
        visited = np.zeros(arr.shape, dtype=bool)
        mask = np.zeros(arr.shape, dtype=bool)
        seed_val = arr[seed_y, seed_x]

        queue = [(seed_y, seed_x)]
        visited[seed_y, seed_x] = True

        while queue:
            cy, cx = queue.pop()
            if abs(float(arr[cy, cx]) - float(seed_val)) <= threshold:
                mask[cy, cx] = True
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < arr.shape[0] and 0 <= nx < arr.shape[1] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        queue.append((ny, nx))

        if mask.any():
            self._apply_mask_to_volume(lm, axis, slice_index, mask, label)

        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def clear_label(self, label_map_id: str, label: int) -> bool:
        """Remove all voxels of a specific label."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        lm.volume[lm.volume == label] = 0
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    # ─── Morphological Operations ─────────────────────────────────

    def erode(self, label_map_id: str, label: int, iterations: int = 1) -> bool:
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        binary = (lm.volume == label).astype(np.uint8)
        eroded = ndimage.binary_erosion(binary, iterations=iterations).astype(np.uint8)
        # Replace only this label's voxels
        mask = (lm.volume == label) & (eroded == 0)
        lm.volume[mask] = 0
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def dilate(self, label_map_id: str, label: int, iterations: int = 1) -> bool:
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        binary = (lm.volume == label).astype(np.uint8)
        dilated = ndimage.binary_dilation(binary, iterations=iterations).astype(np.uint8)
        # Add new voxels where dilation expanded
        new_voxels = (dilated == 1) & (lm.volume != label)
        lm.volume[new_voxels] = label
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def smooth(self, label_map_id: str, label: int, sigma: float = 1.0) -> bool:
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        binary = (lm.volume == label).astype(np.float32)
        smoothed = ndimage.gaussian_filter(binary, sigma=sigma)
        threshold = 0.3
        new_binary = (smoothed >= threshold).astype(np.uint8)
        # Remove old label voxels not in smoothed result
        remove_mask = (lm.volume == label) & (new_binary == 0)
        lm.volume[remove_mask] = 0
        # Add new label voxels from smoothed result
        add_mask = (new_binary == 1) & (lm.volume == 0)
        lm.volume[add_mask] = label
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    # ─── Slice Mask Retrieval ─────────────────────────────────────

    def get_slice_mask(
        self, label_map_id: str, label: int, slice_index: int, orientation: str
    ) -> Optional[list]:
        """Get binary mask for a single label on a single slice."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return None
        axis = ORIENTATION_AXIS.get(orientation)
        if axis is None:
            return None

        slc = self._make_slice(lm, axis, slice_index)
        mask = (lm.volume[slc] == label).astype(np.uint8)
        return mask.tolist()

    def get_all_masks_on_slice(
        self, label_map_id: str, slice_index: int, orientation: str
    ) -> Optional[dict]:
        """Get all label masks on a single slice: {label_id: mask_data}."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return None
        axis = ORIENTATION_AXIS.get(orientation)
        if axis is None:
            return None

        slc = self._make_slice(lm, axis, slice_index)
        slice_vol = lm.volume[slc]
        result = {}
        for label_entry in lm.labels:
            lid = label_entry["id"] if isinstance(label_entry, dict) else label_entry.id
            mask = (slice_vol == lid).astype(np.uint8)
            if mask.any():
                result[str(lid)] = mask.tolist()
        return result

    # ─── Export ────────────────────────────────────────────────────

    def export_nifti(self, label_map_id: str) -> Optional[io.BytesIO]:
        """Export label map as NIfTI .nii.gz."""
        import tempfile, os
        lm = self.get_label_map(label_map_id)
        if not lm:
            return None

        # nibabel expects (X, Y, Z) — our volume is (Z, Y, X), so transpose
        volume_t = lm.volume.transpose(2, 1, 0)
        full_affine = np.eye(4)
        for i in range(3):
            full_affine[i, i] = lm.spacing[i] if i < len(lm.spacing) else 1.0
        if len(lm.origin) >= 3:
            full_affine[0, 3] = lm.origin[0]
            full_affine[1, 3] = lm.origin[1]
            full_affine[2, 3] = lm.origin[2]

        img = nib.Nifti1Image(volume_t, full_affine)
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            nib.save(img, tmp_path)
            with open(tmp_path, "rb") as f:
                buf = io.BytesIO(f.read())
        finally:
            os.unlink(tmp_path)
        return buf

    def export_dicom_seg(
        self,
        label_map_id: str,
        session_id: str = "",
        patient_name: str = "",
        study_description: str = "",
    ) -> Optional[io.BytesIO]:
        """Export label map as DICOM SEG."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return None

        # Build a minimal DICOM SEG
        file_meta = pydicom.Dataset()
        file_meta.FileMetaInformationGroupLength = 0
        file_meta.FileMetaInformationVersion = b"\x00\x01"
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.66.4"
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

        ds = FileDataset(None, Dataset(), preamble=b"\x00" * 128, file_meta=file_meta)

        # Patient module
        ds.PatientName = patient_name or "Unknown"
        ds.PatientID = lm.patient_id

        # General study module
        ds.StudyInstanceUID = pydicom.uid.generate_uid()
        ds.StudyDate = datetime.now(timezone.utc).strftime("%Y%m%d")
        ds.StudyTime = datetime.now(timezone.utc).strftime("%H%M%S")
        ds.StudyDescription = study_description or "ROI Export"

        # General series module
        ds.Modality = "SEG"
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.SeriesNumber = 1

        # Segmentation series module
        ds.InstanceNumber = 1
        ds.ContentDate = datetime.now(timezone.utc).strftime("%Y%m%d")
        ds.ContentTime = datetime.now(timezone.utc).strftime("%H%M%S")

        # SOP common
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

        # Build segment sequences from labels
        seg_sequence = []
        for label_entry in lm.labels:
            lid = label_entry["id"] if isinstance(label_entry, dict) else label_entry.id
            lname = label_entry["name"] if isinstance(label_entry, dict) else label_entry.name
            seg_item = Dataset()
            seg_item.SegmentNumber = lid
            seg_item.SegmentLabel = lname
            seg_item.SegmentAlgorithmType = "MANUAL"
            seg_sequence.append(seg_item)
        ds.SegmentSequence = DicomSequence(seg_sequence)

        # Spatial options
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.ImagePositionPatient = [float(x) for x in lm.origin[:3]] if len(lm.origin) >= 3 else [0, 0, 0]
        ds.PixelSpacing = [float(x) for x in lm.spacing[1:3]] if len(lm.spacing) >= 3 else [1.0, 1.0]

        # Number of frames
        num_labels = len(lm.labels) if lm.labels else 1
        ds.NumberOfFrames = str(lm.shape[0] * num_labels)

        # Pixel data: pack label map
        if lm.labels:
            # Multi-segment: one set of frames per label
            frames = []
            for label_entry in lm.labels:
                lid = label_entry["id"] if isinstance(label_entry, dict) else label_entry.id
                binary = (lm.volume == lid).astype(np.uint8)
                for z in range(binary.shape[0]):
                    frames.append(binary[z].tobytes())
            pixel_data = b"".join(frames)
        else:
            # Single segment
            frames = []
            for z in range(lm.volume.shape[0]):
                frames.append((lm.volume[z] > 0).astype(np.uint8).tobytes())
            pixel_data = b"".join(frames)

        ds.PixelData = pixel_data

        buf = io.BytesIO()
        pydicom.dcmwrite(buf, ds, write_like_original=False)
        buf.seek(0)
        return buf

    def import_nifti(
        self,
        label_map_id: str,
        nifti_bytes: bytes,
    ) -> bool:
        """Import a NIfTI label map, overwriting the existing volume."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False

        self._push_undo(lm)
        img = nib.load(io.BytesIO(nifti_bytes))
        data = np.asarray(img.dataobj).astype(np.uint8)
        # NIfTI is (X, Y, Z), we store (Z, Y, X)
        volume = data.transpose(2, 1, 0)
        # Resize if shapes don't match
        if volume.shape != tuple(lm.shape):
            from scipy.ndimage import zoom
            factors = [t / s for t, s in zip(lm.shape, volume.shape)]
            volume = zoom(volume, factors, order=0).astype(np.uint8)
        lm.volume = volume
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    # ─── AI Segmentation Integration ──────────────────────────────

    def apply_ai_mask(
        self,
        label_map_id: str,
        label: int,
        mask_volume: np.ndarray,
    ) -> bool:
        """Apply a full 3D mask from AI segmentation to the label map."""
        lm = self.get_label_map(label_map_id)
        if not lm:
            return False
        self._push_undo(lm)
        if mask_volume.shape != tuple(lm.shape):
            from scipy.ndimage import zoom
            factors = [t / s for t, s in zip(lm.shape, mask_volume.shape)]
            mask_volume = zoom(mask_volume, factors, order=0).astype(np.uint8)
        # Set voxels where mask is nonzero
        lm.volume[mask_volume > 0] = label
        lm.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    # ─── Internal Helpers ─────────────────────────────────────────

    def _get_slice_shape(self, lm: LabelMap, axis: int) -> tuple:
        """Get 2D shape of a slice for the given axis."""
        if axis == 0:  # axial: (Y, X)
            return (lm.shape[1], lm.shape[2])
        elif axis == 1:  # coronal: (Z, X)
            return (lm.shape[0], lm.shape[2])
        else:  # sagittal: (Z, Y)
            return (lm.shape[0], lm.shape[1])

    def _make_slice(self, lm: LabelMap, axis: int, slice_index: int):
        """Build numpy index tuple for slicing along axis."""
        if axis == 0:
            si = min(max(0, slice_index), lm.shape[0] - 1)
            return (si, slice(None), slice(None))
        elif axis == 1:
            si = min(max(0, slice_index), lm.shape[1] - 1)
            return (slice(None), si, slice(None))
        else:
            si = min(max(0, slice_index), lm.shape[2] - 1)
            return (slice(None), slice(None), si)

    def _set_voxel(self, lm: LabelMap, axis: int, slice_index: int, y: int, x: int, label: int):
        """Set a single voxel in the volume from 2D slice coordinates."""
        if axis == 0:  # axial
            z = min(max(0, slice_index), lm.shape[0] - 1)
            y = min(max(0, y), lm.shape[1] - 1)
            x = min(max(0, x), lm.shape[2] - 1)
            lm.volume[z, y, x] = label
        elif axis == 1:  # coronal
            z = min(max(0, y), lm.shape[0] - 1)
            sy = min(max(0, slice_index), lm.shape[1] - 1)
            x = min(max(0, x), lm.shape[2] - 1)
            lm.volume[z, sy, x] = label
        else:  # sagittal
            z = min(max(0, y), lm.shape[0] - 1)
            y = min(max(0, x), lm.shape[1] - 1)
            sx = min(max(0, slice_index), lm.shape[2] - 1)
            lm.volume[z, y, sx] = label

    def _apply_mask_to_volume(
        self, lm: LabelMap, axis: int, slice_index: int, mask: np.ndarray, label: int
    ):
        """Apply a 2D boolean mask to the 3D volume along the given axis."""
        if axis == 0:
            z = min(max(0, slice_index), lm.shape[0] - 1)
            y_max, x_max = lm.shape[1], lm.shape[2]
            my = min(mask.shape[0], y_max)
            mx = min(mask.shape[1], x_max)
            lm.volume[z, :my, :mx] = np.where(mask[:my, :mx], label, lm.volume[z, :my, :mx])
        elif axis == 1:
            sy = min(max(0, slice_index), lm.shape[1] - 1)
            z_max, x_max = lm.shape[0], lm.shape[2]
            mz = min(mask.shape[0], z_max)
            mx = min(mask.shape[1], x_max)
            lm.volume[:mz, sy, :mx] = np.where(mask[:mz, :mx], label, lm.volume[:mz, sy, :mx])
        else:
            sx = min(max(0, slice_index), lm.shape[2] - 1)
            z_max, y_max = lm.shape[0], lm.shape[1]
            mz = min(mask.shape[0], z_max)
            my = min(mask.shape[1], y_max)
            lm.volume[:mz, :my, sx] = np.where(mask[:mz, :my], label, lm.volume[:mz, :my, sx])

    def _polygon_mask(self, points: list[tuple[int, int]], shape: tuple) -> np.ndarray:
        """Create a boolean mask from polygon vertices using scanline rasterization."""
        mask = np.zeros(shape, dtype=bool)
        n = len(points)
        if n < 3:
            return mask

        y_min = max(0, min(p[0] for p in points))
        y_max = min(shape[0] - 1, max(p[0] for p in points))

        for y in range(y_min, y_max + 1):
            x_intersections = []
            for i in range(n):
                j = (i + 1) % n
                y1, x1 = points[i]
                y2, x2 = points[j]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    if y2 != y1:
                        x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                        x_intersections.append(x_int)
            x_intersections.sort()
            for k in range(0, len(x_intersections) - 1, 2):
                x_start = max(0, int(x_intersections[k]))
                x_end = min(shape[1] - 1, int(x_intersections[k + 1]))
                if x_start <= x_end:
                    mask[y, x_start:x_end + 1] = True

        return mask


# Singleton
roi_service = ROIService()
