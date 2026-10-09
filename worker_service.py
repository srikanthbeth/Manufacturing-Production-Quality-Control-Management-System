from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from models.production_batch import ProductionBatch
from models.production_line import ProductionLine
from models.user import User
from models.worker import Worker
from models.worker_batch_assignment import (
    WorkerBatchAssignment,
)
from repositories.worker_repository import WorkerRepository
from repositories.worker_batch_assignment_repository import (
    WorkerBatchAssignmentRepository,
)


VALID_WORKER_STATUSES = {
    "Active",
    "Inactive",
    "On Leave",
    "Suspended",
}

VALID_SHIFTS = {
    "Morning",
    "Evening",
    "Night",
}


class WorkerService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = WorkerRepository(db)
        self.assignment_repository = (
            WorkerBatchAssignmentRepository(db)
        )

    def create_worker(self, data):

        existing_code = (
            self.repository.get_by_employee_code(
                data.employee_code
            )
        )

        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee code already exists",
            )

        user = self.db.get(
            User,
            data.user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        existing_worker = (
            self.repository.get_by_user_id(
                data.user_id
            )
        )

        if existing_worker:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Worker profile already exists for this user",
            )

        if data.status not in VALID_WORKER_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid worker status",
            )

        if data.shift not in VALID_SHIFTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid shift",
            )

        if data.production_line_id is not None:
            line = self.db.get(
                ProductionLine,
                data.production_line_id,
            )

            if not line:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Production line not found",
                )

        worker = Worker(
            user_id=data.user_id,
            employee_code=data.employee_code,
            skill=data.skill,
            department=data.department,
            shift=data.shift,
            production_line_id=data.production_line_id,
            status=data.status,
            profile_description=data.profile_description,
        )

        return self.repository.create(worker)

    def get_worker(self, worker_id: int):

        worker = self.repository.get_by_id(
            worker_id
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found",
            )

        return worker

    def list_workers(
        self,
        search=None,
        department=None,
        shift=None,
        status=None,
        production_line_id=None,
        page=1,
        page_size=10,
    ):

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than zero",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

        return self.repository.get_all(
            search=search,
            department=department,
            shift=shift,
            status=status,
            production_line_id=production_line_id,
            page=page,
            page_size=page_size,
        )

    def update_worker(
        self,
        worker_id: int,
        data,
    ):

        worker = self.get_worker(worker_id)

        if (
            data.employee_code is not None
            and data.employee_code
            != worker.employee_code
        ):
            existing = (
                self.repository.get_by_employee_code(
                    data.employee_code
                )
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Employee code already exists",
                )

            worker.employee_code = (
                data.employee_code
            )

        if data.skill is not None:
            worker.skill = data.skill

        if data.department is not None:
            worker.department = data.department

        if data.shift is not None:
            if data.shift not in VALID_SHIFTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid shift",
                )

            worker.shift = data.shift

        if data.status is not None:
            if data.status not in VALID_WORKER_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid worker status",
                )

            worker.status = data.status

        if data.production_line_id is not None:
            line = self.db.get(
                ProductionLine,
                data.production_line_id,
            )

            if not line:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Production line not found",
                )

            worker.production_line_id = (
                data.production_line_id
            )

        if data.profile_description is not None:
            worker.profile_description = (
                data.profile_description
            )

        return self.repository.update(worker)

    def delete_worker(self, worker_id: int):

        worker = self.get_worker(worker_id)

        self.repository.delete(worker)

    def assign_worker_to_batch(
        self,
        worker_id: int,
        production_batch_id: int,
    ):

        worker = self.repository.get_by_id(
            worker_id
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found",
            )

        if worker.status != "Active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active workers can be assigned",
            )

        batch = self.db.get(
            ProductionBatch,
            production_batch_id,
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production batch not found",
            )

        if (
            worker.production_line_id is not None
            and batch.production_line_id
            != worker.production_line_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Worker is not assigned to the production line of this batch",
            )

        existing = (
            self.assignment_repository.get_assignment(
                worker_id,
                production_batch_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Worker is already assigned to this production batch",
            )

        assignment = WorkerBatchAssignment(
            worker_id=worker_id,
            production_batch_id=production_batch_id,
        )

        return self.assignment_repository.create(
            assignment
        )

    def remove_worker_from_batch(
        self,
        worker_id: int,
        production_batch_id: int,
    ):

        assignment = (
            self.assignment_repository.get_assignment(
                worker_id,
                production_batch_id,
            )
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker assignment not found",
            )

        self.assignment_repository.delete(
            assignment
        )

    def get_batch_workers(
        self,
        production_batch_id: int,
    ):

        batch = self.db.get(
            ProductionBatch,
            production_batch_id,
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production batch not found",
            )

        assignments = (
            self.assignment_repository.get_by_batch(
                production_batch_id
            )
        )

        return assignments

    def get_worker_batches(
        self,
        worker_id: int,
    ):

        worker = self.repository.get_by_id(
            worker_id
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found",
            )

        return (
            self.assignment_repository.get_by_worker(
                worker_id
            )
        )