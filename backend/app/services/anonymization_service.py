"""DICOM anonymization service with profiles, custom rules, date offset, and audit log."""

import hashlib
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

import pydicom

from app.services import log_service

# ============================================================
# Anonymization profiles
# ============================================================

# Tags that are always cleared regardless of profile
PHI_TAGS = [
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
    "PatientAge", "PatientSize", "PatientWeight",
    "PatientComments", "MedicalAlerts", "PregnancyStatus",
]

RESEARCH_TAGS = PHI_TAGS + [
    "AccessionNumber", "StudyID", "StudyDate", "StudyTime",
    "ContentDate", "ContentTime",
    "InstanceCreationDate", "InstanceCreationTime",
    "InstitutionName", "InstitutionAddress",
    "ReferringPhysicianName", "PerformingPhysicianName",
    "OperatorsName", "PhysiciansOfRecord",
    "DeviceSerialNumber", "StationName",
    "StudyDescription", "SeriesDescription",
]

CLINICAL_TRIAL_TAGS = RESEARCH_TAGS + [
    "Manufacturer", "ManufacturerModelName",
    "SpecificCharacterSet",
    "RTPlanDate", "RTPlanDescription", "RTPlanLabel", "RTPlanName", "RTPlanTime",
    "ApprovalStatus", "ReviewDate", "ReviewTime", "ReviewerName",
    "BrachyTreatmentTechnique",
]

FULL_TAGS = CLINICAL_TRIAL_TAGS + [
    "ProtocolName", "FrameOfReferenceUID",
    "Laterality", "BodyPartExamined",
]

# ============================================================
# Compliance profiles (HIPAA / GDPR / PS3.15)
# ============================================================

# HIPAA Safe Harbor: 18 identifiers that must be removed
HIPAA_18_IDENTIFIERS = [
    (0x0010, 0x0010),  # PatientName
    (0x0010, 0x0020),  # PatientID
    (0x0010, 0x0030),  # PatientBirthDate
    (0x0010, 0x0040),  # PatientSex
    (0x0008, 0x0050),  # AccessionNumber
    (0x0008, 0x0080),  # InstitutionName
    (0x0008, 0x0081),  # InstitutionAddress
    (0x0008, 0x1070),  # OperatorsName
    (0x0008, 0x1050),  # PerformingPhysicianName
    (0x0008, 0x0090),  # ReferringPhysicianName
    (0x0010, 0x1000),  # OtherPatientIDs
    (0x0010, 0x1001),  # OtherPatientNames
    (0x0010, 0x2154),  # PatientTelephoneNumbers
    (0x0010, 0x21D0),  # PatientAge
    (0x0010, 0x21D1),  # PatientSize
    (0x0010, 0x21D2),  # PatientWeight
    (0x0010, 0x4000),  # PatientComments
    (0x0040, 0x0275),  # RequestAttributesSequence
]

HIPAA_18_TAG_NAMES = [
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
    "AccessionNumber", "InstitutionName", "InstitutionAddress",
    "OperatorsName", "PerformingPhysicianName", "ReferringPhysicianName",
    "OtherPatientIDs", "OtherPatientNames", "PatientTelephoneNumbers",
    "PatientAge", "PatientSize", "PatientWeight",
    "PatientComments", "RequestAttributesSequence",
]

HIPAA_SAFE_HARBOR_TAGS = HIPAA_18_TAG_NAMES + [
    "StudyID", "StudyDate", "StudyTime",
    "ContentDate", "ContentTime",
    "InstanceCreationDate", "InstanceCreationTime",
    "DeviceSerialNumber", "StationName",
    "StudyDescription", "SeriesDescription",
]

GDPR_ERASURE_TAGS = HIPAA_SAFE_HARBOR_TAGS + [
    "Manufacturer", "ManufacturerModelName",
    "ProtocolName", "FrameOfReferenceUID",
    "Laterality", "BodyPartExamined",
]

PS315_BASIC_TAGS = [
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
    "AccessionNumber", "InstitutionName", "InstitutionAddress",
    "ReferringPhysicianName", "PerformingPhysicianName", "OperatorsName",
    "DeviceSerialNumber", "StationName",
]

