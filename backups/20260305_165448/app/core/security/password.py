"""Password hashing and verification utility

Single source of truth for password hashing in the application.
Uses bcrypt for secure password hashing.

WP-10-03: Auth Repository + Password Hashing
"""

import bcrypt
import logging

logger = logging.getLogger(__name__)


def hash_password(plain_password: str) -> str:
    """Hash a plain password using bcrypt
    
    Args:
        plain_password: Plain text password
    
    Returns:
        str: Bcrypt hash (UTF-8 decoded)
    
    Raises:
        ValueError: If password is empty or invalid
    """
    if not plain_password or not isinstance(plain_password, str):
        raise ValueError("Password must be a non-empty string")
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    
    # Return as string (decode bytes)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a bcrypt hash
    
    Args:
        plain_password: Plain text password to verify
        password_hash: Bcrypt hash to compare against
    
    Returns:
        bool: True if password matches, False otherwise
    """
    if not plain_password or not password_hash:
        return False
    
    try:
        # Compare password with hash
        result = bcrypt.checkpw(
            plain_password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
        return result
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False
