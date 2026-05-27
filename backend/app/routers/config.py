from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json

router = APIRouter()
CONFIG_DIR = Path(__file__).parent.parent.parent / "config_files"
CONFIG_DIR.mkdir(exist_ok=True)


DEFAULT_TG263 = {
    "name": "TG-263 Structure Names",
    "description": "Standardized structure naming conventions from AAPM TG-263",
    "rules": {
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
        "optic_chiasm": "OpticChiasm",
        "left_parotid": "Parotid_L",
        "right_parotid": "Parotid_R",
        "left_submandibular": "Submandibular_L",
        "right_submandibular": "Submandibular_R",
        "larynx": "Larynx",
        "pharynx": "Pharynx",
        "esophagus": "Esophagus",
        "trachea": "Trachea",
        "heart": "Heart",
        "left_lung": "Lung_L",
        "right_lung": "Lung_R",
        "liver": "Liver",
        "kidney_left": "Kidney_L",
        "kidney_right": "Kidney_R",
        "stomach": "Stomach",
        "bowel": "Bowel",
        "small_bowel": "SmallBowel",
        "large_bowel": "LargeBowel",
        "rectum": "Rectum",
        "bladder": "Bladder",
        "femoral_head_left": "FemoralHead_L",
        "femoral_head_right": "FemoralHead_R",
        "brain": "Brain",
        "mandible": "Mandible",
        "gtv": "GTV",
        "ctv": "CTV",
        "ptv": "PTV",
        "itv": "ITV",
        "body": "External",
        "external": "External",
        "skin": "External",
    },
}

DEFAULT_ORGAN_MATCHING = {
    "name": "Organ Matching Rules",
    "description": "Rules for matching DICOM structure names to standard organ names",
    "rules": {
        "brain": ["Brain", "brain", "BRAIN"],
        "brainstem": ["Brainstem", "brain_stem", "Brain_Stem", "BRAINSTEM"],
        "spinal_cord": ["SpinalCord", "spinal_cord", "Spinal_Cord", "CORD"],
        "eyes": ["Eye_L", "Eye_R", "eye_left", "eye_right", "Globe_L", "Globe_R"],
        "lenses": ["Lens_L", "Lens_R", "lens_left", "lens_right"],
        "optic_nerves": ["OpticNerve_L", "OpticNerve_R", "optic_nerve_L", "optic_nerve_R"],
        "optic_chiasm": ["OpticChiasm", "optic_chiasm", "Optic_Chiasm"],
        "parotids": ["Parotid_L", "Parotid_R", "parotid_left", "parotid_right"],
        "submandibulars": ["Submandibular_L", "Submandibular_R"],
        "larynx": ["Larynx", "larynx", "LARYNX"],
        "pharynx": ["Pharynx", "pharynx"],
        "esophagus": ["Esophagus", "esophagus", "ESOPHAGUS"],
        "trachea": ["Trachea", "trachea", "TRACHEA"],
        "heart": ["Heart", "heart", "HEART", "Heart_Avg"],
        "lungs": ["Lung_L", "Lung_R", "left_lung", "right_lung", "LUNGS"],
        "liver": ["Liver", "liver", "LIVER"],
        "kidneys": ["Kidney_L", "Kidney_R", "kidney_left", "kidney_right"],
        "stomach": ["Stomach", "stomach", "STOMACH"],
        "bowel": ["Bowel", "bowel", "BOWEL", "SmallBowel", "LargeBowel"],
        "rectum": ["Rectum", "rectum", "RECTUM"],
        "bladder": ["Bladder", "bladder", "BLADDER"],
        "femoral_heads": ["FemoralHead_L", "FemoralHead_R", "femoral_head_L", "femoral_head_R"],
        "target_volumes": ["GTV", "CTV", "PTV", "ITV", "TV"],
        "external": ["External", "external", "Body", "body", "Skin", "skin"],
    },
}

DEFAULT_WINDOW_PRESETS = {
    "Custom": [375, 40],
    "Brain: General": [80, 40],
    "Brain: Subdural": [200, 75],
    "Brain: Stroke": [8, 32],
    "Bone: Option 1": [1800, 400],
    "Bone: Option 2": [2800, 600],
    "Bone: Option 3": [4000, 700],
    "Soft Tissue: Option 1": [250, 50],
    "Soft Tissue: Option 2": [350, 20],
    "Soft Tissue: Option 3": [400, 60],
    "Soft Tissue: Option 4": [375, 40],
    "Lung": [1500, -600],
    "Liver": [150, 30],
}

