"""DICOM sequence analysis and smart selection service.

Ports the core analysis logic from select_sequences.py to work with
the web app's session structure (in-memory metadata, not disk files).
"""

from collections import defaultdict
from typing import Optional


def _get_tag(file_info: dict, tag_name: str, default=None):
    """Get a tag value from metadata, with all_tags fallback."""
    meta = file_info.get("metadata", {})
    val = meta.get(tag_name)
    if val is not None:
        return val
    # Fallback: search all_tags by keyword name
    for _hex, tag_data in file_info.get("all_tags", {}).items():
        if tag_data.get("name") == tag_name:
            return tag_data.get("value")
    return default


def _collect_series_metadata(session: dict, patient_id: str) -> dict:
    """Collect per-file metadata for all series of a patient.

    Returns: {series_uid: {series_info: {...}, files_info: [...]}}
    """
    patient = session["patients"].get(patient_id, {})
    series_map = {}

    for study_uid, study in patient.get("studies", {}).items():
        for series_uid, series in study.get("series", {}).items():
            files_info = []
            for fid in series.get("files", []):
                fi = session["files"].get(fid)
                if fi:
                    files_info.append(fi)
            if files_info:
                series_map[series_uid] = {
                    "series_info": series,
                    "files_info": files_info,
                }

    return series_map


def identify_sequence_type(files_info_list: list[dict]) -> dict:
    """Identify sequence type from file metadata.

    Returns: {type: str, confidence: float, reason: str}
    """
    if not files_info_list:
        return {"type": "OTHER", "confidence": 0, "reason": "No files"}

    first = files_info_list[0]
    desc = _get_tag(first, "SeriesDescription", "N/A")
    desc_lower = desc.lower()

    # Collect diffusion b-values
    b_values = set()
    for fi in files_info_list:
        bv = _get_tag(fi, "DiffusionBValue")
        if bv is not None:
            try:
                b_values.add(float(bv))
            except (ValueError, TypeError):
                pass

    # Exclude DKI
    if "dki" in desc_lower:
        return {"type": "OTHER", "confidence": 0.1, "reason": "DKI sequence, not standard DWI"}

    # DWI: has DiffusionBValue with values
    if len(b_values) > 1 or (len(b_values) == 1 and list(b_values)[0] > 0):
        return {
            "type": "DWI",
            "confidence": 0.9,
            "reason": f"DiffusionBValue detected: {sorted(b_values)}",
        }

    # ADC: ImageType contains ADC
    image_type_raw = _get_tag(first, "ImageType", "")
    if isinstance(image_type_raw, list):
        image_types = [str(t).upper() for t in image_type_raw]
    else:
        image_types = [str(image_type_raw).upper()]

    if "ADC" in image_types:
        return {"type": "ADC", "confidence": 0.95, "reason": "ADC in ImageType"}

    # DWI fallback: description keywords
    if any(kw in desc_lower for kw in ["dwi", "reveal", "trace", "diff"]) and "adc" not in desc_lower:
        return {"type": "DWI", "confidence": 0.7, "reason": "Description contains DWI keywords"}

    # ADC fallback: description keyword
    if "adc" in desc_lower:
        return {"type": "ADC", "confidence": 0.7, "reason": "ADC in description"}

    # DCE: multi-indicator approach
    dce_indicators = []

    # TemporalPositionIdentifier
    temporal_positions = set()
    for fi in files_info_list:
        tp = _get_tag(fi, "TemporalPositionIdentifier")
        if tp is not None:
            try:
                temporal_positions.add(int(tp))
            except (ValueError, TypeError):
                pass

    num_files = len(files_info_list)
    slices_per_phase = num_files // len(temporal_positions) if len(temporal_positions) > 1 else num_files

    if len(temporal_positions) > 1:
        if slices_per_phase >= 5 and num_files >= 30:
            dce_indicators.append(f"TemporalPositionIdentifier: {len(temporal_positions)} phases")

    # ContrastBolusAgent
    contrast = _get_tag(first, "ContrastBolusAgent")
    if contrast:
        dce_indicators.append(f"ContrastBolusAgent: {contrast}")

    # Description keywords
    dce_keywords = ["dce", "dynamic", "dyn", "views", "ssdy", "sdyn", "ethrive", "enhance"]
    has_keyword = any(kw in desc_lower for kw in dce_keywords)
    if has_keyword:
        dce_indicators.append(f"Description contains DCE keyword")

    if not has_keyword:
        if len(temporal_positions) > 1 and slices_per_phase >= 10 and num_files >= 50:
            dce_indicators.append("Multi-phase sequence (no DCE keyword)")
        else:
            return {"type": "OTHER", "confidence": 0.1, "reason": "No DCE indicators"}

    # ScanningSequence
    scanning_seq = _get_tag(first, "ScanningSequence")
    if scanning_seq:
        if isinstance(scanning_seq, list):
            sq_list = scanning_seq
        else:
            sq_list = [scanning_seq]
        if any(s in ["GR", "SE"] for s in sq_list):
            dce_indicators.append(f"ScanningSequence: {sq_list}")

    if dce_indicators:
        confidence = min(0.5 + 0.1 * len(dce_indicators), 0.95)
        return {"type": "DCE", "confidence": confidence, "reason": "; ".join(dce_indicators)}

    return {"type": "OTHER", "confidence": 0.1, "reason": "No specific indicators"}


def analyze_dce_phases(files_info_list: list[dict]) -> dict:
    """Analyze DCE temporal phases.

    Returns: {num_phases, slices_per_phase, method}
    """
    # Sort by InstanceNumber
    def _inst_num(fi):
        v = _get_tag(fi, "InstanceNumber")
        try:
            return int(v) if v else 0
        except (ValueError, TypeError):
            return 0

    sorted_files = sorted(files_info_list, key=_inst_num)

    # Try TemporalPositionIdentifier grouping
    phases = defaultdict(list)
    has_temporal = False
    for i, fi in enumerate(sorted_files):
        tp = _get_tag(fi, "TemporalPositionIdentifier")
        if tp is not None:
            has_temporal = True
            try:
                phases[int(tp)].append(i)
            except (ValueError, TypeError):
                pass

    if has_temporal and len(phases) > 1:
        first_key = list(phases.keys())[0]
        return {
            "num_phases": len(phases),
            "slices_per_phase": len(phases[first_key]),
            "method": "TemporalPositionIdentifier",
        }

    # Fallback: AcquisitionTime grouping
    time_groups = defaultdict(list)
    for i, fi in enumerate(sorted_files):
        t = _get_tag(fi, "AcquisitionTime")
        if t:
            time_groups[str(t)].append(i)

    if len(time_groups) > 1:
        sorted_times = sorted(time_groups.keys())
        phases = {i + 1: time_groups[t] for i, t in enumerate(sorted_times)}
        first_phase = list(phases.values())[0] if phases else []
        return {
            "num_phases": len(phases),
            "slices_per_phase": len(first_phase),
            "method": "AcquisitionTime",
        }

    return {
        "num_phases": 1,
        "slices_per_phase": len(sorted_files),
        "method": "default_single_phase",
    }


def analyze_dwi_bvalues(files_info_list: list[dict]) -> Optional[dict]:
    """Analyze DWI b-value distribution via SliceLocation grouping.

    Returns: {num_bvalues, num_slices, total_files, method} or None
    """
    slice_groups = defaultdict(list)
    for i, fi in enumerate(files_info_list):
        sl = _get_tag(fi, "SliceLocation")
        if sl is not None:
            try:
                slice_groups[round(float(sl), 2)].append(i)
            except (ValueError, TypeError):
                pass

    if not slice_groups:
        return None

    counts = [len(v) for v in slice_groups.values()]
    if counts:
        num_bvalues = max(set(counts), key=counts.count)
        return {
            "num_bvalues": num_bvalues,
            "num_slices": len(slice_groups),
            "total_files": len(files_info_list),
            "method": "SliceLocation_groups",
        }
    return None


