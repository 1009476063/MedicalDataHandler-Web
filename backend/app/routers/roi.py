"""ROI (Region of Interest) router.

Endpoints for creating, editing, and exporting label maps
used for manual and AI-assisted ROI delineation.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.response import ApiResponse
from app.services import roi_service

router = APIRouter()


# ─── Request Models ──────────────────────────────────────────

class CreateLabelMapRequest(BaseModel):
    session_id: str
    patient_id: str
    series_uid: str
    shape: list[int]
    spacing: list[float]
    origin: list[float]
    name: str = ""


class AddLabelRequest(BaseModel):
    label_map_id: str
    id: int
    name: str
    color: str = "#FF0000"
    opacity: float = 0.4


class RemoveLabelRequest(BaseModel):
    label_map_id: str
    label_id: int


class RenameLabelRequest(BaseModel):
    label_map_id: str
    label_id: int
    name: str


class PaintRequest(BaseModel):
    label_map_id: str
    label: int
    slice_index: int
    orientation: str  # axial | coronal | sagittal
    points: list[list[float]]  # [[y, x], ...]
    radius: int = 3


class ShapeRequest(BaseModel):
    label_map_id: str
    label: int
    slice_index: int
    orientation: str
    shape_type: str  # polygon | rectangle | ellipse
    points: list[list[float]]


class MagicWandRequest(BaseModel):
    label_map_id: str
    label: int
    slice_index: int
    orientation: str
    seed_x: int
    seed_y: int
    pixel_data: list[list[float]]  # 2D slice pixel data
    threshold: float = 10.0


class ClearLabelRequest(BaseModel):
    label_map_id: str
    label_id: int


class MorphRequest(BaseModel):
    label_map_id: str
    label: int
    iterations: int = 1


class SmoothRequest(BaseModel):
    label_map_id: str
    label: int
    sigma: float = 1.0


class SliceMaskRequest(BaseModel):
    label_map_id: str
    label: int
    slice_index: int
    orientation: str


class SliceAllRequest(BaseModel):
    label_map_id: str
    slice_index: int
    orientation: str


class UndoRedoRequest(BaseModel):
    label_map_id: str


class ExportNiftiRequest(BaseModel):
    label_map_id: str


class ExportDicomSegRequest(BaseModel):
    label_map_id: str
    session_id: str = ""
    patient_name: str = ""
    study_description: str = ""


class ImportNiftiRequest(BaseModel):
    label_map_id: str


# ─── CRUD Endpoints ──────────────────────────────────────────

@router.post("/create")
async def create_label_map(req: CreateLabelMapRequest):
    """Create an empty label map for a patient/series."""
    label_map_id = await asyncio.to_thread(
        roi_service.create_label_map,
        req.session_id, req.patient_id, req.series_uid,
        req.shape, req.spacing, req.origin, req.name,
    )
    return ApiResponse(success=True, data={"id": label_map_id})


@router.get("/list/{session_id}/{patient_id}")
async def list_label_maps(session_id: str, patient_id: str):
    """List all label maps for a patient."""
    items = await asyncio.to_thread(
        roi_service.list_label_maps, session_id, patient_id,
    )
    return ApiResponse(success=True, data={"label_maps": items, "count": len(items)})


@router.get("/{label_map_id}")
async def get_label_map(label_map_id: str):
    """Get label map metadata."""
    lm = await asyncio.to_thread(roi_service.get_label_map, label_map_id)
    if not lm:
        raise HTTPException(status_code=404, detail="Label map not found")
    data = {
        "id": lm.id,
        "name": lm.id[:8],
        "session_id": lm.session_id,
        "patient_id": lm.patient_id,
        "series_uid": lm.series_uid,
        "shape": lm.shape,
        "spacing": lm.spacing,
        "origin": lm.origin,
        "labels": lm.labels,
        "created_at": lm.created_at,
        "updated_at": lm.updated_at,
    }
    return ApiResponse(success=True, data=data)


@router.delete("/{label_map_id}")
async def delete_label_map(label_map_id: str):
    """Delete a label map."""
    ok = await asyncio.to_thread(roi_service.delete_label_map, label_map_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Label map not found")
    return ApiResponse(success=True)


# ─── Label Management ────────────────────────────────────────

@router.post("/add-label")
async def add_label(req: AddLabelRequest):
    """Add a new label to the label map."""
    ok = await asyncio.to_thread(
        roi_service.add_label,
        req.label_map_id, req.id, req.name, req.color, req.opacity,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Label map not found")
    return ApiResponse(success=True)


@router.post("/remove-label")
async def remove_label(req: RemoveLabelRequest):
    """Remove a label from the label map."""
    ok = await asyncio.to_thread(
        roi_service.remove_label, req.label_map_id, req.label_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Label map or label not found")
    return ApiResponse(success=True)


@router.post("/rename-label")
async def rename_label(req: RenameLabelRequest):
    """Rename a label."""
    ok = await asyncio.to_thread(
        roi_service.rename_label, req.label_map_id, req.label_id, req.name,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Label map or label not found")
    return ApiResponse(success=True)


# ─── Drawing Operations ──────────────────────────────────────

@router.post("/paint")
async def paint_stroke(req: PaintRequest):
    """Apply a brush stroke (batch of points) to the label map."""
    ok = await asyncio.to_thread(
        roi_service.paint_stroke,
        req.label_map_id, req.label, req.slice_index,
        req.orientation, req.points, req.radius,
    )
    return ApiResponse(success=True, data={"painted": ok})


@router.post("/shape")
async def paint_shape(req: ShapeRequest):
    """Fill a shape (polygon, rectangle, ellipse) on the label map."""
    ok = await asyncio.to_thread(
        roi_service.paint_shape,
        req.label_map_id, req.label, req.slice_index,
        req.orientation, req.shape_type, req.points,
    )
    return ApiResponse(success=True, data={"filled": ok})


@router.post("/magic-wand")
async def magic_wand(req: MagicWandRequest):
    """Magic wand region-growing fill."""
    import numpy as np
    pixel_data = np.array(req.pixel_data, dtype=np.float64)
    ok = await asyncio.to_thread(
        roi_service.magic_wand,
        req.label_map_id, req.label, req.slice_index,
        req.orientation, req.seed_x, req.seed_y,
        pixel_data, req.threshold,
    )
    return ApiResponse(success=True, data={"filled": ok})


@router.post("/clear-label")
async def clear_label(req: ClearLabelRequest):
    """Remove all voxels for a specific label."""
    ok = await asyncio.to_thread(
        roi_service.clear_label, req.label_map_id, req.label_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Label map not found")
    return ApiResponse(success=True)


# ─── Morphological Operations ────────────────────────────────

@router.post("/erode")
async def erode(req: MorphRequest):
    """Erode a label mask."""
    ok = await asyncio.to_thread(
        roi_service.erode, req.label_map_id, req.label, req.iterations,
    )
    return ApiResponse(success=True, data={"eroded": ok})


@router.post("/dilate")
async def dilate(req: MorphRequest):
    """Dilate a label mask."""
    ok = await asyncio.to_thread(
        roi_service.dilate, req.label_map_id, req.label, req.iterations,
    )
    return ApiResponse(success=True, data={"dilated": ok})


@router.post("/smooth")
async def smooth(req: SmoothRequest):
    """Gaussian smooth a label mask."""
    ok = await asyncio.to_thread(
        roi_service.smooth, req.label_map_id, req.label, req.sigma,
    )
    return ApiResponse(success=True, data={"smoothed": ok})


# ─── Slice Queries ───────────────────────────────────────────

@router.post("/slice-mask")
async def get_slice_mask(req: SliceMaskRequest):
    """Get binary mask for a single label on a single slice."""
    mask = await asyncio.to_thread(
        roi_service.get_slice_mask,
        req.label_map_id, req.label, req.slice_index, req.orientation,
    )
    if mask is None:
        raise HTTPException(status_code=404, detail="Label map not found")
    return ApiResponse(success=True, data={"mask": mask})


@router.post("/slice-all")
async def get_all_masks_on_slice(req: SliceAllRequest):
    """Get all label masks on a single slice."""
    masks = await asyncio.to_thread(
        roi_service.get_all_masks_on_slice,
        req.label_map_id, req.slice_index, req.orientation,
    )
    if masks is None:
        raise HTTPException(status_code=404, detail="Label map not found")
    return ApiResponse(success=True, data={"masks": masks})


# ─── Undo / Redo ─────────────────────────────────────────────

@router.post("/undo")
async def undo(req: UndoRedoRequest):
    """Undo the last drawing operation."""
    ok = await asyncio.to_thread(roi_service.undo, req.label_map_id)
    return ApiResponse(success=True, data={"undone": ok})


@router.post("/redo")
async def redo(req: UndoRedoRequest):
    """Redo the last undone operation."""
    ok = await asyncio.to_thread(roi_service.redo, req.label_map_id)
    return ApiResponse(success=True, data={"redone": ok})


# ─── Import / Export ─────────────────────────────────────────

@router.post("/export/nifti")
async def export_nifti(req: ExportNiftiRequest):
    """Export label map as NIfTI (.nii.gz)."""
    buf = await asyncio.to_thread(roi_service.export_nifti, req.label_map_id)
    if not buf:
        raise HTTPException(status_code=404, detail="Label map not found")
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/gzip",
        headers={"Content-Disposition": "attachment; filename=label_map.nii.gz"},
    )


@router.post("/export/dicom-seg")
async def export_dicom_seg(req: ExportDicomSegRequest):
    """Export label map as DICOM SEG."""
    buf = await asyncio.to_thread(
        roi_service.export_dicom_seg,
        req.label_map_id, req.session_id, req.patient_name, req.study_description,
    )
    if not buf:
        raise HTTPException(status_code=404, detail="Label map not found")
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/dicom",
        headers={"Content-Disposition": "attachment; filename=segmentation.dcm"},
    )


@router.post("/import/nifti")
async def import_nifti(req: ImportNiftiRequest, nifti_bytes: bytes):
    """Import a NIfTI label map (multipart form upload)."""
    ok = await asyncio.to_thread(
        roi_service.import_nifti, req.label_map_id, nifti_bytes,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Label map not found or import failed")
    return ApiResponse(success=True)
