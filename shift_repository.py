from typing import Optional

from sqlalchemy.orm import Session

from models.shift import Shift


class ShiftRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, shift: Shift):
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def get_by_id(
        self,
        shift_id: int,
    ) -> Optional[Shift]:
        return (
            self.db.query(Shift)
            .filter(Shift.id == shift_id)
            .first()
        )

    def get_by_name(
        self,
        name: str,
    ) -> Optional[Shift]:
        return (
            self.db.query(Shift)
            .filter(Shift.name == name)
            .first()
        )

    def get_all(
        self,
        search=None,
        is_active=None,
        page=1,
        page_size=10,
    ):
        query = self.db.query(Shift)

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                Shift.name.ilike(search_value)
            )

        if is_active is not None:
            query = query.filter(
                Shift.is_active == is_active
            )

        total = query.count()

        offset = (page - 1) * page_size

        items = (
            query
            .order_by(Shift.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total

    def update(self, shift: Shift):
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def delete(self, shift: Shift):
        self.db.delete(shift)
        self.db.commit()