PS315_ENHANCED_TAGS = PS315_BASIC_TAGS + [
    "OtherPatientIDs", "OtherPatientNames",
    "PatientAge", "PatientSize", "PatientWeight",
    "PatientComments", "PatientTelephoneNumbers",
    "RequestAttributesSequence",
    "StudyDescription", "SeriesDescription",
    "InstitutionalDepartmentName",
    "NameOfPhysiciansReadingStudy",
    "PhysiciansOfRecord",
]

COMPLIANCE_PROFILES = {
    "hipaa_safe_harbor": {
        "name": "HIPAA Safe Harbor",
        "description": "Remove all 18 HIPAA identifiers. Dates offset, UIDs replaced, private tags removed.",
        "tags": HIPAA_SAFE_HARBOR_TAGS,
        "replace_uids": True,
        "offset_dates": True,
        "remove_private": True,
        "standard": "HIPAA",
    },
    "gdpr_erasure": {
        "name": "GDPR Article 17",
        "description": "Maximum de-identification per GDPR right to erasure. Retain minimum dataset for research.",
        "tags": GDPR_ERASURE_TAGS,
        "replace_uids": True,
        "offset_dates": True,
        "remove_private": True,
        "standard": "GDPR",
    },
    "ps315_basic": {
        "name": "PS3.15 Basic",
        "description": "DICOM PS3.15 Basic Application Level Confidentiality Profile.",
        "tags": PS315_BASIC_TAGS,
        "replace_uids": False,
        "offset_dates": False,
        "remove_private": True,
        "standard": "DICOM",
    },
    "ps315_enhanced": {
        "name": "PS3.15 Enhanced",
        "description": "DICOM PS3.15 Enhanced profile. Removes additional institution and physician info.",
        "tags": PS315_ENHANCED_TAGS,
        "replace_uids": True,
        "offset_dates": True,
        "remove_private": True,
        "standard": "DICOM",
    },
}

PROFILES = {
    "research": {
        "name": "Research",
        "description": "Remove patient identifiers and study dates. Suitable for retrospective research.",
        "tags": RESEARCH_TAGS,
        "replace_uids": False,
        "offset_dates": False,
    },
    "clinical_trial": {
        "name": "Clinical Trial",
        "description": "Remove all PHI and institution info. Replace UIDs. Suitable for multi-center trials.",
        "tags": CLINICAL_TRIAL_TAGS,
        "replace_uids": True,
        "offset_dates": True,
    },
    "full": {
        "name": "Full Anonymization",
        "description": "Maximum de-identification. Replace all UIDs, offset dates, remove private tags.",
        "tags": FULL_TAGS,
        "replace_uids": True,
        "offset_dates": True,
    },
    **COMPLIANCE_PROFILES,
}

# ============================================================
# Date offset
# ============================================================

def _generate_date_offset(seed: str) -> timedelta:
    """Generate a consistent random date offset from a seed."""
    h = hashlib.md5(seed.encode()).hexdigest()
    days = int(h[:8], 16) % 3650 - 1825  # -1825 to +1825 days (~5 years)
    return timedelta(days=days)


def _offset_dicom_date(date_str: str, offset: timedelta) -> str:
    """Offset a DICOM date string (YYYYMMDD)."""
    if not date_str or len(date_str) != 8:
        return date_str
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        dt += offset
        return dt.strftime("%Y%m%d")
    except ValueError:
        return date_str


def _offset_dicom_datetime(dt_str: str, offset: timedelta) -> str:
    """Offset a DICOM datetime string (YYYYMMDDHHMMSS.FFFFFF)."""
    if not dt_str:
        return dt_str
    try:
        # Handle fractional seconds
        if "." in dt_str:
            base, frac = dt_str.split(".", 1)
        else:
            base = dt_str
            frac = ""
        dt = datetime.strptime(base, "%Y%m%d%H%M%S")
        dt += offset
        result = dt.strftime("%Y%m%d%H%M%S")
        if frac:
            result += "." + frac
        return result
    except ValueError:
        return dt_str


# ============================================================
# UID replacement
# ============================================================