DEFAULT_DISEASE_SITES = [
    "ABDOMEN", "ADRENAL", "BLADDER", "BONE", "BRAIN", "BREAST", "CHESTWALL", "CSI",
    "ESOPHAGUS", "GI", "GU", "GYN", "HEART", "HN", "KIDNEY", "LIVER", "LUNG",
    "LYMPHOMA", "MEDIASTINUM", "PANCREAS", "PELVIS", "PROSTATE", "RECTAL",
    "SARCOMA", "SKIN", "SPINE", "TBI",
]

DEFAULT_MACHINE_NAMES = [
    "Varian-21EX", "Varian-VitalBeam", "Varian-TrueBeam", "Elekta-Agility",
    "Elekta-Versa", "Elekta-Unity", "Varian-Ethos", "Varian-Halcyon",
    "Accuray-CyberKnife", "Elekta-GammaKnife", "Xcision-GammaPod", "RefleXion-X1",
]

DEFAULT_USER_CONFIG = {
    "json_objective_filename": "objectives.json",
    "unmatched_organ_name": "!UNKNOWN!",
    "screen_size": [2064, 1152],
    "font_scale": 1.0,
    "orientation_label_color": [255, 0, 0, 255],
    "pan_speed": 0.02,
    "voxel_spacing": [3.0, 3.0, 3.0],
    "use_config_voxel_spacing": True,
    "zoom_factor": 0.1,
    "screen_size_input_mode": "Percentage",
    "font": "Inter_18pt-Medium",
    "force_voxel_spacing_isotropic_largest": False,
    "force_voxel_spacing_isotropic_smallest": False,
}

DEFAULTS = {
    "tg263": DEFAULT_TG263,
    "organ_matching": DEFAULT_ORGAN_MATCHING,
    "window_presets": {"name": "Window Presets", "description": "CT window/level presets", "rules": DEFAULT_WINDOW_PRESETS},
    "disease_sites": {"name": "Disease Sites", "description": "Treatment disease sites", "rules": DEFAULT_DISEASE_SITES},
    "machine_names": {"name": "Machine Names", "description": "Treatment machine names", "rules": DEFAULT_MACHINE_NAMES},
    "user_config": {"name": "User Configuration", "description": "Runtime user preferences", "rules": DEFAULT_USER_CONFIG},
}


def _normalize_name(name: str) -> str:
    """Convert URL-style hyphens to filesystem-style underscores."""
    return name.replace("-", "_")


def _load_config(name: str) -> dict:
    config_file = CONFIG_DIR / f"{_normalize_name(name)}.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                data = json.load(f)
            if data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def _save_config(name: str, data: dict):
    config_file = CONFIG_DIR / f"{_normalize_name(name)}.json"
    with open(config_file, "w") as f:
        json.dump(data, f, indent=2)


@router.get("/")
async def list_configs():
    configs = [f.stem for f in CONFIG_DIR.glob("*.json")]
    return {"configs": configs}


@router.get("/{config_name}")
async def get_config(config_name: str):
    normalized = _normalize_name(config_name)
    data = _load_config(config_name)
    if not data:
        if normalized in DEFAULTS:
            return DEFAULTS[normalized]
        raise HTTPException(status_code=404, detail="Config not found")
    # Normalize: wrap flat data in standard {name, description, rules} format
    if "rules" not in data and normalized in DEFAULTS:
        default = DEFAULTS[normalized]
        data = {"name": default.get("name", normalized), "description": default.get("description", ""), "rules": data}
    return data


class UpdateConfigRequest(BaseModel):
    rules: dict


@router.put("/{config_name}")
async def update_config(config_name: str, req: UpdateConfigRequest):
    normalized = _normalize_name(config_name)
    data = _load_config(config_name)
    if not data:
        if normalized in DEFAULTS:
            data = DEFAULTS[normalized].copy()
        else:
            data = {"name": normalized, "description": "", "rules": {}}
    # Normalize: ensure standard wrapper exists
    if "rules" not in data:
        default = DEFAULTS.get(normalized, {})
        data = {"name": default.get("name", normalized), "description": default.get("description", ""), "rules": data}

    data["rules"] = req.rules
    _save_config(config_name, data)
    return {"success": True, "config_name": config_name}


@router.post("/{config_name}/reset")
async def reset_config(config_name: str):
    normalized = _normalize_name(config_name)
    if normalized in DEFAULTS:
        _save_config(config_name, DEFAULTS[normalized])
        return {"success": True, "config": DEFAULTS[normalized]}
    raise HTTPException(status_code=404, detail="No default config for this name")
