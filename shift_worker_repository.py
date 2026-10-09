from sqlalchemy.orm import Session

from models.shift_worker import ShiftWorker


class ShiftWorkerRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        assignment: ShiftWorker,
    ):
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_assignment(
        self,
        shift_id: int,
        worker_id: int,
    ):
        return (
            self.db.query(ShiftWorker)
            .filter(
                ShiftWorker.shift_id == shift_id,
                ShiftWorker.worker_id == worker_id,
            )
            .first()
        )

    def get_by_shift(
        self,
        shift_id: int,
    ):
        return (
            self.db.query(ShiftWorker)
            .filter(
                ShiftWorker.shift_id == shift_id
            )
            .order_by(
                ShiftWorker.id.desc()
            )
            .all()
        )

    def get_by_worker(
        self,
        worker_id: int,
    ):
        return (
            self.db.query(ShiftWorker)
            .filter(
                ShiftWorker.worker_id == worker_id
            )
            .order_by(
                ShiftWorker.id.desc()
            )
            .all()
        )

    def delete(
        self,
        assignment: ShiftWorker,
    ):
        self.db.delete(assignment)
        self.db.commit()