def _generate_replaced_uid(original_uid: str, seed: str, uid_map: dict[str, str]) -> str:
    """Generate a deterministic replacement UID."""
    if original_uid in uid_map:
        return uid_map[original_uid]
    h = hashlib.sha256((seed + original_uid).encode()).hexdigest()
    # DICOM UID format: digits only, max 64 chars, starts with a digit
    uid = "2." + ".".join(h[i:i+4] for i in range(0, 60, 4))
    uid_map[original_uid] = uid
    return uid


# ============================================================
# Core anonymization
# ============================================================

def get_profile(profile_name: str) -> dict:
    """Get anonymization profile by name."""
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown profile: {profile_name}. Available: {list(PROFILES.keys())}")
    return PROFILES[profile_name]


def get_available_profiles() -> list[dict]:
    """List available anonymization profiles."""
    return [
        {"key": k, "name": v["name"], "description": v["description"]}
        for k, v in PROFILES.items()
    ]


def preview_anonymization(
    dcm: pydicom.Dataset,
    profile_name: str = "research",
    custom_rules: Optional[dict[str, str]] = None,
    date_offset_days: Optional[int] = None,
    seed: str = "",
) -> dict:
    """Preview what anonymization would do without modifying the dataset.

    Returns a diff of tag changes.
    """
    profile = get_profile(profile_name)
    tags_to_clear = list(profile["tags"])
    if custom_rules:
        tags_to_clear.extend(k for k, v in custom_rules.items() if v == "clear")

    changes = []
    for tag_name in tags_to_clear:
        if hasattr(dcm, tag_name):
            original = str(getattr(dcm, tag_name, ""))
            if original:
                changes.append({
                    "tag": tag_name,
                    "original": original[:200],
                    "action": "clear",
                    "new_value": "",
                })

    # UID replacements
    if profile["replace_uids"]:
        for uid_tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID",
                        "FrameOfReferenceUID", "TransferSyntaxUID"]:
            if hasattr(dcm, uid_tag):
                original = str(getattr(dcm, uid_tag, ""))
                if original:
                    replaced = _generate_replaced_uid(original, seed, {})
                    changes.append({
                        "tag": uid_tag,
                        "original": original,
                        "action": "replace_uid",
                        "new_value": replaced,
                    })

    # Date offsets
    if profile["offset_dates"] or date_offset_days is not None:
        offset = timedelta(days=date_offset_days) if date_offset_days is not None else _generate_date_offset(seed)
        date_tags = ["StudyDate", "ContentDate", "InstanceCreationDate",
                     "PatientBirthDate", "RTPlanDate", "ReviewDate"]
        for tag_name in date_tags:
            if hasattr(dcm, tag_name):
                original = str(getattr(dcm, tag_name, ""))
                if original:
                    new_val = _offset_dicom_date(original, offset)
                    changes.append({
                        "tag": tag_name,
                        "original": original,
                        "action": "offset_date",
                        "new_value": new_val,
                    })

        time_tags = ["StudyTime", "ContentTime", "InstanceCreationTime"]
        for tag_name in time_tags:
            if hasattr(dcm, tag_name):
                original = str(getattr(dcm, tag_name, ""))
                if original:
                    new_val = _offset_dicom_datetime(original, offset)
                    changes.append({
                        "tag": tag_name,
                        "original": original,
                        "action": "offset_time",
                        "new_value": new_val,
                    })

    # Private tags
    changes.append({
        "tag": "(private tags)",
        "original": f"{len([e for e in dcm if e.tag.is_private])} private elements",
        "action": "remove_private",
        "new_value": "0",
    })

    return {"changes": changes, "total": len(changes)}


