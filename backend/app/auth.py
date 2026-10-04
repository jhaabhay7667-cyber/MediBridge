import hashlib, hmac, os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

ALGO = "HS256"
bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    key = os.getenv("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY environment variable is not set")
    return key


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, _secret(), algorithm=ALGO)


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauthorized
    try:
        payload = jwt.decode(creds.credentials, _secret(), algorithms=[ALGO])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    if user is None:
        raise unauthorized
    return user
