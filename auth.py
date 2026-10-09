from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import UserRole
from database import get_db
from models.user import User
from schemas.auth import (
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from services.auth_service import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.register(
        full_name=data.full_name,
        email=data.email,
        password=data.password,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.login(
        email=data.email,
        password=data.password,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.refresh(
        refresh_token=data.refresh_token,
    )


@router.post(
    "/logout",
)
def logout(
    data: RefreshTokenRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.logout(
        user_id=current_user.id,
        refresh_token=(
            data.refresh_token
            if data
            else None
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post(
    "/password-reset/request",
)
def request_password_reset(
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.request_password_reset(
        email=data.email,
    )


@router.post(
    "/password-reset/confirm",
)
def reset_password(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.reset_password(
        token=data.token,
        new_password=data.new_password,
    )


@router.patch(
    "/users/{user_id}/deactivate",
    response_model=UserResponse,
)
def deactivate_user(
    user_id: int,
    _: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.deactivate_user(
        user_id=user_id,
    )


@router.patch(
    "/users/{user_id}/activate",
    response_model=UserResponse,
)
def activate_user(
    user_id: int,
    _: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.activate_user(
        user_id=user_id,
    )