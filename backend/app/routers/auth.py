"""Auth router — OIDC login flow, token management, user info."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.auth_service import (
    is_auth_enabled,
    get_oidc_discovery,
    exchange_code,
    refresh_token,
    create_access_token,
    decode_access_token,
    OIDC_CLIENT_ID,
    OIDC_REDIRECT_URI,
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    code: str


class RefreshRequest(BaseModel):
    refreshToken: str


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str | None = None
    expiresIn: int = 3600
    tokenType: str = "Bearer"


class UserInfo(BaseModel):
    sub: str
    name: str
    email: str
    isAuthenticated: bool


@router.get("/config")
async def auth_config():
    if not is_auth_enabled():
        return {"enabled": False}
    discovery = await get_oidc_discovery()
    return {
        "enabled": True,
        "authorizationEndpoint": discovery.get("authorization_endpoint", ""),
        "clientId": OIDC_CLIENT_ID,
        "redirectUri": OIDC_REDIRECT_URI,
    }


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if not is_auth_enabled():
        user_info = {"sub": "local", "name": "Local User", "email": "local@localhost"}
        token = create_access_token(user_info)
        return TokenResponse(accessToken=token)

    try:
        token_data = await exchange_code(req.code)
    except Exception:
        raise HTTPException(status_code=400, detail="Code exchange failed")

    access_token = token_data.get("access_token", "")
    refresh = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh,
        expiresIn=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    if not is_auth_enabled():
        raise HTTPException(status_code=400, detail="OIDC not configured")

    try:
        token_data = await refresh_token(req.refreshToken)
    except Exception:
        raise HTTPException(status_code=400, detail="Refresh failed")

    return TokenResponse(
        accessToken=token_data.get("access_token", ""),
        refreshToken=token_data.get("refresh_token"),
        expiresIn=token_data.get("expires_in", 3600),
    )


@router.get("/me", response_model=UserInfo)
async def me(user: dict = Depends(get_current_user)):
    return UserInfo(
        sub=user.get("sub", ""),
        name=user.get("name", ""),
        email=user.get("email", ""),
        isAuthenticated=user.get("sub") != "anonymous",
    )


@router.post("/logout")
async def logout():
    return {"status": "ok"}
