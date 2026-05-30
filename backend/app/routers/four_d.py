"""4D dynamic sequence endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from app.models.response import ApiResponse

router = APIRouter()


class FourDVolumeRequest(BaseModel):
    session_id: str
    patient_id: str
    series_uid: str
    time_point: Optional[int] = None


@router.get("/info/{session_id}/{patient_id}/{series_uid}")
async def get_4d_info(session_id: str, patient_id: str, series_uid: str):
    """Detect temporal positions in a series and return time point metadata."""
    from app.services.four_d_service import detect_temporal_positions
    result = await asyncio.to_thread(
        detect_temporal_positions, session_id, patient_id, series_uid,
    )
    if result is None:
        return ApiResponse(success=True, data={"is_4d": False, "time_point_count": 0, "time_points": []})
    return ApiResponse(success=True, data=result)


@router.post("/volume")
async def get_4d_volume(req: FourDVolumeRequest):
    """Return volume data for a specific time point."""
    from app.services.four_d_service import get_4d_volume
    result = await asyncio.to_thread(
        get_4d_volume, req.session_id, req.patient_id, req.series_uid, req.time_point,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No 4D data found")

    # Serialize numpy arrays
    volumes = {}
    for pos, vol in result.items():
        arr = vol["array"]
        volumes[str(pos)] = {
            "data": arr.tolist(),
            "shape": vol["shape"],
            "spacing": vol["spacing"],
            "origin": vol["origin"],
            "dtype": vol["dtype"],
            "min": vol["min"],
            "max": vol["max"],
            "mean": vol["mean"],
        }
    return ApiResponse(success=True, data={"volumes": volumes})
