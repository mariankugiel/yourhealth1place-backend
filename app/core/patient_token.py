from datetime import datetime, timedelta
from typing import Optional

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


def _get_secret() -> str:
    """
    Resolve the secret used for patient token signing.

    Falls back to the main SECRET_KEY when a dedicated secret is not provided.
    """
    return settings.PATIENT_TOKEN_SECRET or settings.SECRET_KEY


def generate_patient_token(patient_id: int, expires_minutes: Optional[int] = None) -> str:
    """
    Generate a signed token that represents a patient identifier.

    Args:
        patient_id: Internal patient ID to encode.
        expires_minutes: Optional custom expiration in minutes. Falls back to
            settings.PATIENT_TOKEN_EXPIRES_MINUTES.

    Returns:
        Signed JWT token string.
    """
    expiry_window = expires_minutes if expires_minutes is not None else settings.PATIENT_TOKEN_EXPIRES_MINUTES

    payload = {
        "pid": int(patient_id),
    }

    if expiry_window:
        payload["exp"] = datetime.utcnow() + timedelta(minutes=expiry_window)

    return jwt.encode(payload, _get_secret(), algorithm=settings.ALGORITHM)


def decode_patient_token(token: str) -> Optional[int]:
    """
    Decode a patient token and extract the patient ID.

    Args:
        token: Token string produced by generate_patient_token.

    Returns:
        The encoded patient ID or None if the token is invalid/expired.
    """
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[settings.ALGORITHM])
        patient_id = payload.get("pid")
        if patient_id is None:
            return None
        return int(patient_id)
    except (ExpiredSignatureError, InvalidTokenError, ValueError, TypeError):
        return None

