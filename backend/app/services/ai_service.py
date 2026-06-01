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
                json_str = content.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
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
                json_str = content.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "summary": content,
                "key_findings": [],
                "recommendations": [],
            }

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