def _first_geometry(files_info: list[dict]):
    """Extract geometry (Rows, Cols, PixelSpacing) from first file."""
    for fi in files_info or []:
        if not fi:
            continue
        rows = _get_tag(fi, "Rows")
        cols = _get_tag(fi, "Columns")
        ps = _get_tag(fi, "PixelSpacing")
        if rows and cols and ps:
            try:
                ps_val = ps if isinstance(ps, list) else [ps]
                ps_key = (float(ps_val[0]), float(ps_val[1]))
                return int(rows), int(cols), ps_key
            except (ValueError, TypeError, IndexError):
                pass
    return None, None, None


def _geometry_score(dwi_item: dict, adc_geom: tuple) -> int:
    """Score geometry match between DWI and ADC."""
    if not adc_geom:
        return 0
    adc_rows, adc_cols, adc_ps = adc_geom
    dwi_rows, dwi_cols, dwi_ps = _first_geometry(dwi_item.get("files_info", []))
    score = 0
    if adc_rows and dwi_rows and adc_rows == dwi_rows:
        score += 1
    if adc_cols and dwi_cols and adc_cols == dwi_cols:
        score += 1
    if adc_ps and dwi_ps and abs(adc_ps[0] - dwi_ps[0]) < 1e-3 and abs(adc_ps[1] - dwi_ps[1]) < 1e-3:
        score += 1
    return score


def _representative_bvalue(files_info: list[dict]):
    """Get the most common b-value from files."""
    counts = {}
    for fi in files_info or []:
        b = _get_tag(fi, "DiffusionBValue")
        if b is None:
            continue
        try:
            v = float(b)
            counts[v] = counts.get(v, 0) + 1
        except (ValueError, TypeError):
            continue
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _select_best_adc(candidates: list[dict]) -> Optional[dict]:
    """Pick ADC with most files."""
    if not candidates:
        return None
    return max(candidates, key=lambda x: x["file_count"])


def _select_best_dwi(dwi_candidates: list[dict], adc_ref: Optional[dict]) -> Optional[list | dict]:
    """Select best DWI series, possibly a list for dual b-value."""
    if not dwi_candidates:
        return None

    adc_files = adc_ref["file_count"] if adc_ref else 0
    adc_geom = _first_geometry(adc_ref.get("files_info", [])) if adc_ref else None

    # Exclude registration DWI
    dwi_non_reg = [d for d in dwi_candidates if "REG" not in d.get("description", "").upper()]
    dwi_pool = dwi_non_reg if dwi_non_reg else dwi_candidates

    # Geometry matching
    if adc_geom and dwi_pool:
        scored = sorted(dwi_pool, key=lambda d: (_geometry_score(d, adc_geom), d["file_count"]), reverse=True)
        best_score = _geometry_score(scored[0], adc_geom)
        if best_score > 0:
            dwi_pool = [d for d in scored if _geometry_score(d, adc_geom) == best_score]

    # 1) Double b-value DWI (file_count == ADC * 2)
    if adc_files > 0:
        expected = adc_files * 2
        for d in dwi_pool:
            if d["file_count"] == expected:
                dwi_analysis = d.get("dwi_analysis") or {}
                if dwi_analysis.get("num_bvalues", 0) == 2:
                    return d

    # 1.5) Dual b-value split into two Series
    if adc_files > 0:
        dwi_single_series = []
        for d in dwi_pool:
            if d["file_count"] != adc_files:
                continue
            dwi_analysis = d.get("dwi_analysis") or {}
            if dwi_analysis.get("num_bvalues", 0) != 1:
                continue
            d["_rep_bvalue"] = _representative_bvalue(d.get("files_info", []))
            dwi_single_series.append(d)

        if len(dwi_single_series) >= 2:
            b0 = [d for d in dwi_single_series if d.get("_rep_bvalue") == 0]
            nonzero = [d for d in dwi_single_series if d.get("_rep_bvalue") not in (None, 0)]
            if b0 and nonzero:
                d1 = b0[0]
                d2 = max(nonzero, key=lambda x: x.get("_rep_bvalue", 0))
                return [d1, d2]
            return sorted(dwi_single_series, key=lambda x: x["series_number"])[:2]

    # 2) Single b-value DWI (file_count == ADC)
    if adc_files > 0:
        dwi_single_bvalue = [d for d in dwi_pool if d["file_count"] == adc_files]
        if dwi_single_bvalue:
            return dwi_single_bvalue[0]

        # Same count fallback
        dwi_same_count = [d for d in dwi_pool if d["file_count"] == adc_files]
        if dwi_same_count:
            return dwi_same_count[0]

        # Closest count
        if dwi_pool:
            return min(dwi_pool, key=lambda x: abs(x["file_count"] - adc_files))

    # No ADC reference: pick by file count
    return max(dwi_pool, key=lambda x: x["file_count"]) if dwi_pool else None


