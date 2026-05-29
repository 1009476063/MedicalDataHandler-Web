from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import json
import csv
import io

router = APIRouter()

# In-memory annotation store per session
_annotations: dict[str, list[dict]] = {}


class AnnotationItem(BaseModel):
    uid: str
    tool_name: str
    label: str = ""
    stats: dict = {}


class AnnotationBatch(BaseModel):
    session_id: str
    series_uid: str
    annotations: list[AnnotationItem]


@router.post("/api/annotations/save")
async def save_annotations(batch: AnnotationBatch):
    key = f"{batch.session_id}:{batch.series_uid}"
    _annotations[key] = [a.model_dump() for a in batch.annotations]
    return {"status": "ok", "count": len(batch.annotations)}


@router.get("/api/annotations/{session_id}/{series_uid}")
async def load_annotations(session_id: str, series_uid: str):
    key = f"{session_id}:{series_uid}"
    return _annotations.get(key, [])


@router.get("/api/annotations/{session_id}/{series_uid}/export")
async def export_annotations_csv(session_id: str, series_uid: str):
    key = f"{session_id}:{series_uid}"
    items = _annotations.get(key, [])
    if not items:
        raise HTTPException(status_code=404, detail="No annotations found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tool", "Label", "Value", "Unit"])
    for item in items:
        tool = item.get("tool_name", "")
        label = item.get("label", "")
        stats = item.get("stats", {})
        value, unit = "", ""
        if tool == "Length" and "length" in stats:
            value = f"{stats['length']:.2f}"
            unit = "mm"
        elif tool == "Angle" and "angle" in stats:
            value = f"{stats['angle']:.1f}"
            unit = "deg"
        elif tool in ("RectangleROI", "EllipticalROI") and "mean" in stats:
            value = f"{stats['mean']:.1f}"
            unit = "HU"
        elif tool == "Probe" and "value" in stats:
            value = f"{stats['value']:.1f}"
            unit = "HU"
        writer.writerow([tool, label, value, unit])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=annotations_{series_uid}.csv"},
    )
