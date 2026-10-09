from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.auth_token import AuthToken


class AuthTokenRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        token: str,
        token_type: str,
        expires_at: datetime,
    ):
        auth_token = AuthToken(
            user_id=user_id,
            token=token,
            token_type=token_type,
            expires_at=expires_at,
        )

        self.db.add(auth_token)
        self.db.flush()

        return auth_token

    def get_valid_refresh_token(self, token: str):
        statement = select(AuthToken).where(
            AuthToken.token == token,
            AuthToken.token_type == "refresh",
            AuthToken.revoked.is_(False),
        )

        auth_token = self.db.scalar(statement)

        if not auth_token:
            return None

        expires_at = auth_token.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= datetime.now(timezone.utc):
            return None

        return auth_token

    def revoke(self, auth_token: AuthToken):
        auth_token.revoked = True
        self.db.flush()

    def revoke_all_for_user(self, user_id: int):
        statement = select(AuthToken).where(
            AuthToken.user_id == user_id,
            AuthToken.revoked.is_(False),
        )

        tokens = self.db.scalars(statement).all()

        for token in tokens:
            token.revoked = True

        self.db.flush()