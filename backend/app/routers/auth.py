from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import clear_session_cookie, create_token, hash_password, set_session_cookie, verify_password
from ..database import get_db
from ..dependencies import get_current_user
from ..models import DoctorProfile, PatientProfile, Role, User
from ..schemas import LoginRequest, SignupRequest
from ..serializers import serialize_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=Role(payload.role),
    )
    db.add(user)
    db.flush()

    if user.role == Role.patient:
        db.add(
            PatientProfile(
                user_id=user.id,
                full_name=user.name,
                allergies=[],
                chronic_conditions=[],
                medications=[],
            )
        )
    else:
        db.add(
            DoctorProfile(
                user_id=user.id,
                full_name=user.name,
            )
        )

    db.commit()
    db.refresh(user)

    set_session_cookie(response, create_token(user.id, user.role, user.session_version))
    return {"user": serialize_user(user)}


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.role.value != payload.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Selected role does not match this account",
        )

    set_session_cookie(response, create_token(user.id, user.role, user.session_version))
    return {"user": serialize_user(user)}


@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    current_user.session_version += 1
    db.commit()
    clear_session_cookie(response)
    return {"success": True}


@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    return {"user": serialize_user(current_user)}
