from datetime import UTC, datetime, timedelta
from typing import TypedDict
from uuid import uuid4

import bcrypt
import jwt
from fastapi import HTTPException, Response, status

from .config import settings
from .models import Role


SESSION_DURATION_DAYS = 7
JWT_ALGORITHM = "HS256"
TOKEN_TYPE = "session"

ROLE_PERMISSIONS: dict[Role, list[str]] = {
    Role.patient: [
        "patient:read:self",
    ],
    Role.doctor: [
        "doctor:read:patients",
        "doctor:write:encounters",
        "doctor:review:ai",
    ],
}


class TokenPayload(TypedDict):
    sub: str
    role: str
    permissions: list[str]
    session_version: int


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_role_permissions(role: Role) -> list[str]:
    return list(ROLE_PERMISSIONS[role])


def create_token(user_id: str, role: Role, session_version: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role.value,
        "permissions": get_role_permissions(role),
        "session_version": session_version,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "typ": TOKEN_TYPE,
        "jti": uuid4().hex,
        "exp": now + timedelta(days=SESSION_DURATION_DAYS),
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        if payload.get("typ") != TOKEN_TYPE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token",
            )
        permissions = payload.get("permissions")
        if not isinstance(permissions, list) or not all(
            isinstance(permission, str) for permission in permissions
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token",
            )
        return {
            "sub": str(payload["sub"]),
            "role": str(payload["role"]),
            "permissions": permissions,
            "session_version": int(payload["session_version"]),
        }
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        ) from error


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=SESSION_DURATION_DAYS * 24 * 60 * 60,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
