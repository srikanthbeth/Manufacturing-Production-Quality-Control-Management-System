from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int):
        return self.db.get(User, user_id)

    def get_by_email(self, email: str):
        statement = select(User).where(
            User.email == email
        )

        return self.db.scalar(statement)

    def create(self, user: User):
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)

        return user

    def save(self):
        self.db.commit()

    def refresh(self, user: User):
        self.db.refresh(user)