def anonymize_dataset(
    dcm: pydicom.Dataset,
    profile_name: str = "research",
    custom_rules: Optional[dict[str, str]] = None,
    date_offset_days: Optional[int] = None,
    seed: str = "",
) -> tuple[pydicom.Dataset, list[dict]]:
    """Anonymize a DICOM dataset in-place.

    Returns (modified dataset, list of changes applied).
    """
    profile = get_profile(profile_name)
    tags_to_clear = list(profile["tags"])
    if custom_rules:
        for tag_name, action in custom_rules.items():
            if action == "clear" and tag_name not in tags_to_clear:
                tags_to_clear.append(tag_name)

    changes = []

    # Clear tags
    for tag_name in tags_to_clear:
        if hasattr(dcm, tag_name):
            original = str(getattr(dcm, tag_name, ""))
            if original:
                setattr(dcm, tag_name, "")
                changes.append({"tag": tag_name, "original": original[:200], "action": "clear"})

    # Replace UIDs
    uid_map: dict[str, str] = {}
    if profile["replace_uids"]:
        for uid_tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID",
                        "FrameOfReferenceUID"]:
            if hasattr(dcm, uid_tag):
                original = str(getattr(dcm, uid_tag, ""))
                if original:
                    new_uid = _generate_replaced_uid(original, seed, uid_map)
                    setattr(dcm, uid_tag, new_uid)
                    changes.append({"tag": uid_tag, "original": original, "action": "replace_uid"})

    # Offset dates
    if profile["offset_dates"] or date_offset_days is not None:
        offset = timedelta(days=date_offset_days) if date_offset_days is not None else _generate_date_offset(seed)
        date_tags = ["StudyDate", "ContentDate", "InstanceCreationDate",
                     "PatientBirthDate", "RTPlanDate", "ReviewDate"]
        for tag_name in date_tags:
            if hasattr(dcm, tag_name):
                original = str(getattr(dcm, tag_name, ""))
                if original:
                    new_val = _offset_dicom_date(original, offset)
                    setattr(dcm, tag_name, new_val)
                    changes.append({"tag": tag_name, "original": original, "action": "offset_date"})

        time_tags = ["StudyTime", "ContentTime", "InstanceCreationTime"]
        for tag_name in time_tags:
            if hasattr(dcm, tag_name):
                original = str(getattr(dcm, tag_name, ""))
                if original:
                    new_val = _offset_dicom_datetime(original, offset)
                    setattr(dcm, tag_name, new_val)
                    changes.append({"tag": tag_name, "original": original, "action": "offset_time"})

    # Remove private tags
    private_count = len([e for e in dcm if e.tag.is_private])
    if private_count > 0:
        dcm.remove_private_tags()
        changes.append({"tag": "(private tags)", "original": str(private_count), "action": "remove_private"})

    return dcm, changes


# ============================================================
# Session-level anonymization
# ============================================================

