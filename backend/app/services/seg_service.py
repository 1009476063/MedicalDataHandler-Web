"""DICOM SEG (Segmentation) service.

Parses DICOM SEG objects to extract per-segment binary masks.
SEG objects store multi-segment segmentation results with per-frame
functional groups identifying which segment each frame belongs to.
"""

import io
import os
import json
import numpy as np
import pydicom
from pathlib import Path
from typing import Optional
from collections import defaultdict

from app.services.log_service import log_service
from app.utils.cache import LRUCache

UPLOAD_DIR = Path("uploads")
_seg_cache = LRUCache(maxsize=5)


def _get_session(session_id: str) -> Optional[dict]:
    """Get session from dicom_service singleton."""
    from app.services.dicom_service import dicom_service
    return dicom_service.sessions.get(session_id)


def _load_seg_bytes(session_id: str, file_id: str) -> Optional[bytes]:
    """Load raw SEG bytes from disk or in-memory fallback."""
    return dicom_service.load_raw_dicom(session_id, file_id)


def _parse_seg(ds: pydicom.Dataset) -> dict:
    """Parse a DICOM SEG dataset into structured segment info."""
    segments = []
    if not hasattr(ds, "SegmentSequence"):
        return {"segments": [], "frame_count": 0}

    for seg_item in ds.SegmentSequence:
        seg_num = int(getattr(seg_item, "SegmentNumber", 0))
        label = str(getattr(seg_item, "SegmentLabel", f"Segment {seg_num}"))
        algorithm = str(getattr(seg_item, "SegmentAlgorithmType", "MANUAL"))
        # CIELab color (stored as 3 uint16 values)
        color = []
        if hasattr(seg_item, "RecommendedDisplayCIELabValue"):
            color = [int(v) for v in seg_item.RecommendedDisplayCIELabValue]

        segments.append({
            "segment_number": seg_num,
            "label": label,
            "algorithm_type": algorithm,
            "color": color,
        })

    frame_count = int(getattr(ds, "NumberOfFrames", 1))

    return {
        "segments": segments,
        "frame_count": frame_count,
    }


def _extract_segment_mask(
    ds: pydicom.Dataset,
    segment_number: int,
    target_shape: Optional[tuple] = None,
) -> Optional[np.ndarray]:
    """Extract a binary mask for a specific segment number from a SEG dataset.

    Handles both per-frame segment identification and packed-bit pixel data.
    """
    if not hasattr(ds, "pixel_array"):
        return None

    pixel_array = ds.pixel_array
    num_frames = int(getattr(ds, "NumberOfFrames", 1))

    # Determine spatial dimensions
    if pixel_array.ndim == 2:
        # Single frame, single segment
        mask = (pixel_array > 0).astype(np.uint8)
        if target_shape and mask.shape != target_shape:
            mask = _resize_mask(mask, target_shape)
        return mask

    if pixel_array.ndim == 3:
        # Multiple frames or multi-segment single frame
        # Check if we have PerFrameFunctionalGroupsSequence
        has_frame_groups = hasattr(ds, "PerFrameFunctionalGroupsSequence")

        if has_frame_groups and num_frames > 1:
            # Per-frame segment identification
            mask_frames = []
            for frame_idx in range(min(num_frames, len(ds.PerFrameFunctionalGroupsSequence))):
                frame_groups = ds.PerFrameFunctionalGroupsSequence[frame_idx]
                # Check if this frame belongs to our segment
                if hasattr(frame_groups, "FrameContentSequence"):
                    for fc in frame_groups.FrameContentSequence:
                        if hasattr(fc, "SegmentIdentificationSequence"):
                            for sid in fc.SegmentIdentificationSequence:
                                if int(getattr(sid, "ReferencedSegmentNumber", -1)) == segment_number:
                                    frame_mask = (pixel_array[frame_idx] > 0).astype(np.uint8)
                                    mask_frames.append(frame_mask)
                                    break

            if mask_frames:
                return np.stack(mask_frames, axis=0)
            return None

        else:
            # No per-frame info — treat as single segment, all frames belong to it
            mask = (pixel_array > 0).astype(np.uint8)
            if target_shape and mask.shape != target_shape:
                mask = _resize_mask(mask, target_shape)
            return mask

    if pixel_array.ndim == 4:
        # Multi-segment: (frames_per_segment, segments, rows, cols) or similar
        has_frame_groups = hasattr(ds, "PerFrameFunctionalGroupsSequence")

        if has_frame_groups and num_frames > 1:
            mask_frames = []
            for frame_idx in range(min(num_frames, len(ds.PerFrameFunctionalGroupsSequence))):
                frame_groups = ds.PerFrameFunctionalGroupsSequence[frame_idx]
                if hasattr(frame_groups, "FrameContentSequence"):
                    for fc in frame_groups.FrameContentSequence:
                        if hasattr(fc, "SegmentIdentificationSequence"):
                            for sid in fc.SegmentIdentificationSequence:
                                if int(getattr(sid, "ReferencedSegmentNumber", -1)) == segment_number:
                                    # pixel_array[frame_idx] could be multi-channel
                                    frame_data = pixel_array[frame_idx]
                                    if frame_data.ndim > 2:
                                        frame_data = frame_data[..., 0]
                                    frame_mask = (frame_data > 0).astype(np.uint8)
                                    mask_frames.append(frame_mask)
                                    break

            if mask_frames:
                return np.stack(mask_frames, axis=0)
            return None

        # No per-frame info, try to index by segment
        if pixel_array.shape[1] <= segment_number:
            return None
        mask = (pixel_array[:, segment_number - 1] > 0).astype(np.uint8)
        if target_shape and mask.shape != target_shape:
            mask = _resize_mask(mask, target_shape)
        return mask

    return None


