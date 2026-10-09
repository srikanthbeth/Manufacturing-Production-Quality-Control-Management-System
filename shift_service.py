from decimal import Decimal

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.machine import Machine
from models.production_batch import ProductionBatch
from models.shift import Shift
from models.shift_machine_usage import ShiftMachineUsage
from models.shift_production_output import ShiftProductionOutput
from models.shift_worker import ShiftWorker
from models.worker import Worker

from repositories.shift_repository import ShiftRepository
from repositories.shift_worker_repository import (
    ShiftWorkerRepository,
)
from repositories.shift_production_output_repository import (
    ShiftProductionOutputRepository,
)
from repositories.shift_machine_usage_repository import (
    ShiftMachineUsageRepository,
)


VALID_SHIFT_NAMES = {
    "Morning",
    "Evening",
    "Night",
}


class ShiftService:

    def __init__(self, db: Session):
        self.db = db

        self.repository = ShiftRepository(db)

        self.worker_repository = ShiftWorkerRepository(
            db
        )

        self.output_repository = (
            ShiftProductionOutputRepository(db)
        )

        self.machine_repository = (
            ShiftMachineUsageRepository(db)
        )

    def create_shift(self, data):
        if data.name not in VALID_SHIFT_NAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid shift name",
            )

        existing = self.repository.get_by_name(
            data.name
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Shift already exists",
            )

        if data.start_time == data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shift start time and end time cannot be the same",
            )

        shift = Shift(
            name=data.name,
            start_time=data.start_time,
            end_time=data.end_time,
            description=data.description,
            is_active=data.is_active,
        )

        return self.repository.create(shift)

    def get_shift(self, shift_id: int):
        shift = self.repository.get_by_id(
            shift_id
        )

        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift not found",
            )

        return shift

    def list_shifts(
        self,
        search=None,
        is_active=None,
        page=1,
        page_size=10,
    ):
        return self.repository.get_all(
            search=search,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )

    def update_shift(
        self,
        shift_id: int,
        data,
    ):
        shift = self.get_shift(shift_id)

        if data.name is not None:
            if data.name not in VALID_SHIFT_NAMES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid shift name",
                )

            if data.name != shift.name:
                existing = self.repository.get_by_name(
                    data.name
                )

                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Shift already exists",
                    )

                shift.name = data.name

        if data.start_time is not None:
            shift.start_time = data.start_time

        if data.end_time is not None:
            shift.end_time = data.end_time

        if (
            shift.start_time == shift.end_time
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shift start time and end time cannot be the same",
            )

        if data.description is not None:
            shift.description = data.description

        if data.is_active is not None:
            shift.is_active = data.is_active

        return self.repository.update(shift)

    def delete_shift(self, shift_id: int):
        shift = self.get_shift(shift_id)

        self.repository.delete(shift)

    def assign_worker(
        self,
        shift_id: int,
        worker_id: int,
    ):
        shift = self.get_shift(shift_id)

        if not shift.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign worker to inactive shift",
            )

        worker = self.db.get(
            Worker,
            worker_id,
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found",
            )

        if worker.status != "Active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active workers can be assigned to a shift",
            )

        existing = (
            self.worker_repository.get_assignment(
                shift_id,
                worker_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Worker is already assigned to this shift",
            )

        assignment = ShiftWorker(
            shift_id=shift_id,
            worker_id=worker_id,
        )

        return self.worker_repository.create(
            assignment
        )

    def remove_worker(
        self,
        shift_id: int,
        worker_id: int,
    ):
        assignment = (
            self.worker_repository.get_assignment(
                shift_id,
                worker_id,
            )
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker shift assignment not found",
            )

        self.worker_repository.delete(
            assignment
        )

    def get_shift_workers(
        self,
        shift_id: int,
    ):
        self.get_shift(shift_id)

        return self.worker_repository.get_by_shift(
            shift_id
        )

    def get_worker_shifts(
        self,
        worker_id: int,
    ):
        worker = self.db.get(
            Worker,
            worker_id,
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found",
            )

        return self.worker_repository.get_by_worker(
            worker_id
        )

    def record_production_output(
        self,
        shift_id: int,
        data,
    ):
        shift = self.get_shift(shift_id)

        if not shift.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot record output for inactive shift",
            )

        batch = self.db.get(
            ProductionBatch,
            data.production_batch_id,
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production batch not found",
            )

        if data.rejected_quantity > data.produced_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejected quantity cannot exceed produced quantity",
            )

        output = ShiftProductionOutput(
            shift_id=shift_id,
            production_batch_id=data.production_batch_id,
            produced_quantity=data.produced_quantity,
            rejected_quantity=data.rejected_quantity,
        )

        return self.output_repository.create(
            output
        )

    def get_production_output(
        self,
        shift_id: int,
    ):
        self.get_shift(shift_id)

        return self.output_repository.get_by_shift(
            shift_id
        )

    def record_machine_usage(
        self,
        shift_id: int,
        data,
    ):
        shift = self.get_shift(shift_id)

        if not shift.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot record machine usage for inactive shift",
            )

        machine = self.db.get(
            Machine,
            data.machine_id,
        )

        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

        if data.downtime_hours > data.usage_hours:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Downtime hours cannot exceed usage hours",
            )

        usage = ShiftMachineUsage(
            shift_id=shift_id,
            machine_id=data.machine_id,
            usage_hours=data.usage_hours,
            downtime_hours=data.downtime_hours,
            notes=data.notes,
        )

        return self.machine_repository.create(
            usage
        )

    def get_machine_usage(
        self,
        shift_id: int,
    ):
        self.get_shift(shift_id)

        return self.machine_repository.get_by_shift(
            shift_id
        )

    def get_performance(
        self,
        shift_id: int,
    ):
        shift = self.get_shift(shift_id)

        worker_count = (
            self.db.query(
                func.count(ShiftWorker.id)
            )
            .filter(
                ShiftWorker.shift_id == shift_id
            )
            .scalar()
            or 0
        )

        production_totals = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        ShiftProductionOutput.produced_quantity
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        ShiftProductionOutput.rejected_quantity
                    ),
                    0,
                ),
            )
            .filter(
                ShiftProductionOutput.shift_id
                == shift_id
            )
            .first()
        )

        machine_totals = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        ShiftMachineUsage.usage_hours
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        ShiftMachineUsage.downtime_hours
                    ),
                    0,
                ),
            )
            .filter(
                ShiftMachineUsage.shift_id
                == shift_id
            )
            .first()
        )

        total_produced = Decimal(
            str(production_totals[0])
        )

        total_rejected = Decimal(
            str(production_totals[1])
        )

        total_usage = Decimal(
            str(machine_totals[0])
        )

        total_downtime = Decimal(
            str(machine_totals[1])
        )

        if total_produced > 0:
            efficiency = float(
                (
                    (
                        total_produced
                        - total_rejected
                    )
                    / total_produced
                )
                * 100
            )
        else:
            efficiency = 0.0

        if worker_count > 0:
            output_per_worker = float(
                total_produced
                / Decimal(worker_count)
            )
        else:
            output_per_worker = 0.0

        return {
            "shift_id": shift.id,
            "shift_name": shift.name,
            "worker_count": worker_count,
            "total_produced_quantity": total_produced,
            "total_rejected_quantity": total_rejected,
            "total_machine_usage_hours": total_usage,
            "total_machine_downtime_hours": total_downtime,
            "production_efficiency": efficiency,
            "output_per_worker": output_per_worker,
        }