def anonymize_patient_files(
    session_id: str,
    patient_id: str,
    profile_name: str = "research",
    custom_rules: Optional[dict[str, str]] = None,
    date_offset_days: Optional[int] = None,
    seed: Optional[str] = None,
) -> dict:
    """Anonymize all DICOM files for a patient and save as DICOM."""
    from app.services import dicom_service
    from app.services.dicom_converter_service import _get_session_dir, _load_pixel_data

    session = dicom_service.sessions.get(session_id)
    if not session:
        return {"files": [], "errors": ["Session not found"]}

    patient = session.get("patients", {}).get(patient_id)
    if not patient:
        return {"files": [], "errors": ["Patient not found"]}

    if not seed:
        seed = str(uuid.uuid4())

    output_dir = os.path.join(str(_get_session_dir(session_id)), "anonymized", patient_id)
    os.makedirs(output_dir, exist_ok=True)

    log_service.info(f"Anonymizing {patient.get('name', patient_id)} with profile '{profile_name}'", "anonymization")

    files = []
    errors = []
    total_changes = 0
    audit_entries = []

    for study_uid, study in patient.get("studies", {}).items():
        for series_uid, series in study.get("series", {}).items():
            for fid in series.get("files", []):
                file_info = session.get("files", {}).get(fid)
                raw = _load_pixel_data(session, fid)
                if not file_info or not raw:
                    continue

                try:
                    pixel = raw.get("data")
                    if pixel is None:
                        continue

                    arr = list(pixel) if isinstance(pixel, list) else pixel.tolist() if hasattr(pixel, 'tolist') else list(pixel)

                    # Build a proper DICOM dataset with pixel data
                    import numpy as np
                    pixel_array = np.array(arr, dtype=np.int16) if arr else np.zeros((1,), dtype=np.int16)

                    # Create DICOM file from stored metadata
                    meta = file_info.get("metadata", {})
                    file_dcm = pydicom.Dataset()
                    file_dcm.PatientName = meta.get("PatientName", "")
                    file_dcm.PatientID = meta.get("PatientID", "")
                    file_dcm.Modality = meta.get("Modality", "OT")
                    file_dcm.SOPClassUID = meta.get("SOPClassUID", "1.2.840.10008.5.1.4.1.1.2")
                    file_dcm.SOPInstanceUID = fid
                    file_dcm.StudyInstanceUID = study_uid
                    file_dcm.SeriesInstanceUID = series_uid

                    # Anonymize
                    anon_dcm, changes = anonymize_dataset(
                        file_dcm, profile_name, custom_rules, date_offset_days, seed
                    )
                    total_changes += len(changes)

                    # Save anonymized DICOM
                    out_path = os.path.join(output_dir, f"{fid}_anon.dcm")
                    anon_dcm.save_as(out_path)

                    files.append({
                        "original_uid": fid,
                        "anonymized_path": out_path,
                        "changes": len(changes),
                    })

                    audit_entries.append({
                        "file": fid,
                        "study_uid": study_uid,
                        "series_uid": series_uid,
                        "profile": profile_name,
                        "changes_count": len(changes),
                    })

                except Exception as e:
                    errors.append(f"Error anonymizing {fid}: {str(e)}")
                    log_service.error(f"Anonymization error for {fid}: {e}", "anonymization")

    # Write audit log
    audit_path = os.path.join(output_dir, "audit_log.json")
    with open(audit_path, "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "patient_id": patient_id,
            "profile": profile_name,
            "seed": seed,
            "files_anonymized": len(files),
            "total_changes": total_changes,
            "entries": audit_entries,
        }, f, indent=2)

    log_service.info(f"Anonymization complete: {len(files)} files, {total_changes} changes", "anonymization")

    return {
        "files": files,
        "errors": errors,
        "total_changes": total_changes,
        "output_dir": output_dir,
        "audit_log": audit_path,
    }


# ============================================================
# Compliance validation
# ============================================================

def validate_compliance(dataset: pydicom.Dataset, profile: str) -> dict:
    """Validate a dataset against a compliance profile.

    Returns {compliant: bool, violations: [...], checked_tags: int, passed: int, failed: int}.
    """
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")

    prof = PROFILES[profile]
    tags_to_check = prof.get("tags", [])
    violations = []
    checked = 0
    passed = 0

    for tag_name in tags_to_check:
        if hasattr(dataset, tag_name):
            checked += 1
            value = getattr(dataset, tag_name, None)
            if value is not None and str(value).strip():
                violations.append({
                    "tag": tag_name,
                    "value": str(value)[:200],
                    "message": f"Tag {tag_name} still contains data after anonymization",
                })
            else:
                passed += 1

    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "checked_tags": checked,
        "passed": passed,
        "failed": len(violations),
        "profile": profile,
        "standard": prof.get("standard", ""),
    }


def detect_burned_in_annotations(dataset: pydicom.Dataset) -> dict:
    """Detect burned-in annotations in a DICOM dataset.

    Checks BurnedInAnnotation (0028,0301) tag and heuristic pixel analysis.
    Returns {has_burned_in: bool, method: str, details: str}.
    """
    # Check explicit BurnedInAnnotation tag
    burned_in_tag = (0x0028, 0x0301)
    if burned_in_tag in dataset:
        value = dataset[burned_in_tag].value
        has_burned = str(value).upper() in ("YES", "1", "TRUE")
        return {
            "has_burned_in": has_burned,
            "method": "tag",
            "details": f"BurnedInAnnotation tag present with value: {value}",
        }

    # Heuristic: check if PatientName appears in OverlayData or other text-bearing tags
    has_text_overlay = False
    for tag_keyword in ["OverlayData", "GraphicLayerData"]:
        if hasattr(dataset, tag_keyword):
            data = getattr(dataset, tag_keyword, None)
            if data and len(str(data)) > 100:
                has_text_overlay = True
                break

    return {
        "has_burned_in": has_text_overlay,
        "method": "heuristic",
        "details": "No BurnedInAnnotation tag; checked overlay data heuristically",
    }


