from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import (
    AccountStatus,
    MachineStatus,
    PlantStatus,
    ProductionLineStatus,
    ProductionOrderStatus,
    UserRole,
)
from models.production_batch import ProductionBatch
from models.production_line import ProductionLine
from models.production_order import ProductionOrder
from models.machine import Machine
from models.user import User
from repositories.production_batch_repository import (
    ProductionBatchRepository,
)


SUPERVISOR_ROLES = {
    UserRole.PRODUCTION_SUPERVISOR,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PLANT_MANAGER,
    UserRole.SUPER_ADMIN,
}


class ProductionBatchService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ProductionBatchRepository(db)

    def _calculate_metrics(
        self,
        planned_quantity: int,
        produced_quantity: int,
        rejected_quantity: int,
    ) -> tuple[float, float, float]:

        if planned_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Planned quantity must be greater than zero",
            )

        if produced_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Produced quantity cannot be negative",
            )

        if rejected_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejected quantity cannot be negative",
            )

        if rejected_quantity > produced_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejected quantity cannot exceed produced quantity",
            )

        completion_percentage = (
            produced_quantity / planned_quantity
        ) * 100

        if produced_quantity > 0:
            rejection_percentage = (
                rejected_quantity / produced_quantity
            ) * 100
        else:
            rejection_percentage = 0.0

        production_efficiency = (
            (produced_quantity - rejected_quantity)
            / planned_quantity
        ) * 100

        return (
            round(completion_percentage, 2),
            round(rejection_percentage, 2),
            round(production_efficiency, 2),
        )

    def _validate_production_order(
        self,
        production_order_id: int,
    ) -> ProductionOrder:

        production_order = self.db.get(
            ProductionOrder,
            production_order_id,
        )

        if not production_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production order not found",
            )

        if production_order.status in {
            ProductionOrderStatus.COMPLETED,
            ProductionOrderStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cannot create or assign a batch to a "
                    "completed or cancelled production order"
                ),
            )

        return production_order

    def _validate_production_line(
        self,
        production_line_id: int,
    ) -> ProductionLine:

        production_line = self.db.get(
            ProductionLine,
            production_line_id,
        )

        if not production_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production line not found",
            )

        if production_line.status != ProductionLineStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Production line must be active",
            )

        return production_line

    def _validate_machine(
        self,
        machine_id: int,
        production_line_id: int,
    ) -> Machine:

        machine = self.db.get(
            Machine,
            machine_id,
        )

        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

        if machine.production_line_id != production_line_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Machine does not belong to the selected "
                    "production line"
                ),
            )

        if machine.status == MachineStatus.DECOMMISSIONED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Machine is decommissioned",
            )

        return machine

    def _validate_supervisor(
        self,
        supervisor_id: int,
    ) -> User:

        supervisor = self.db.get(
            User,
            supervisor_id,
        )

        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supervisor not found",
            )

        if supervisor.status != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supervisor account is inactive",
            )

        if supervisor.role not in SUPERVISOR_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not eligible to be a production supervisor",
            )

        return supervisor

    def _validate_times(
        self,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> None:

        if start_time and end_time and end_time < start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time cannot be before start time",
            )

    def create(
        self,
        batch_number: str,
        production_order_id: int,
        planned_quantity: int,
        produced_quantity: int,
        rejected_quantity: int,
        start_time: datetime | None,
        end_time: datetime | None,
        production_line_id: int,
        machine_id: int,
        supervisor_id: int,
    ) -> ProductionBatch:

        existing = self.repository.get_by_batch_number(
            batch_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch number already exists",
            )

        production_order = self._validate_production_order(
            production_order_id
        )

        production_line = self._validate_production_line(
            production_line_id
        )

        machine = self._validate_machine(
            machine_id,
            production_line.id,
        )

        supervisor = self._validate_supervisor(
            supervisor_id
        )

        self._validate_times(
            start_time,
            end_time,
        )

        if production_order.production_line_id != production_line.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Production line must match the production "
                    "order production line"
                ),
            )

        (
            completion_percentage,
            rejection_percentage,
            production_efficiency,
        ) = self._calculate_metrics(
            planned_quantity,
            produced_quantity,
            rejected_quantity,
        )

        batch = ProductionBatch(
            batch_number=batch_number,
            production_order_id=production_order.id,
            planned_quantity=planned_quantity,
            produced_quantity=produced_quantity,
            rejected_quantity=rejected_quantity,
            start_time=start_time,
            end_time=end_time,
            production_line_id=production_line.id,
            machine_id=machine.id,
            supervisor_id=supervisor.id,
            completion_percentage=completion_percentage,
            rejection_percentage=rejection_percentage,
            production_efficiency=production_efficiency,
        )

        return self.repository.create(batch)

    def get(
        self,
        batch_id: int,
    ) -> ProductionBatch:

        batch = self.repository.get_by_id(
            batch_id
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production batch not found",
            )

        return batch

    def list(
        self,
        search: str | None = None,
        production_order_id: int | None = None,
        production_line_id: int | None = None,
        machine_id: int | None = None,
        supervisor_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[int, list[ProductionBatch]]:

        return self.repository.list(
            search=search,
            production_order_id=production_order_id,
            production_line_id=production_line_id,
            machine_id=machine_id,
            supervisor_id=supervisor_id,
            page=page,
            page_size=page_size,
        )

    def update(
        self,
        batch_id: int,
        planned_quantity: int | None = None,
        produced_quantity: int | None = None,
        rejected_quantity: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        production_line_id: int | None = None,
        machine_id: int | None = None,
        supervisor_id: int | None = None,
    ) -> ProductionBatch:

        batch = self.get(batch_id)

        new_planned_quantity = (
            planned_quantity
            if planned_quantity is not None
            else batch.planned_quantity
        )

        new_produced_quantity = (
            produced_quantity
            if produced_quantity is not None
            else batch.produced_quantity
        )

        new_rejected_quantity = (
            rejected_quantity
            if rejected_quantity is not None
            else batch.rejected_quantity
        )

        new_start_time = (
            start_time
            if start_time is not None
            else batch.start_time
        )

        new_end_time = (
            end_time
            if end_time is not None
            else batch.end_time
        )

        new_production_line_id = (
            production_line_id
            if production_line_id is not None
            else batch.production_line_id
        )

        new_machine_id = (
            machine_id
            if machine_id is not None
            else batch.machine_id
        )

        new_supervisor_id = (
            supervisor_id
            if supervisor_id is not None
            else batch.supervisor_id
        )

        self._validate_production_order(
            batch.production_order_id
        )

        production_line = self._validate_production_line(
            new_production_line_id
        )

        self._validate_machine(
            new_machine_id,
            production_line.id,
        )

        self._validate_supervisor(
            new_supervisor_id
        )

        self._validate_times(
            new_start_time,
            new_end_time,
        )

        production_order = self.db.get(
            ProductionOrder,
            batch.production_order_id,
        )

        if production_order.production_line_id != new_production_line_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Production line must match the production "
                    "order production line"
                ),
            )

        (
            completion_percentage,
            rejection_percentage,
            production_efficiency,
        ) = self._calculate_metrics(
            new_planned_quantity,
            new_produced_quantity,
            new_rejected_quantity,
        )

        batch.planned_quantity = new_planned_quantity
        batch.produced_quantity = new_produced_quantity
        batch.rejected_quantity = new_rejected_quantity
        batch.start_time = new_start_time
        batch.end_time = new_end_time
        batch.production_line_id = new_production_line_id
        batch.machine_id = new_machine_id
        batch.supervisor_id = new_supervisor_id
        batch.completion_percentage = completion_percentage
        batch.rejection_percentage = rejection_percentage
        batch.production_efficiency = production_efficiency

        return self.repository.update(batch)

    def delete(
        self,
        batch_id: int,
    ) -> None:

        batch = self.get(batch_id)

        self.repository.delete(batch)