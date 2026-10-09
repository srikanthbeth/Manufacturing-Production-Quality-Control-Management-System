from sqlalchemy.orm import Session

from models.shift_machine_usage import (
    ShiftMachineUsage,
)


class ShiftMachineUsageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        usage: ShiftMachineUsage,
    ):
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_by_shift(
        self,
        shift_id: int,
    ):
        return (
            self.db.query(ShiftMachineUsage)
            .filter(
                ShiftMachineUsage.shift_id == shift_id
            )
            .order_by(
                ShiftMachineUsage.id.desc()
            )
            .all()
        )