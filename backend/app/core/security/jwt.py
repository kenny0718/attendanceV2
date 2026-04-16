"""JWT Token Utilities (WP-10-04B)

Minimal JWT implementation for login API.
Supports access and refresh tokens for sliding sessions.
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


ACCESS_REQUIRED_CLAIMS = ["sub", "company_id", "role_id", "session_id", "type"]
REFRESH_REQUIRED_CLAIMS = ["sub", "session_id", "type"]


def _build_payload(claims: Dict[str, Any], expires_in_seconds: int) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        **claims,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp())
    }


def create_access_token(claims: Dict[str, Any], expires_in: int | None = None) -> str:
    required_claims = ACCESS_REQUIRED_CLAIMS
    for claim in required_claims:
        if claim not in claims:
            raise ValueError(f"Missing required claim: {claim}")
    
    payload = _build_payload(
        {**claims, "type": "access"},
        expires_in or settings.access_token_minutes * 60,
    )
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    logger.debug(
        "Created access token for sub=%s, company_id=%s, session_id=%s",
        claims['sub'],
        claims['company_id'],
        claims['session_id'],
    )
    return token


def create_refresh_token(claims: Dict[str, Any], expires_in: int | None = None) -> str:
    required_claims = REFRESH_REQUIRED_CLAIMS
    for claim in required_claims:
        if claim not in claims:
            raise ValueError(f"Missing required claim: {claim}")

    payload = _build_payload(
        {**claims, "type": "refresh"},
        expires_in or settings.refresh_token_days * 86400,
    )
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    logger.debug("Created refresh token for sub=%s, session_id=%s", claims['sub'], claims['session_id'])
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    payload = _decode_token(token)
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload


def decode_refresh_token(token: str) -> Dict[str, Any]:
    payload = _decode_token(token)
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise
