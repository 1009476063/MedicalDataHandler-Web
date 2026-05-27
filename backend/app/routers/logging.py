from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.log_service import log_service

router = APIRouter()


class LogRequest(BaseModel):
    level: str = "info"
    message: str
    source: str = "system"


@router.post("/log")
async def add_log(req: LogRequest):
    entry = log_service.log(req.level, req.message, req.source)
    return {"success": True, "entry": entry}


@router.get("/logs")
async def get_logs(since: Optional[float] = None, level: Optional[str] = None, limit: int = 100):
    logs = log_service.get_logs(since=since, level=level, limit=limit)
    return {"logs": logs, "total": len(log_service.entries)}


@router.delete("/logs")
async def clear_logs():
    log_service.clear()
    return {"success": True}