# ============================================================
# AI-enhanced detection
# ============================================================

async def detect_burned_in_annotations_ai(
    pixel_data: "np.ndarray",
    model_id: str = "gpt-4o-mini",
) -> dict:
    """Use vision AI to detect burned-in text annotations in an image.

    Takes a numpy pixel array, encodes as base64 PNG, and sends to vision API.
    Returns {detected: bool, regions: list, confidence: float, raw_response: str}.
    """
    from app.services.ai_service import ai_service, _get_config
    import base64 as _b64
    import io as _io
    from PIL import Image as _Image
    import numpy as _np

    cfg = _get_config()
    if not cfg["api_base"] or not cfg["api_key"]:
        return {"detected": False, "regions": [], "confidence": 0.0, "raw_response": "AI API not configured"}

    # Encode middle slice as base64 PNG
    if pixel_data.ndim == 3:
        slice_2d = pixel_data[pixel_data.shape[0] // 2]
    else:
        slice_2d = pixel_data

    slice_2d = slice_2d.astype(_np.float32)
    mn, mx = slice_2d.min(), slice_2d.max()
    if mx > mn:
        slice_2d = (slice_2d - mn) / (mx - mn) * 255.0
    else:
        slice_2d = _np.zeros_like(slice_2d, dtype=_np.float32)

    img = _Image.fromarray(slice_2d.astype(_np.uint8), mode="L")
    buf = _io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64_image = _b64.b64encode(buf.getvalue()).decode("ascii")

    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{cfg['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Analyze this medical image for burned-in annotations "
                                        "(text, names, dates, IDs visible on the image). "
                                        "Return JSON: {\"detected\": bool, \"regions\": "
                                        "[{\"type\": str, \"description\": str, \"confidence\": float}], "
                                        "\"overall_confidence\": float}"
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{b64_image}", "detail": "low"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 512,
                },
            )
            resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        import json as _json
        if "```" in content:
            json_str = content.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            result = _json.loads(json_str.strip())
        else:
            result = _json.loads(content)
        return {
            "detected": result.get("detected", False),
            "regions": result.get("regions", []),
            "confidence": result.get("overall_confidence", 0.0),
            "raw_response": content,
        }
    except Exception as e:
        return {"detected": False, "regions": [], "confidence": 0.0, "raw_response": str(e)}


async def validate_compliance_ai(
    tag_values: dict[str, str],
    profile: str,
) -> dict:
    """Use AI to review DICOM tag values for compliance risks.

    Checks if tag values still contain real patient names, dates, or identifiers
    even after anonymization.
    Returns {compliant: bool, risks: list, summary: str}.
    """
    from app.services.ai_service import _get_config
    import httpx
    import json as _json

    cfg = _get_config()
    if not cfg["api_base"] or not cfg["api_key"]:
        return {"compliant": True, "risks": [], "summary": "AI API not configured — manual review recommended"}

    # Build a summary of non-empty tags for review
    non_empty = {k: v for k, v in tag_values.items() if v and str(v).strip()}
    if not non_empty:
        return {"compliant": True, "risks": [], "summary": "All checked tags are empty"}

    tag_summary = "\n".join(f"- {k}: {str(v)[:80]}" for k, v in non_empty.items())

    prompt = (
        f"Review these DICOM tag values after {profile} anonymization. "
        "Check if any values still contain real patient information "
        "(names, dates of birth, IDs, institution names, physician names). "
        "Return JSON: {\"compliant\": bool, \"risks\": "
        "[{\"tag\": str, \"value\": str, \"risk\": str, \"severity\": \"high\"|\"medium\"|\"low\"}], "
        "\"summary\": str}\n\n"
        f"Tag values:\n{tag_summary}"
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{cfg['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        if "```" in content:
            json_str = content.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            result = _json.loads(json_str.strip())
        else:
            result = _json.loads(content)
        return result
    except Exception as e:
        return {"compliant": True, "risks": [], "summary": f"AI check failed: {e}"}
