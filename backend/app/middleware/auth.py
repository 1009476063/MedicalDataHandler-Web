"""Auth middleware — FastAPI dependency for protected endpoints."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import (
    is_auth_enabled,
    decode_access_token,
    validate_oidc_token,
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not is_auth_enabled():
        return {"sub": "anonymous", "name": "Local User", "email": ""}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try local JWT first
    payload = decode_access_token(token)
    if payload:
        return payload

    # Try OIDC token validation
    payload = await validate_oidc_token(token)
    if payload:
        return payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )
