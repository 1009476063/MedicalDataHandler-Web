from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import numpy as np
import io
import json
import asyncio
from pathlib import Path

from app.services.dicom_service import dicom_service
from app.services.image_builder import ImageBuilder

router = APIRouter()
image_builder = ImageBuilder()

CONFIG_DIR = Path(__file__).parent.parent.parent / "config_files"


def _load_extended_hu_red_table():
    """Load extended HU-to-RED calibration data from config files (450+ points)."""
    hu_file = CONFIG_DIR / "ct_HU_map_vals.json"
    red_file = CONFIG_DIR / "ct_RED_map_vals.json"
    if hu_file.exists() and red_file.exists():
        with open(hu_file) as f:
            hu_vals = json.load(f)
        with open(red_file) as f:
            red_vals = json.load(f)
        if len(hu_vals) == len(red_vals) and len(hu_vals) > 35:
            return list(zip(hu_vals, red_vals))
    # Fallback to built-in 35-point table
    return [
        (-1000, 0.000), (-950, 0.050), (-900, 0.100), (-850, 0.150),
        (-800, 0.200), (-750, 0.250), (-700, 0.300), (-650, 0.350),
        (-600, 0.400), (-550, 0.450), (-500, 0.500), (-450, 0.550),
        (-400, 0.600), (-350, 0.650), (-300, 0.700), (-250, 0.750),
        (-200, 0.800), (-150, 0.850), (-100, 0.900), (-50, 0.950),
        (0, 1.000), (50, 1.050), (100, 1.100), (150, 1.150),
        (200, 1.200), (300, 1.300), (400, 1.400), (500, 1.500),
        (600, 1.600), (700, 1.700), (800, 1.800), (900, 1.900),
        (1000, 2.000), (1500, 2.500), (2000, 3.000), (3000, 4.000),
    ]


HU_TO_RED_TABLE = _load_extended_hu_red_table()


def _build_hu_red_interpolator():
    """Build scipy interp1d interpolator for HU-to-RED conversion."""
    try:
        from scipy.interpolate import interp1d
        hu_vals = np.array([p[0] for p in HU_TO_RED_TABLE], dtype=np.float64)
        red_vals = np.array([p[1] for p in HU_TO_RED_TABLE], dtype=np.float64)
        return interp1d(hu_vals, red_vals, kind='linear', fill_value=(red_vals[0], red_vals[-1]), bounds_error=False)
    except ImportError:
        return None


_hu_red_interp = _build_hu_red_interpolator()

# TG-263 structure name mapping (common structure names to standard names)
TG263_NAMES = {
    # Organs at risk
    "brainstem": "Brainstem",
    "brain_stem": "Brainstem",
    "spinal_cord": "SpinalCord",
    "spinalcord": "SpinalCord",
    "cord": "SpinalCord",
    "left_eye": "Eye_L",
    "right_eye": "Eye_R",
    "left_lens": "Lens_L",
    "right_lens": "Lens_R",
    "left_optic_nerve": "OpticNerve_L",
    "right_optic_nerve": "OpticNerve_R",
    "left_optic_chiasm": "OpticChiasm_L",
    "right_optic_chiasm": "OpticChiasm_R",
    "optic_chiasm": "OpticChiasm",
    "left_parotid": "Parotid_L",
    "right_parotid": "Parotid_R",
    "left_submandibular": "Submandibular_L",
    "right_submandibular": "Submandibular_R",
    "left_cochlea": "Cochlea_L",
    "right_cochlea": "Cochlea_R",
    "larynx": "Larynx",
    "pharynx": "Pharynx",
    "esophagus": "Esophagus",
    "trachea": "Trachea",
    "heart": "Heart",
    "lungs": "Lungs",
    "left_lung": "Lung_L",
    "right_lung": "Lung_R",
    "liver": "Liver",
    "kidney_left": "Kidney_L",
    "kidney_right": "Kidney_R",
    "kidneys": "Kidneys",
    "stomach": "Stomach",
    "bowel": "Bowel",
    "small_bowel": "SmallBowel",
    "large_bowel": "LargeBowel",
    "rectum": "Rectum",
    "bladder": "Bladder",
    "femoral_head_left": "FemoralHead_L",
    "femoral_head_right": "FemoralHead_R",
    "femoral_heads": "FemoralHeads",
    "brain": "Brain",
    "mandible": "Mandible",
    "globe_left": "Globe_L",
    "globe_right": "Globe_R",
    "lacrimal_left": "Lacrimal_L",
    "lacrimal_right": "Lacrimal_R",
    "temporal_lobe_left": "TemporalLobe_L",
    "temporal_lobe_right": "TemporalLobe_R",
    "hippocampus_left": "Hippocampus_L",
    "hippocampus_right": "Hippocampus_R",
    # Target volumes
    "gtv": "GTV",
    "ctv": "CTV",
    "ptv": "PTV",
    "tv": "TV",
    "itv": "ITV",
    # External
    "body": "External",
    "external": "External",
    "patient": "External",
    "skin": "External",
}


class ConvertHURequest(BaseModel):
    session_id: str
    patient_id: str
    series_uid: str
    conversion_type: str = "red"  # "red" for HU-to-RED