def _resize_mask(mask: np.ndarray, target_shape: tuple) -> np.ndarray:
    """Resize a mask to target shape using nearest-neighbor interpolation."""
    from scipy.ndimage import zoom
    factors = [t / s for t, s in zip(target_shape, mask.shape)]
    resized = zoom(mask, factors, order=0)
    return (resized > 0).astype(np.uint8)


def list_segments(session_id: str, patient_id: str) -> list[dict]:
    """List all SEG objects and their segments for a patient."""
    session = _get_session(session_id)
    if not session:
        return []

    results = []
    for fid, finfo in session.get("files", {}).items():
        if finfo.get("patient_id") != patient_id:
            continue
        if finfo.get("modality") != "SEG":
            continue

        raw_bytes = _load_seg_bytes(session_id, fid)
        if not raw_bytes:
            continue

        try:
            cache_key = f"{session_id}_{fid}"
            ds = _seg_cache.get(cache_key)
            if ds is None:
                ds = pydicom.dcmread(io.BytesIO(raw_bytes), force=True)
                _seg_cache.put(cache_key, ds)
            seg_info = _parse_seg(ds)
            results.append({
                "file_id": fid,
                "filename": finfo.get("filename", fid),
                "series_uid": finfo.get("series_uid", ""),
                "segments": seg_info["segments"],
                "frame_count": seg_info["frame_count"],
                "description": finfo.get("metadata", {}).get("SeriesDescription", ""),
            })
        except Exception as e:
            log_service.warning(f"Failed to parse SEG {fid}: {e}", "seg")

    return results


def get_segment_mask(
    session_id: str,
    file_id: str,
    segment_number: int,
) -> Optional[dict]:
    """Get binary mask data for a specific segment.

    Returns the mask as a nested list (for JSON serialization) along with
    spatial metadata needed for overlay rendering.
    """
    raw_bytes = _load_seg_bytes(session_id, file_id)
    if not raw_bytes:
        return None

    try:
        cache_key = f"{session_id}_{file_id}"
        ds = _seg_cache.get(cache_key)
        if ds is None:
            ds = pydicom.dcmread(io.BytesIO(raw_bytes), force=True)
            _seg_cache.put(cache_key, ds)
    except Exception as e:
        log_service.warning(f"Failed to read SEG {file_id}: {e}", "seg")
        return None

    mask = _extract_segment_mask(ds, segment_number)
    if mask is None:
        return None

    # Get spatial metadata from the referenced series
    origin = [0.0, 0.0, 0.0]
    spacing = [1.0, 1.0, 1.0]
    if hasattr(ds, "ImagePositionPatient"):
        origin = [float(v) for v in ds.ImagePositionPatient]
    if hasattr(ds, "PixelSpacing"):
        spacing = [float(v) for v in ds.PixelSpacing]
        if hasattr(ds, "SpacingBetweenSlices"):
            spacing.append(float(ds.SpacingBetweenSlices))

    return {
        "segment_number": segment_number,
        "shape": list(mask.shape),
        "origin": origin,
        "spacing": spacing,
        "data": mask.tolist(),
    }


def get_segment_volume(
    session_id: str,
    patient_id: str,
    segment_number: Optional[int] = None,
) -> Optional[dict]:
    """Build a 3D volume from all segments (or a specific one) across all SEG files.

    Returns binary masks indexed by segment number with spatial alignment info.
    """
    session = _get_session(session_id)
    if not session:
        return None

    # Find all SEG files for this patient
    seg_files = []
    for fid, finfo in session.get("files", {}).items():
        if finfo.get("patient_id") == patient_id and finfo.get("modality") == "SEG":
            seg_files.append(fid)

    if not seg_files:
        return None

    all_segments = {}
    for fid in seg_files:
        raw_bytes = _load_seg_bytes(session_id, fid)
        if not raw_bytes:
            continue

        try:
            cache_key = f"{session_id}_{fid}"
            ds = _seg_cache.get(cache_key)
            if ds is None:
                ds = pydicom.dcmread(io.BytesIO(raw_bytes), force=True)
                _seg_cache.put(cache_key, ds)
            seg_info = _parse_seg(ds)

            for seg in seg_info["segments"]:
                seg_num = seg["segment_number"]
                if segment_number is not None and seg_num != segment_number:
                    continue

                mask = _extract_segment_mask(ds, seg_num)
                if mask is not None:
                    all_segments[seg_num] = {
                        "label": seg["label"],
                        "color": seg["color"],
                        "shape": list(mask.shape),
                        "data": mask.tolist(),
                    }
        except Exception as e:
            log_service.warning(f"Failed to process SEG volume {fid}: {e}", "seg")

    if not all_segments:
        return None

    return {
        "segments": all_segments,
        "segment_count": len(all_segments),
    }


def detect_seg_in_session(session_id: str, patient_id: str) -> bool:
    """Check if a patient has any SEG files."""
    session = _get_session(session_id)
    if not session:
        return False
    for fid, finfo in session.get("files", {}).items():
        if finfo.get("patient_id") == patient_id and finfo.get("modality") == "SEG":
            return True
    return False
