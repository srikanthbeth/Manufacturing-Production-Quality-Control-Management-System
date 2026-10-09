from sqlalchemy.orm import Session

from models.worker_batch_assignment import (
    WorkerBatchAssignment,
)


class WorkerBatchAssignmentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        assignment: WorkerBatchAssignment,
    ):
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_assignment(
        self,
        worker_id: int,
        production_batch_id: int,
    ):
        return (
            self.db.query(
                WorkerBatchAssignment
            )
            .filter(
                WorkerBatchAssignment.worker_id
                == worker_id,
                WorkerBatchAssignment.production_batch_id
                == production_batch_id,
            )
            .first()
        )

    def get_by_batch(
        self,
        production_batch_id: int,
    ):
        return (
            self.db.query(
                WorkerBatchAssignment
            )
            .filter(
                WorkerBatchAssignment.production_batch_id
                == production_batch_id
            )
            .order_by(
                WorkerBatchAssignment.id.desc()
            )
            .all()
        )

    def get_by_worker(
        self,
        worker_id: int,
    ):
        return (
            self.db.query(
                WorkerBatchAssignment
            )
            .filter(
                WorkerBatchAssignment.worker_id
                == worker_id
            )
            .order_by(
                WorkerBatchAssignment.id.desc()
            )
            .all()
        )

    def delete(
        self,
        assignment: WorkerBatchAssignment,
    ):
        self.db.delete(assignment)
        self.db.commit()