class RenameStructRequest(BaseModel):
    session_id: str
    patient_id: str
    struct_key: str
    new_name: str


class SumDoseRequest(BaseModel):
    session_id: str
    patient_id: str
    dose_file_ids: list[str]


def interpolate_hu_to_red(hu_value: float) -> float:
    """Convert HU value to Relative Electron Density using interpolation."""
    if _hu_red_interp is not None:
        return float(_hu_red_interp(hu_value))
    # Fallback to manual linear interpolation
    if hu_value <= HU_TO_RED_TABLE[0][0]:
        return HU_TO_RED_TABLE[0][1]
    if hu_value >= HU_TO_RED_TABLE[-1][0]:
        return HU_TO_RED_TABLE[-1][1]
    for i in range(len(HU_TO_RED_TABLE) - 1):
        hu1, red1 = HU_TO_RED_TABLE[i]
        hu2, red2 = HU_TO_RED_TABLE[i + 1]
        if hu1 <= hu_value <= hu2:
            t = (hu_value - hu1) / (hu2 - hu1)
            return red1 + t * (red2 - red1)
    return 1.0


def vectorized_hu_to_red(volume: np.ndarray) -> np.ndarray:
    """Vectorized HU-to-RED conversion for entire volume."""
    if _hu_red_interp is not None:
        return _hu_red_interp(volume).astype(np.float32)
    return np.vectorize(interpolate_hu_to_red)(volume).astype(np.float32)


def _convert_hu_sync(req: ConvertHURequest) -> io.BytesIO:
    volume_info = image_builder.get_volume(req.session_id, req.patient_id, req.series_uid)
    if volume_info is None:
        raise HTTPException(status_code=404, detail="Volume not found")
    red_volume = vectorized_hu_to_red(volume_info["array"])
    nrrd_header = (
        f"NRRD0004\n"
        f"type: float\n"
        f"dimension: 3\n"
        f"sizes: {red_volume.shape[2]} {red_volume.shape[1]} {red_volume.shape[0]}\n"
        f"encoding: raw\n"
        f"endian: little\n"
        f"space directions: (1,0,0) (0,1,0) (0,0,1)\n"
        f"space origin: (0,0,0)\n"
        f"\n"
    )
    output = io.BytesIO()
    output.write(nrrd_header.encode())
    output.write(red_volume.astype(np.float32).tobytes())
    output.seek(0)
    return output


@router.post("/convert-hu")
async def convert_hu_to_red(req: ConvertHURequest):
    """Convert CT HU values to Relative Electron Density (RED)."""
    try:
        output = await asyncio.to_thread(_convert_hu_sync, req)
        return StreamingResponse(
            output,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=RED_{req.series_uid[:8]}.nrrd"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename-struct")
async def rename_struct(req: RenameStructRequest):
    """Rename a structure using TG-263 naming conventions."""
    try:
        result = dicom_service.rename_struct(
            req.session_id, req.patient_id, req.struct_key, req.new_name
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Structure not found")
        return {"success": True, "new_name": req.new_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-rename-structs")
async def auto_rename_structs(session_id: str, patient_id: str):
    """Automatically rename all structures using TG-263 naming conventions."""
    try:
        structs = dicom_service.get_structs(session_id, patient_id)
        if not structs:
            return {"renamed": 0, "structures": []}

        renamed = []
        for struct in structs:
            original_name = struct.get("name", "").lower().strip()
            if original_name in TG263_NAMES:
                new_name = TG263_NAMES[original_name]
                dicom_service.rename_struct(session_id, patient_id, struct["key"], new_name)
                renamed.append({"key": struct["key"], "old_name": struct["name"], "new_name": new_name})

        return {"renamed": len(renamed), "structures": renamed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tg263-names")
async def get_tg263_names():
    """Get the TG-263 structure name mapping."""
    return {"names": TG263_NAMES}


def _sum_doses_sync(req: SumDoseRequest) -> io.BytesIO:
    base_info = image_builder.get_volume(req.session_id, req.patient_id, req.dose_file_ids[0])
    if base_info is None:
        raise HTTPException(status_code=404, detail="Dose not found")
    summed = base_info["array"].copy()
    for dose_id in req.dose_file_ids[1:]:
        dose_info = image_builder.get_volume(req.session_id, req.patient_id, dose_id)
        if dose_info is not None and dose_info["array"].shape == summed.shape:
            summed += dose_info["array"]
    nrrd_header = (
        f"NRRD0004\n"
        f"type: float\n"
        f"dimension: 3\n"
        f"sizes: {summed.shape[2]} {summed.shape[1]} {summed.shape[0]}\n"
        f"encoding: raw\n"
        f"endian: little\n"
        f"space directions: (1,0,0) (0,1,0) (0,0,1)\n"
        f"space origin: (0,0,0)\n"
        f"\n"
    )
    output = io.BytesIO()
    output.write(nrrd_header.encode())
    output.write(summed.astype(np.float32).tobytes())
    output.seek(0)
    return output


@router.post("/sum-doses")
async def sum_doses(req: SumDoseRequest):
    """Sum multiple dose distributions."""
    try:
        if len(req.dose_file_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 dose files required")
        output = await asyncio.to_thread(_sum_doses_sync, req)
        return StreamingResponse(
            output,
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=summed_dose.nrrd"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