def _select_best_dce(dce_candidates: list[dict]) -> list[dict]:
    """Select DCE candidates, excluding post-processing series."""
    exclude_keywords = ["_WI", "_WO", "_SUB", "_TTP", "_MIP", "_PEI", "SUB", "MIP"]
    dce_raw = [
        d for d in dce_candidates
        if not any(kw.upper() in d["description"].upper() for kw in exclude_keywords)
        and d["file_count"] >= 10
    ]
    return dce_raw


def _select_best_mg(mg_candidates: list[dict]) -> list[dict]:
    """Select MG series: only RCC/LCC/RMLO/LMLO views."""
    wanted = ["RCC", "LCC", "RMLO", "LMLO"]

    def _mg_view_key(item):
        lat = (_get_tag(item, "ImageLaterality") or "").upper()
        vp = (_get_tag(item, "ViewPosition") or "").upper()
        if lat in ["R", "L"] and vp:
            return f"{lat}{vp}"
        desc_u = (item.get("description") or "").upper()
        for k in wanted:
            if k in desc_u:
                return k
        return None

    best_by_view = {}
    for c in mg_candidates:
        k = _mg_view_key(c)
        if k not in wanted:
            continue
        prev = best_by_view.get(k)
        if prev is None or c.get("file_count", 0) > prev.get("file_count", 0):
            best_by_view[k] = c

    return [best_by_view[k] for k in wanted if k in best_by_view]


