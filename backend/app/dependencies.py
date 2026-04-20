from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .auth import decode_token
from .config import settings
from .database import get_db
from .models import Role, User


@dataclass
class AuthContext:
    user_id: str
    role: Role


def get_auth_context(request: Request) -> AuthContext:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = decode_token(token)
    return AuthContext(user_id=payload["sub"], role=Role(payload["role"]))


def require_role(role: Role):
    def dependency(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if auth.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return auth

    return dependency


def get_current_user(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, auth.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is no longer valid",
        )
    return user
