"""
Authentication service — OIDC discovery, JWKS, JWT validation.
All auth is optional: when OIDC_ISSUER is not configured, auth is disabled.
"""
import os
import time
import logging
from typing import Any

import httpx
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# Configuration from environment
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")
OIDC_REDIRECT_URI = os.environ.get("OIDC_REDIRECT_URI", "http://localhost:5173/auth/callback")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 3600

# Cached OIDC discovery
_discovery_cache: dict[str, Any] = {}
_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0
_JWKS_CACHE_TTL = 3600


def is_auth_enabled() -> bool:
    if not OIDC_ISSUER:
        return False
    if not JWT_SECRET:
        raise RuntimeError(
            "OIDC_ISSUER is set but JWT_SECRET is not. "
            "Set the JWT_SECRET environment variable to a strong random string."
        )
    return True


async def get_oidc_discovery() -> dict[str, Any]:
    if _discovery_cache:
        return _discovery_cache
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{OIDC_ISSUER}/.well-known/openid-configuration")
        resp.raise_for_status()
        _discovery_cache.update(resp.json())
    return _discovery_cache


async def get_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_CACHE_TTL:
        return _jwks_cache
    discovery = await get_oidc_discovery()
    jwks_uri = discovery.get("jwks_uri", "")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(jwks_uri)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = now
    return _jwks_cache


async def exchange_code(code: str) -> dict[str, Any]:
    discovery = await get_oidc_discovery()
    token_endpoint = discovery.get("token_endpoint", "")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": OIDC_REDIRECT_URI,
                "client_id": OIDC_CLIENT_ID,
                "client_secret": OIDC_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_token(refresh_token_str: str) -> dict[str, Any]:
    discovery = await get_oidc_discovery()
    token_endpoint = discovery.get("token_endpoint", "")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            token_endpoint,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token_str,
                "client_id": OIDC_CLIENT_ID,
                "client_secret": OIDC_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        return resp.json()


def create_access_token(user_info: dict[str, Any]) -> str:
    payload = {
        "sub": user_info.get("sub", "anonymous"),
        "name": user_info.get("name", ""),
        "email": user_info.get("email", ""),
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


async def validate_oidc_token(token: str) -> dict[str, Any] | None:
    try:
        jwks = await get_jwks()
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key = k
                break
        if not key:
            return None
        from jose import jwk
        public_key = jwk.construct(key)
        return jwt.decode(token, public_key, algorithms=["RS256", "RS512", "ES256"])
    except Exception:
        return None
