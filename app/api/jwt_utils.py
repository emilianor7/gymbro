from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

from ..config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS


def create_access_token(user_id: int) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> Optional[int]:
    """Devuelve user_id si valido, None si invalido/expirado."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub else None
    except (jwt.PyJWTError, ValueError, TypeError):
        return None
