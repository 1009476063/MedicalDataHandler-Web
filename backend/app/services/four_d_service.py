"""4D dynamic sequence support — groups DICOM slices by temporal position."""
from typing import Optional
from collections import defaultdict
import numpy as np


def _get_session(session_id: str) -> Optional[dict]:
    from app.services.dicom_service import dicom_service
    return dicom_service.sessions.get(session_id)


def _load_pixel(session_id: str, file_id: str) -> Optional[dict]:
    session = _get_session(session_id)
    if not session:
        return None
    raw = session.get("raw_data", {}).get(file_id)
    if not raw:
        return None
    if "data_path" in raw and raw["data_path"]:
        try:
            pixel_array = np.load(raw["data_path"])
            return {**raw, "data": pixel_array}
        except Exception:
            return None
    return raw


def detect_temporal_positions(session_id: str, patient_id: str, series_uid: str) -> Optional[dict]:
    """Detect temporal positions in a series and return time point metadata."""
    session = _get_session(session_id)
    if not session:
        return None

    # Collect files for this series with temporal position info
    time_groups: dict[int, list[str]] = defaultdict(list)
    has_temporal = False

    for fid, finfo in session["files"].items():
        if finfo.get("patient_id") != patient_id:
            continue
        if finfo.get("series_uid") != series_uid:
            continue
        if finfo.get("modality") not in ("CT", "MR", "PT", "NM", "OT"):
            continue

        temporal_pos = finfo.get("temporal_position", 1)
        if finfo.get("has_temporal", False):
            has_temporal = True
        time_groups[temporal_pos].append(fid)

    if not has_temporal:
        return None

    time_points = []
    for pos in sorted(time_groups.keys()):
        fids = time_groups[pos]
        # Get spacing/shape from first file
        first_raw = _load_pixel(session_id, fids[0])
        shape = list(first_raw["data"].shape) if first_raw and "data" in first_raw else [0, 0]
        time_points.append({
            "position": pos,
            "file_count": len(fids),
            "shape": shape,
        })

    return {
        "is_4d": True,
        "time_point_count": len(time_points),
        "time_points": time_points,
    }


def get_4d_volume(
    session_id: str, patient_id: str, series_uid: str,
    time_point: Optional[int] = None,
) -> Optional[dict]:
    """Return volume for a specific time point (or all time points)."""
    session = _get_session(session_id)
    if not session:
        return None

    # Group files by temporal position
    time_groups: dict[int, list[tuple[str, dict]]] = defaultdict(list)

    for fid, finfo in session["files"].items():
        if finfo.get("patient_id") != patient_id:
            continue
        if finfo.get("series_uid") != series_uid:
            continue
        if finfo.get("modality") not in ("CT", "MR", "PT", "NM", "OT"):
            continue

        raw = _load_pixel(session_id, fid)
        if raw and "data" in raw:
            pos = finfo.get("temporal_position", 1)
            time_groups[pos].append((fid, raw))

    if not time_groups:
        return None

    # Sort each time group by slice location
    for pos in time_groups:
        time_groups[pos].sort(
            key=lambda x: x[1].get("slice_location", x[1].get("instance_number", 0))
        )

    if time_point is not None:
        # Single time point
        if time_point not in time_groups:
            return None
        groups_to_build = {time_point: time_groups[time_point]}
    else:
        groups_to_build = time_groups

    results = {}
    for pos, slices_data in groups_to_build.items():
        pixel_data = np.stack([s[1]["data"] for s in slices_data], axis=0)

        if len(slices_data) > 1:
            spacing_z = float(abs(
                slices_data[1][1].get("slice_location", 0)
                - slices_data[0][1].get("slice_location", 0)
            ))
        else:
            spacing_z = 1.0
        spacing_y = float(slices_data[0][1]["spacing"][0])
        spacing_x = float(slices_data[0][1]["spacing"][1])

        raw_origin = slices_data[0][1].get("position", [0.0, 0.0, 0.0])
        if hasattr(raw_origin, 'tolist'):
            origin = [float(x) for x in raw_origin.tolist()]
        elif isinstance(raw_origin, (list, tuple)):
            origin = [float(x) for x in raw_origin]
        else:
            origin = [0.0, 0.0, 0.0]

        results[pos] = {
            "array": pixel_data,
            "shape": list(pixel_data.shape),
            "spacing": [spacing_z, spacing_y, spacing_x],
            "origin": origin,
            "dtype": str(pixel_data.dtype),
            "min": float(pixel_data.min()),
            "max": float(pixel_data.max()),
            "mean": float(pixel_data.mean()),
        }

    return results
