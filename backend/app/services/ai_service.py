"""AI analysis service — calls OpenAI-compatible vision API for medical image analysis."""

import asyncio
import base64
import io
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Common organ HU ranges (approximate, for text-guided segmentation)
_HU_RANGES: dict[str, tuple[float, float]] = {
    "A_Aorta": (-100, 400),
    "Heart": (-100, 400),
    "Lung_L": (-1000, -200),
    "Lung_R": (-1000, -200),
    "Liver": (-20, 180),
    "Kidney_L": (-20, 200),
    "Kidney_R": (-20, 200),
    "Spleen": (-20, 200),
    "Pancreas": (-20, 200),
    "Spinal_Cord": (20, 80),
    "Brain": (20, 80),
    "Bone": (200, 3000),
    "Fat": (-200, -50),
    "Muscle": (-100, 200),
    "GTV": (-20, 400),
    "CTV": (-20, 400),
    "PTV": (-20, 400),
}

# ---------------------------------------------------------------------------
# Configuration — env vars as defaults, overridable via config file
# ---------------------------------------------------------------------------
AI_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ai_config.json")

AI_API_BASE = os.getenv("AI_API_BASE", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_DEFAULT_MODEL = os.getenv("AI_DEFAULT_MODEL", "")


def _load_config_file() -> dict:
    """Load persisted AI config from disk (if any)."""
    try:
        if os.path.exists(AI_CONFIG_PATH):
            with open(AI_CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_config_file(data: dict) -> None:
    """Persist AI config to disk."""
    try:
        with open(AI_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save AI config: {e}")


def _get_config() -> dict:
    """Get effective AI config (file overrides env)."""
    file_cfg = _load_config_file()
    return {
        "api_base": file_cfg.get("api_base") or AI_API_BASE,
        "api_key": file_cfg.get("api_key") or AI_API_KEY,
        "default_model": file_cfg.get("default_model") or AI_DEFAULT_MODEL,
    }

# Built-in model list (supplemented by /v1/models if endpoint configured)
BUILTIN_MODELS = [
    {"id": "mimo-v2.5", "name": "MiMo v2.5", "description": "Default vision model", "type": "vision"},
    {"id": "gpt-4o", "name": "GPT-4o Vision", "description": "Multimodal vision model for medical image analysis", "type": "vision"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast lightweight vision analysis", "type": "vision"},
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "description": "Anthropic vision model", "type": "vision"},
]


@dataclass
class AIJob:
    job_id: str
    model_id: str
    status: str = "pending"  # pending | running | completed | failed
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    error: str | None = None
    result: dict | None = None
    progress_queue: asyncio.Queue | None = None


class AIService:
    """Manages AI analysis jobs and communicates with OpenAI-compatible API."""

    def __init__(self) -> None:
        self._jobs: dict[str, AIJob] = {}

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    @staticmethod
    def get_config() -> dict:
        return _get_config()

    @staticmethod
    def update_config(api_base: str | None, api_key: str | None, default_model: str | None) -> dict:
        file_cfg = _load_config_file()
        if api_base is not None:
            file_cfg["api_base"] = api_base
        if api_key is not None:
            file_cfg["api_key"] = api_key
        if default_model is not None:
            file_cfg["default_model"] = default_model
        _save_config_file(file_cfg)
        return _get_config()

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------
    async def list_models(self) -> list[dict[str, str]]:
        """Return available models. Falls back to built-in list if no endpoint."""
        cfg = _get_config()
        return await self.list_models_with_config(cfg["api_base"], cfg["api_key"])

    async def list_models_with_config(self, api_base: str, api_key: str) -> list[dict[str, str]]:
        """Return available models using explicit config. Falls back to built-in list."""
        if not api_base or not api_key:
            return BUILTIN_MODELS
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{api_base.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    return [
                        {"id": m["id"], "name": m.get("id", ""), "description": "Remote model", "type": "vision"}
                        for m in data
                    ]
        except Exception:
            logger.warning("Failed to fetch remote models, using built-in list")
        return BUILTIN_MODELS

    # ------------------------------------------------------------------
    # Job lifecycle
    # ------------------------------------------------------------------
    _JOB_TTL = 3600  # 1 hour

    def create_job(self, model_id: str) -> AIJob:
        self._evict_stale_jobs()
        job = AIJob(job_id=str(uuid.uuid4()), model_id=model_id)
        self._jobs[job.job_id] = job
        return job

    def _evict_stale_jobs(self) -> None:
        now = time.time()
        stale = [jid for jid, j in self._jobs.items() if now - j.created_at > self._JOB_TTL]
        for jid in stale:
            del self._jobs[jid]

    def get_job(self, job_id: str) -> AIJob | None:
        return self._jobs.get(job_id)

    async def run_analysis(
        self,
        job: AIJob,
        session_id: str,
        patient_id: str,
        series_uid: str,
        prompt: str,
        slice_strategy: str = "middle",
    ) -> None:
        """Run medical image analysis in background."""
        queue: asyncio.Queue = asyncio.Queue()
        job.progress_queue = queue
        job.status = "running"

        try:
            await queue.put({"progress": 0.1, "message": "Loading image data..."})

            # Load pixel data from session
            pixel_data = await asyncio.to_thread(
                self._load_pixel_data, session_id, patient_id, series_uid
            )
            if pixel_data is None:
                raise ValueError("Could not load image data for analysis")

            await queue.put({"progress": 0.3, "message": "Preparing image..."})
            b64_image = await asyncio.to_thread(
                self._pixel_to_base64, pixel_data, slice_strategy
            )

            await queue.put({"progress": 0.4, "message": f"Sending to {job.model_id}..."})

            # Call OpenAI-compatible API
            result = await self._call_vision_api(job.model_id, b64_image, prompt)

            await queue.put({"progress": 0.9, "message": "Processing results..."})

            job.result = result
            job.status = "completed"
            job.progress = 1.0
            await queue.put({"progress": 1.0, "message": "Analysis complete", "done": True})

        except Exception as e:
            logger.error(f"AI job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            await queue.put({"progress": 1.0, "message": f"Failed: {e}", "done": True, "error": True})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_pixel_data(
        self, session_id: str, patient_id: str, series_uid: str
    ) -> np.ndarray | None:
        """Load pixel data from disk cache."""
        from app.services.dicom_service import dicom_service

        session = dicom_service.get_session(session_id)
        if not session:
            return None
        patient = session.get("patients", {}).get(patient_id)
        if not patient:
            return None
        series_info = patient.get("series", {}).get(series_uid)
        if not series_info:
            return None

        npy_path = series_info.get("npy_path")
        if npy_path and os.path.exists(npy_path):
            return np.load(npy_path)

        # Try raw_data fallback
        raw = series_info.get("raw_data")
        if raw is not None:
            return np.asarray(raw) if not isinstance(raw, np.ndarray) else raw
        return None

    @staticmethod
    def _pixel_to_base64(pixel_data: np.ndarray, slice_strategy: str = "middle") -> str:
        """Convert numpy pixel array to base64-encoded PNG.

        Strategies:
        - middle: single middle slice (default)
        - multi: 5 evenly-spaced slices arranged in a row grid
        - mip: maximum intensity projection along axis 0
        """
        if pixel_data.ndim == 3:
            depth = pixel_data.shape[0]
            if slice_strategy == "multi" and depth >= 5:
                # Pick 5 evenly-spaced slices
                indices = np.linspace(0, depth - 1, 5, dtype=int)
                slices = [pixel_data[i] for i in indices]
                # Arrange in a row (1 row, 5 cols) with small gap
                gap = 2
                h, w = slices[0].shape
                canvas = np.zeros((h, w * 5 + gap * 4), dtype=slices[0].dtype)
                for col, s in enumerate(slices):
                    x = col * (w + gap)
                    canvas[:, x:x + w] = s
                slice_2d = canvas
            elif slice_strategy == "mip":
                # Maximum intensity projection
                slice_2d = np.max(pixel_data, axis=0)
            else:
                # Middle slice
                mid = depth // 2
                slice_2d = pixel_data[mid]
        else:
            slice_2d = pixel_data

        # Normalize to 0-255
        slice_2d = slice_2d.astype(np.float32)
        mn, mx = slice_2d.min(), slice_2d.max()
        if mx > mn:
            slice_2d = (slice_2d - mn) / (mx - mn) * 255.0
        else:
            slice_2d = np.zeros_like(slice_2d, dtype=np.float32)

        img = Image.fromarray(slice_2d.astype(np.uint8), mode="L")
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    async def _call_vision_api(
        self, model_id: str, b64_image: str, prompt: str
    ) -> dict[str, Any]:
        """Send image to OpenAI-compatible vision endpoint and parse response."""
        cfg = _get_config()
        if not cfg["api_base"] or not cfg["api_key"]:
            # Offline mode — return simulated analysis
            return self._simulate_analysis(prompt)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical imaging AI assistant. Analyze the provided "
                    "medical image and return structured findings in JSON format:\n"
                    '{"findings": [{"region": str, "description": str, "confidence": float, '
                    '"severity": "normal"|"mild"|"moderate"|"severe"}], '
                    '"summary": str, "modality_guess": str}'
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or "Analyze this medical image and provide structured findings."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}", "detail": "high"},
                    },
                ],
            },
        ]

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{cfg['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                },
                json={"model": model_id, "messages": messages, "max_tokens": 2048},
            )
            resp.raise_for_status()

        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Try to parse JSON from response
        try:
            # Handle markdown code blocks
            if "```" in content:
                # Find the first code block content
                start = content.find("```")
                if start != -1:
                    # Skip opening ``` and optional language tag
                    line_start = content.find("\n", start)
                    if line_start != -1:
                        end = content.find("```", line_start + 1)
                        if end != -1:
                            json_str = content[line_start + 1:end].strip()
                            if json_str.startswith("json"):
                                json_str = json_str[4:]
                            return json.loads(json_str)
            return json.loads(content)
        except json.JSONDecodeError:
            return {"findings": [], "summary": content, "modality_guess": "unknown"}

    # ------------------------------------------------------------------
    # Study summary generation
    # ------------------------------------------------------------------
    async def generate_summary(
        self,
        findings: list[dict[str, Any]],
        model_id: str = "gpt-4o-mini",
        patient_context: str = "",
    ) -> dict[str, Any]:
        """Generate a natural language study summary from findings."""
        cfg = _get_config()
        if not cfg["api_base"] or not cfg["api_key"]:
            return self._simulate_summary(findings)

        findings_text = json.dumps(findings, ensure_ascii=False, indent=2)
        system_prompt = (
            "You are a medical imaging report assistant. Given a list of AI-generated "
            "findings from a medical image analysis, produce a structured summary report.\n"
            "Return JSON with:\n"
            '{"summary": str (2-4 sentence overview), '
            '"key_findings": list[str] (top 3-5 concise bullet points), '
            '"recommendations": list[str] (0-3 clinical suggestions)}'
        )
        user_msg = f"Findings:\n{findings_text}"
        if patient_context:
            user_msg += f"\n\nPatient context: {patient_context}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{cfg['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()

        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        try:
            if "```" in content:
                start = content.find("```")
                if start != -1:
                    line_start = content.find("\n", start)
                    if line_start != -1:
                        end = content.find("```", line_start + 1)
                        if end != -1:
                            json_str = content[line_start + 1:end].strip()
                            if json_str.startswith("json"):
                                json_str = json_str[4:]
                            return json.loads(json_str)
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "summary": content,
                "key_findings": [],
                "recommendations": [],
            }

    # ------------------------------------------------------------------
    # AI Segmentation methods
    # ------------------------------------------------------------------

    async def run_auto_segmentation(
        self,
        job: AIJob,
        session_id: str,
        patient_id: str,
        series_uid: str,
        label_map_id: str,
        label: int,
    ) -> None:
        """Auto-detect lesions and generate segmentation mask.

        Uses vision API for localization, then classic image processing
        (Otsu + morphological ops) for pixel-level mask generation.
        """
        queue: asyncio.Queue = asyncio.Queue()
        job.progress_queue = queue
        job.status = "running"

        try:
            await queue.put({"progress": 0.1, "message": "Loading image data..."})

            pixel_data = await asyncio.to_thread(
                self._load_pixel_data, session_id, patient_id, series_uid
            )
            if pixel_data is None:
                raise ValueError("Could not load image data")

            if pixel_data.ndim != 3:
                raise ValueError(f"Expected 3D volume, got {pixel_data.ndim}D")

            await queue.put({"progress": 0.2, "message": "AI localizing regions of interest..."})

            # Use vision API to identify which slices likely contain lesions
            slice_range = await self._localize_slices(job.model_id, pixel_data)

            await queue.put({"progress": 0.5, "message": "Generating segmentation mask..."})

            # Generate pixel-level mask using classic methods on localized slices
            mask = await asyncio.to_thread(
                self._auto_segment_mask, pixel_data, slice_range
            )

            await queue.put({"progress": 0.8, "message": "Applying mask to label map..."})

            # Apply mask to label map
            from app.services.roi_service import roi_service
            await asyncio.to_thread(
                roi_service.apply_ai_mask, label_map_id, label, mask
            )

            job.result = {
                "type": "auto_segmentation",
                "label_map_id": label_map_id,
                "label": label,
                "slice_range": slice_range,
                "voxel_count": int(np.count_nonzero(mask)),
            }
            job.status = "completed"
            job.progress = 1.0
            await queue.put({"progress": 1.0, "message": "Segmentation complete", "done": True})

        except Exception as e:
            logger.error(f"Auto segmentation job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            await queue.put({"progress": 1.0, "message": f"Failed: {e}", "done": True, "error": True})

    async def run_text_guided_segmentation(
        self,
        job: AIJob,
        session_id: str,
        patient_id: str,
        series_uid: str,
        text_prompt: str,
        label_map_id: str,
        label: int,
    ) -> None:
        """Segment a structure described by text prompt.

        Uses organ matching for HU ranges, with optional vision API refinement.
        """
        queue: asyncio.Queue = asyncio.Queue()
        job.progress_queue = queue
        job.status = "running"

        try:
            await queue.put({"progress": 0.1, "message": "Loading image data..."})

            pixel_data = await asyncio.to_thread(
                self._load_pixel_data, session_id, patient_id, series_uid
            )
            if pixel_data is None:
                raise ValueError("Could not load image data")

            await queue.put({"progress": 0.3, "message": "Matching organ to HU range..."})

            # Find HU range from organ matching config
            hu_range = await asyncio.to_thread(
                self._match_organ_hu_range, text_prompt
            )

            await queue.put({"progress": 0.5, "message": "Generating mask with HU thresholding..."})

            if hu_range:
                # Use HU range for thresholding
                mask = await asyncio.to_thread(
                    self._threshold_segment_mask, pixel_data, hu_range
                )
            else:
                # Fallback: use vision API localization + Otsu
                await queue.put({"progress": 0.4, "message": "Using AI localization..."})
                slice_range = await self._localize_slices(job.model_id, pixel_data, text_prompt)
                mask = await asyncio.to_thread(
                    self._auto_segment_mask, pixel_data, slice_range
                )

            await queue.put({"progress": 0.8, "message": "Applying mask to label map..."})

            from app.services.roi_service import roi_service
            await asyncio.to_thread(
                roi_service.apply_ai_mask, label_map_id, label, mask
            )

            job.result = {
                "type": "text_guided_segmentation",
                "label_map_id": label_map_id,
                "label": label,
                "text_prompt": text_prompt,
                "hu_range": hu_range,
                "voxel_count": int(np.count_nonzero(mask)),
            }
            job.status = "completed"
            job.progress = 1.0
            await queue.put({"progress": 1.0, "message": "Segmentation complete", "done": True})

        except Exception as e:
            logger.error(f"Text segmentation job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            await queue.put({"progress": 1.0, "message": f"Failed: {e}", "done": True, "error": True})

    async def run_reference_guided_segmentation(
        self,
        job: AIJob,
        session_id: str,
        patient_id: str,
        series_uid: str,
        ref_label_map_id: str,
        ref_label: int,
        label_map_id: str,
        label: int,
    ) -> None:
        """Segment using an existing label as reference template.

        Extracts intensity statistics from the reference region and uses
        region growing to find similar tissue.
        """
        queue: asyncio.Queue = asyncio.Queue()
        job.progress_queue = queue
        job.status = "running"

        try:
            await queue.put({"progress": 0.1, "message": "Loading image data..."})

            pixel_data = await asyncio.to_thread(
                self._load_pixel_data, session_id, patient_id, series_uid
            )
            if pixel_data is None:
                raise ValueError("Could not load image data")

            await queue.put({"progress": 0.3, "message": "Loading reference mask..."})

            from app.services.roi_service import roi_service
            ref_lm = await asyncio.to_thread(roi_service.get_label_map, ref_label_map_id)
            if not ref_lm:
                raise ValueError("Reference label map not found")

            ref_mask = (ref_lm.volume == ref_label).astype(np.uint8)

            # Resize reference mask if shapes differ
            if ref_mask.shape != tuple(pixel_data.shape):
                from scipy.ndimage import zoom
                factors = [t / s for t, s in zip(pixel_data.shape, ref_mask.shape)]
                ref_mask = (zoom(ref_mask, factors, order=0) > 0.5).astype(np.uint8)

            await queue.put({"progress": 0.5, "message": "Extracting intensity statistics..."})

            mask = await asyncio.to_thread(
                self._reference_segment_mask, pixel_data, ref_mask
            )

            await queue.put({"progress": 0.8, "message": "Applying mask to label map..."})

            await asyncio.to_thread(
                roi_service.apply_ai_mask, label_map_id, label, mask
            )

            job.result = {
                "type": "reference_guided_segmentation",
                "label_map_id": label_map_id,
                "label": label,
                "ref_label_map_id": ref_label_map_id,
                "ref_label": ref_label,
                "voxel_count": int(np.count_nonzero(mask)),
            }
            job.status = "completed"
            job.progress = 1.0
            await queue.put({"progress": 1.0, "message": "Segmentation complete", "done": True})

        except Exception as e:
            logger.error(f"Reference segmentation job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            await queue.put({"progress": 1.0, "message": f"Failed: {e}", "done": True, "error": True})

    # ------------------------------------------------------------------
    # Segmentation helpers
    # ------------------------------------------------------------------

    async def _localize_slices(
        self, model_id: str, pixel_data: np.ndarray, hint: str = ""
    ) -> list[int]:
        """Use vision API to identify which slices likely contain lesions.

        Returns list of slice indices (axis 0) to focus on.
        """
        depth = pixel_data.shape[0]

        # Send MIP + a few key slices for localization
        b64_multi = await asyncio.to_thread(self._pixel_to_base64, pixel_data, "multi")

        prompt = (
            "This is a medical image volume showing 5 evenly-spaced slices. "
            "Identify which slices (0-indexed, approximate) contain abnormalities or structures of interest. "
            "Return JSON: {\"slice_indices\": [int, ...], \"description\": str}"
        )
        if hint:
            prompt += f"\nFocus on: {hint}"

        # Use multi-slice image for better context
        result = await self._call_vision_api(model_id, b64_multi, prompt)

        indices = result.get("slice_indices", [])
        if not indices:
            # Fallback: return middle half of slices
            quarter = depth // 4
            indices = list(range(quarter, depth - quarter))

        # Clamp to valid range
        return [max(0, min(depth - 1, i)) for i in indices]

    @staticmethod
    def _auto_segment_mask(
        pixel_data: np.ndarray,
        slice_range: list[int],
    ) -> np.ndarray:
        """Generate segmentation mask using Otsu thresholding + morphology.

        Focuses on the slices identified by the vision API.
        """
        from scipy.ndimage import binary_fill_holes, binary_closing, label as ndimage_label

        volume = pixel_data.astype(np.float64)
        mask = np.zeros(volume.shape, dtype=np.uint8)

        for z in slice_range:
            if z < 0 or z >= volume.shape[0]:
                continue
            slice_2d = volume[z]

            # Otsu threshold
            try:
                from skimage.filters import threshold_otsu
                thresh = threshold_otsu(slice_2d.astype(np.uint16))
            except ImportError:
                # Fallback: use percentile-based threshold
                nonzero = slice_2d[slice_2d > 0]
                if len(nonzero) == 0:
                    continue
                thresh = np.percentile(nonzero, 70)

            binary = (slice_2d > thresh).astype(np.uint8)

            # Morphological cleanup
            binary = binary_closing(binary, iterations=2).astype(np.uint8)
            binary = binary_fill_holes(binary).astype(np.uint8)

            # Keep only largest connected component
            labeled, num_features = ndimage_label(binary)
            if num_features > 0:
                sizes = np.bincount(labeled.ravel())
                sizes[0] = 0  # ignore background
                largest = sizes.argmax()
                binary = (labeled == largest).astype(np.uint8)

            mask[z] = binary

        # 3D closing to connect across slices
        mask = binary_closing(mask, iterations=1).astype(np.uint8)
        return mask

    @staticmethod
    def _match_organ_hu_range(text_prompt: str) -> tuple[float, float] | None:
        """Match text prompt to organ HU range from config."""
        import json as _json

        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config_files", "organ_matching.json"
        )
        try:
            with open(config_path, "r") as f:
                organ_config = _json.load(f)
        except (FileNotFoundError, OSError):
            return None

        prompt_lower = text_prompt.lower().strip()

        # Search organ aliases
        for organ_name, aliases in organ_config.items():
            if organ_name == "rules":
                continue
            if isinstance(aliases, list):
                for alias in aliases:
                    if alias in prompt_lower or prompt_lower in alias:
                        return _HU_RANGES.get(organ_name)
            elif isinstance(aliases, dict):
                for alias_key, alias_list in aliases.items():
                    if isinstance(alias_list, list):
                        for alias in alias_list:
                            if alias in prompt_lower or prompt_lower in alias:
                                return _HU_RANGES.get(organ_name)
        return None

    @staticmethod
    def _threshold_segment_mask(
        pixel_data: np.ndarray,
        hu_range: tuple[float, float],
    ) -> np.ndarray:
        """Generate mask by HU range thresholding + morphology."""
        from scipy.ndimage import binary_fill_holes, binary_closing, label as ndimage_label

        volume = pixel_data.astype(np.float64)
        mask = ((volume >= hu_range[0]) & (volume <= hu_range[1])).astype(np.uint8)

        # Per-slice morphological cleanup
        for z in range(mask.shape[0]):
            if mask[z].sum() == 0:
                continue
            mask[z] = binary_closing(mask[z], iterations=2).astype(np.uint8)
            mask[z] = binary_fill_holes(mask[z]).astype(np.uint8)

            labeled, num_features = ndimage_label(mask[z])
            if num_features > 0:
                sizes = np.bincount(labeled.ravel())
                sizes[0] = 0
                largest = sizes.argmax()
                mask[z] = (labeled == largest).astype(np.uint8)

        mask = binary_closing(mask, iterations=1).astype(np.uint8)
        return mask

    @staticmethod
    def _reference_segment_mask(
        pixel_data: np.ndarray,
        ref_mask: np.ndarray,
    ) -> np.ndarray:
        """Generate mask using reference region intensity statistics.

        Computes mean/std of intensities in the reference mask region,
        then finds similar voxels via z-score thresholding + region growing.
        """
        from scipy.ndimage import binary_fill_holes, binary_closing, label as ndimage_label

        volume = pixel_data.astype(np.float64)

        # Extract intensity stats from reference region
        ref_pixels = volume[ref_mask > 0]
        if len(ref_pixels) < 10:
            # Not enough reference data — fallback to Otsu
            return np.zeros(volume.shape, dtype=np.uint8)

        mean_val = np.mean(ref_pixels)
        std_val = max(np.std(ref_pixels), 1.0)
        z_thresh = 2.5

        # Find voxels with similar intensity
        z_scores = np.abs((volume - mean_val) / std_val)
        mask = (z_scores < z_thresh).astype(np.uint8)

        # Mask out background (zero voxels)
        mask[volume == 0] = 0

        # Per-slice cleanup
        for z in range(mask.shape[0]):
            if mask[z].sum() == 0:
                continue
            mask[z] = binary_closing(mask[z], iterations=2).astype(np.uint8)
            mask[z] = binary_fill_holes(mask[z]).astype(np.uint8)

            labeled, num_features = ndimage_label(mask[z])
            if num_features > 0:
                sizes = np.bincount(labeled.ravel())
                sizes[0] = 0
                largest = sizes.argmax()
                mask[z] = (labeled == largest).astype(np.uint8)

        mask = binary_closing(mask, iterations=1).astype(np.uint8)
        return mask

    @staticmethod
    def _simulate_summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a basic summary when no API is configured."""
        n = len(findings)
        severe = sum(1 for f in findings if f.get("severity") == "severe")
        moderate = sum(1 for f in findings if f.get("severity") == "moderate")
        parts = [f"Analysis identified {n} finding(s)"]
        if severe:
            parts.append(f"{severe} severe")
        if moderate:
            parts.append(f"{moderate} moderate")
        return {
            "summary": "; ".join(parts) + ". Configure AI endpoint for detailed summary.",
            "key_findings": [f"{f.get('region', '?')}: {f.get('description', '')[:80]}" for f in findings[:5]],
            "recommendations": [],
        }

    @staticmethod
    def _simulate_analysis(prompt: str) -> dict[str, Any]:
        """Return simulated analysis when no API is configured."""
        return {
            "findings": [
                {
                    "region": "Simulation",
                    "description": f"AI API not configured. Set AI_API_BASE and AI_API_KEY environment variables. Prompt received: {prompt[:100]}",
                    "confidence": 0.0,
                    "severity": "normal",
                }
            ],
            "summary": "Offline mode — no AI endpoint configured. Configure AI_API_BASE and AI_API_KEY to enable real analysis.",
            "modality_guess": "unknown",
        }


# Singleton
ai_service = AIService()
