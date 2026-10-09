from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.enums import MachineStatus
from models.machine import Machine
from repositories.machine_repository import MachineRepository
from repositories.production_line_repository import ProductionLineRepository
from schemas.machine import (
    MachineCreate,
    MachineStatusUpdate,
    MachineUpdate,
)


class MachineService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MachineRepository(db)
        self.production_line_repository = (
            ProductionLineRepository(db)
        )

    def create(self, data: MachineCreate):
        existing = self.repository.get_by_code(
            data.machine_code
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Machine code already exists",
            )

        production_line = (
            self.production_line_repository.get_by_id(
                data.production_line_id
            )
        )

        if not production_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production line not found",
            )

        machine = Machine(
            machine_code=data.machine_code,
            machine_type=data.machine_type,
            production_line_id=data.production_line_id,
            installation_date=data.installation_date,
            status=data.status,
            operating_hours=data.operating_hours,
        )

        try:
            return self.repository.create(machine)

        except IntegrityError:
            self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Machine could not be created",
            )

    def get(self, machine_id: int):
        machine = self.repository.get_by_id(
            machine_id
        )

        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

        return machine

    def list(
        self,
        search: str | None = None,
        production_line_id: int | None = None,
        status: MachineStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        total, items = self.repository.list(
            search=search,
            production_line_id=production_line_id,
            status=status,
            page=page,
            page_size=page_size,
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    def update(
        self,
        machine_id: int,
        data: MachineUpdate,
    ):
        machine = self.get(machine_id)

        if machine.status == MachineStatus.DECOMMISSIONED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decommissioned machine cannot be modified",
            )

        if data.production_line_id is not None:
            production_line = (
                self.production_line_repository.get_by_id(
                    data.production_line_id
                )
            )

            if not production_line:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Production line not found",
                )

            machine.production_line_id = (
                data.production_line_id
            )

        if data.machine_type is not None:
            machine.machine_type = data.machine_type

        if data.installation_date is not None:
            machine.installation_date = (
                data.installation_date
            )

        if data.operating_hours is not None:
            machine.operating_hours = (
                data.operating_hours
            )

        return self.repository.update(machine)

    def update_status(
        self,
        machine_id: int,
        data: MachineStatusUpdate,
    ):
        machine = self.get(machine_id)

        if (
            machine.status
            == MachineStatus.DECOMMISSIONED
            and data.status != MachineStatus.DECOMMISSIONED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decommissioned machine cannot be reactivated",
            )

        machine.status = data.status

        return self.repository.update(machine)

    def delete(self, machine_id: int):
        machine = self.get(machine_id)

        if machine.status != MachineStatus.DECOMMISSIONED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only decommissioned machines can be deleted",
            )

        self.repository.delete(machine)

    def get_by_production_line(
        self,
        production_line_id: int,
    ):
        production_line = (
            self.production_line_repository.get_by_id(
                production_line_id
            )
        )

        if not production_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production line not found",
            )

        return self.repository.get_by_production_line(
            production_line_id
        )