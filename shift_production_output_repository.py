from sqlalchemy.orm import Session

from models.shift_production_output import (
    ShiftProductionOutput,
)


class ShiftProductionOutputRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        output: ShiftProductionOutput,
    ):
        self.db.add(output)
        self.db.commit()
        self.db.refresh(output)
        return output

    def get_by_shift(
        self,
        shift_id: int,
    ):
        return (
            self.db.query(ShiftProductionOutput)
            .filter(
                ShiftProductionOutput.shift_id == shift_id
            )
            .order_by(
                ShiftProductionOutput.id.desc()
            )
            .all()
        )