import os

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException


def get_fernet():
    key = os.getenv("HEALTH_DATA_ENCRYPTION_KEY", "").strip()

    if not key:
        raise HTTPException(
            status_code=503,
            detail="Health data encryption is not configured."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="The health data encryption key is invalid."
        ) from exc


def encrypt_health_text(value: str) -> str:
    return get_fernet().encrypt(
        value.encode("utf-8")
    ).decode("ascii")


def decrypt_health_text(value: str) -> str:
    try:
        return get_fernet().decrypt(
            value.encode("ascii")
        ).decode("utf-8")

    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Saved health data could not be decrypted."
        ) from exc