from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.enums import AccountStatus, UserRole
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from models.auth_token import AuthToken
from models.user import User
from repositories.auth_token_repository import AuthTokenRepository
from repositories.user_repository import UserRepository


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.token_repository = AuthTokenRepository(db)

    def register(
        self,
        full_name: str,
        email: str,
        password: str,
    ):
        email = email.lower().strip()

        existing_user = self.user_repository.get_by_email(
            email
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            full_name=full_name.strip(),
            email=email,
            password_hash=hash_password(password),
            role=UserRole.WORKER,
            status=AccountStatus.ACTIVE,
        )

        self.user_repository.create(user)

        self.db.commit()
        self.db.refresh(user)

        return user

    def login(
        self,
        email: str,
        password: str,
    ):
        email = email.lower().strip()

        user = self.user_repository.get_by_email(
            email
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if user.status == AccountStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(
            user.id
        )

        refresh_token, refresh_expiry = (
            create_refresh_token(user.id)
        )

        self.token_repository.create(
            user_id=user.id,
            token=refresh_token,
            token_type="refresh",
            expires_at=refresh_expiry,
        )

        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh(
        self,
        refresh_token: str,
    ):
        token_record = (
            self.token_repository.get_valid_refresh_token(
                refresh_token
            )
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = self.user_repository.get_by_id(
            token_record.user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if user.status == AccountStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        self.token_repository.revoke(
            token_record
        )

        access_token = create_access_token(
            user.id
        )

        new_refresh_token, expiry = (
            create_refresh_token(user.id)
        )

        self.token_repository.create(
            user_id=user.id,
            token=new_refresh_token,
            token_type="refresh",
            expires_at=expiry,
        )

        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    def logout(
        self,
        user_id: int,
        refresh_token: str | None = None,
    ):
        if refresh_token:
            token_record = (
                self.token_repository.get_valid_refresh_token(
                    refresh_token
                )
            )

            if (
                token_record
                and token_record.user_id == user_id
            ):
                self.token_repository.revoke(
                    token_record
                )
        else:
            self.token_repository.revoke_all_for_user(
                user_id
            )

        self.db.commit()

        return {
            "message": "Successfully logged out"
        }

    def deactivate_user(
        self,
        user_id: int,
    ):
        user = self.user_repository.get_by_id(
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.status = AccountStatus.INACTIVE

        self.token_repository.revoke_all_for_user(
            user.id
        )

        self.db.commit()
        self.db.refresh(user)

        return user

    def activate_user(
        self,
        user_id: int,
    ):
        user = self.user_repository.get_by_id(
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.status = AccountStatus.ACTIVE

        self.db.commit()
        self.db.refresh(user)

        return user

    def request_password_reset(
        self,
        email: str,
    ):
        email = email.lower().strip()

        user = self.user_repository.get_by_email(
            email
        )

        if not user:
            return {
                "message": (
                    "If the email exists, a password reset "
                    "request has been created"
                )
            }

        reset_token = token_urlsafe(32)

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=30)
        )

        self.token_repository.create(
            user_id=user.id,
            token=reset_token,
            token_type="password_reset",
            expires_at=expires_at,
        )

        self.db.commit()

        return {
            "message": "Password reset request created",
            "reset_token": reset_token,
        }

    def reset_password(
        self,
        token: str,
        new_password: str,
    ):
        statement = select(AuthToken).where(
            AuthToken.token == token,
            AuthToken.token_type == "password_reset",
            AuthToken.revoked.is_(False),
        )

        token_record = self.db.scalar(
            statement
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token",
            )

        expires_at = token_record.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= datetime.now(
            timezone.utc
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token expired",
            )

        user = self.user_repository.get_by_id(
            token_record.user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.password_hash = hash_password(
            new_password
        )

        token_record.revoked = True

        self.token_repository.revoke_all_for_user(
            user.id
        )

        self.db.commit()

        return {
            "message": "Password reset successfully"
        }