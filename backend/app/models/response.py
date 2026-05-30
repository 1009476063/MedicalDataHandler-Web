"""Standard API response models."""

from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    """Standard API response envelope."""
    success: bool
    data: Any = None
    error: Optional[str] = None


class PaginatedResponse(ApiResponse):
    """Paginated API response with metadata."""
    meta: dict = {}
