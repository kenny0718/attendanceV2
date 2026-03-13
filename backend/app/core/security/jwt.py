"""JWT Token Utilities (WP-10-04B)

Minimal JWT implementation for login API.
Uses HS256 algorithm with 900 seconds expiry.
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_access_token(claims: Dict[str, Any], expires_in: int = 900) -> str:
    """Create JWT access token
    
    Args:
        claims: Token claims (must include 'sub', 'company_id', 'role_id')
        expires_in: Token expiry in seconds (default: 900 = 15 minutes)
    
    Returns:
        str: JWT token
    
    Raises:
        ValueError: If required claims are missing
    """
    # Validate required claims
    required_claims = ["sub", "company_id", "role_id"]
    for claim in required_claims:
        if claim not in claims:
            raise ValueError(f"Missing required claim: {claim}")
    
    # Add timestamps
    now = datetime.now(timezone.utc)
    payload = {
        **claims,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp())
    }
    
    # Encode JWT
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256"
    )
    
    logger.debug(f"Created JWT token for sub={claims['sub']}, company_id={claims['company_id']}")
    
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT access token
    
    Args:
        token: JWT token string
    
    Returns:
        Dict[str, Any]: Decoded claims
    
    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise
