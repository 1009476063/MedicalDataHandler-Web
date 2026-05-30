import subprocess
import time
import asyncio
import platform
from fastapi import APIRouter

from app.models.response import ApiResponse

router = APIRouter()
_start_time = time.time()

# GPU info cache (5 min TTL) to avoid repeated nvidia-smi calls
_gpu_cache: dict = {}
GPU_CACHE_TTL = 300  # 5 minutes


def _get_gpu_info_cached() -> dict:
    now = time.time()
    if _gpu_cache.get("data") and now - _gpu_cache.get("ts", 0) < GPU_CACHE_TTL:
        return _gpu_cache["data"]

    info = {
        "gpu_available": False,
        "gpu_name": None,
        "driver_version": None,
        "gpu_memory_mb": None,
    }
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            parts = line.split(",")
            name = parts[0].strip()
            mem = parts[1].strip() if len(parts) > 1 else "0"
            info.update({
                "gpu_available": True,
                "gpu_name": name,
                "gpu_memory_mb": int(mem),
            })
        cuda = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if cuda.returncode == 0 and cuda.stdout.strip():
            info["driver_version"] = cuda.stdout.strip().split("\n")[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    _gpu_cache["data"] = info
    _gpu_cache["ts"] = now
    return info


@router.get("/gpu-info")
async def get_gpu_info():
    return ApiResponse(success=True, data=await asyncio.to_thread(_get_gpu_info_cached))


@router.get("/info")
async def get_system_info():
    uptime = time.time() - _start_time
    return ApiResponse(success=True, data={
        "version": "1.0.0",
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "uptime_seconds": int(uptime),
        "hostname": platform.node(),
    })