def analyze_patient_sequences(session: dict, patient_id: str) -> dict:
    """Main orchestrator: analyze all series and select best for each type.

    Returns:
        {
            all_series: [...],     # All series with classification
            selected: {ADC, DWI, DCE, MG, US},
            reasons: {type: str},
        }
    """
    series_map = _collect_series_metadata(session, patient_id)

    adc_candidates = []
    dwi_candidates = []
    dce_candidates = []
    mg_candidates = []
    us_candidates = []
    all_series = []

    for series_uid, data in series_map.items():
        series_info = data["series_info"]
        files_info = data["files_info"]
        desc = series_info.get("description", "N/A")
        modality = str(series_info.get("modality", "MR")).upper()
        file_count = series_info.get("file_count", len(files_info))
        series_number = series_info.get("series_number", 0)

        entry_base = {
            "series_uid": series_uid,
            "series_number": series_number,
            "description": desc,
            "modality": modality,
            "file_count": file_count,
        }

        # MG/US: skip MR analysis, collect by modality
        if modality in ["US"]:
            us_candidates.append({**entry_base, "files_info": files_info})
            all_series.append({**entry_base, "type": "US", "confidence": 1.0, "reason": f"Modality={modality}"})
            continue

        if modality in ["MG", "DX", "CR"]:
            mg_candidates.append({**entry_base, "files_info": files_info})
            all_series.append({**entry_base, "type": "MG", "confidence": 1.0, "reason": f"Modality={modality}"})
            continue

        # MR sequence classification
        result = identify_sequence_type(files_info)
        seq_type = result["type"]
        confidence = result["confidence"]
        reason = result["reason"]

        series_entry = {**entry_base, "type": seq_type, "confidence": confidence, "reason": reason}

        if confidence < 0.5:
            all_series.append(series_entry)
            continue

        if seq_type == "ADC":
            adc_candidates.append({**entry_base, "files_info": files_info, "identification_reason": reason})
            series_entry["candidate_for"] = "ADC"
        elif seq_type == "DWI":
            dwi_analysis = analyze_dwi_bvalues(files_info)
            dwi_candidates.append({**entry_base, "files_info": files_info, "dwi_analysis": dwi_analysis, "identification_reason": reason})
            series_entry["candidate_for"] = "DWI"
            if dwi_analysis:
                series_entry["dwi_info"] = f"{dwi_analysis['num_bvalues']} b-values x {dwi_analysis['num_slices']} slices"
        elif seq_type == "DCE":
            dce_analysis = analyze_dce_phases(files_info)
            dce_candidates.append({**entry_base, "files_info": files_info, "dce_analysis": dce_analysis, "identification_reason": reason})
            series_entry["candidate_for"] = "DCE"
            if dce_analysis:
                series_entry["dce_info"] = f"{dce_analysis['num_phases']} phases x {dce_analysis['slices_per_phase']} slices"

        all_series.append(series_entry)

    # Selection logic
    selected = {}
    reasons = {}

    # ADC
    best_adc = _select_best_adc(adc_candidates)
    if best_adc:
        selected["ADC"] = best_adc
        reasons["ADC"] = f"Most files ({best_adc['file_count']})"

    # DWI
    best_dwi = _select_best_dwi(dwi_candidates, best_adc)
    if best_dwi:
        selected["DWI"] = best_dwi
        if isinstance(best_dwi, list):
            bvals = [d.get("_rep_bvalue") for d in best_dwi]
            reasons["DWI"] = f"Dual b-value split: {len(best_dwi)} series, b-values={bvals}"
        else:
            dwi_a = best_dwi.get("dwi_analysis") or {}
            bv = dwi_a.get("num_bvalues", "?")
            sl = dwi_a.get("num_slices", best_dwi["file_count"])
            reasons["DWI"] = f"{best_dwi['file_count']} files ({bv} b-values x {sl} slices)"

    # DCE
    dce_raw = _select_best_dce(dce_candidates)
    selected["DCE"] = dce_raw
    reasons["DCE"] = f"{len(dce_raw)} DCE candidates" if dce_raw else "No DCE candidates"

    # MG
    mg_sel = _select_best_mg(mg_candidates)
    selected["MG"] = mg_sel
    reasons["MG"] = f"{len(mg_sel)} MG series selected" if mg_sel else "No MG series"

    # US
    selected["US"] = sorted(us_candidates, key=lambda x: x.get("series_number", 0))
    reasons["US"] = f"{len(selected['US'])} US series" if selected["US"] else "No US series"

    # Serialize selected for JSON response
    def _serialize_series(item):
        if item is None:
            return None
        if isinstance(item, list):
            return [_serialize_series(i) for i in item]
        return {
            "series_uid": item.get("series_uid"),
            "series_number": item.get("series_number"),
            "description": item.get("description"),
            "modality": item.get("modality"),
            "file_count": item.get("file_count"),
            "identification_reason": item.get("identification_reason"),
            "dwi_analysis": item.get("dwi_analysis"),
            "dce_analysis": item.get("dce_analysis"),
            "dwi_info": item.get("dwi_info"),
            "dce_info": item.get("dce_info"),
            "candidate_for": item.get("candidate_for"),
        }

    return {
        "all_series": all_series,
        "selected": {k: _serialize_series(v) for k, v in selected.items()},
        "reasons": reasons,
    }
