import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import (
    AccountStatus,
    ProductionLineStatus,
    UserRole,
)
from models.plant import Plant
from models.production_line import ProductionLine
from models.user import User
from repositories.production_line_repository import (
    ProductionLineRepository,
)


class ProductionLineService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ProductionLineRepository(db)

    def _validate_plant(self, plant_id: int):
        plant = self.db.get(
            Plant,
            plant_id,
        )

        if not plant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plant not found",
            )

        return plant

    def _validate_supervisor(
        self,
        supervisor_id: int | None,
    ):
        if supervisor_id is None:
            return None

        supervisor = self.db.get(
            User,
            supervisor_id,
        )

        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production supervisor not found",
            )

        if supervisor.status == AccountStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an inactive user as production supervisor",
            )

        if supervisor.role != UserRole.PRODUCTION_SUPERVISOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user must have Production Supervisor role",
            )

        return supervisor

    def create(
        self,
        name: str,
        code: str,
        production_capacity: int,
        plant_id: int,
        status_value: ProductionLineStatus,
        supervisor_id: int | None,
    ):
        code = code.strip().upper()

        existing = self.repository.get_by_code(code)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Production line code already exists",
            )

        self._validate_plant(plant_id)

        self._validate_supervisor(
            supervisor_id
        )

        production_line = ProductionLine(
            name=name.strip(),
            code=code,
            production_capacity=production_capacity,
            plant_id=plant_id,
            status=status_value,
            supervisor_id=supervisor_id,
        )

        self.repository.create(production_line)

        self.db.commit()
        self.repository.refresh(production_line)

        return production_line

    def get_by_id(self, line_id: int):
        production_line = self.repository.get_by_id(
            line_id
        )

        if not production_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production line not found",
            )

        return production_line

    def list_lines(
        self,
        search: str | None,
        plant_id: int | None,
        status_value: ProductionLineStatus | None,
        page: int,
        page_size: int,
    ):
        if plant_id is not None:
            self._validate_plant(plant_id)

        items, total = self.repository.search(
            search=search,
            plant_id=plant_id,
            status=status_value,
            page=page,
            page_size=page_size,
        )

        total_pages = (
            math.ceil(total / page_size)
            if total
            else 0
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update(
        self,
        line_id: int,
        data,
    ):
        production_line = self.get_by_id(line_id)

        if data.name is not None:
            production_line.name = data.name.strip()

        if data.production_capacity is not None:
            production_line.production_capacity = (
                data.production_capacity
            )

        if data.plant_id is not None:
            self._validate_plant(data.plant_id)
            production_line.plant_id = data.plant_id

        if data.status is not None:
            production_line.status = data.status

        if data.supervisor_id is not None:
            self._validate_supervisor(
                data.supervisor_id
            )
            production_line.supervisor_id = (
                data.supervisor_id
            )

        self.db.commit()
        self.repository.refresh(production_line)

        return production_line

    def update_status(
        self,
        line_id: int,
        status_value: ProductionLineStatus,
    ):
        production_line = self.get_by_id(line_id)

        production_line.status = status_value

        self.db.commit()
        self.repository.refresh(production_line)

        return production_line

    def assign_supervisor(
        self,
        line_id: int,
        supervisor_id: int,
    ):
        production_line = self.get_by_id(line_id)

        self._validate_supervisor(
            supervisor_id
        )

        production_line.supervisor_id = supervisor_id

        self.db.commit()
        self.repository.refresh(production_line)

        return production_line

    def remove_supervisor(
        self,
        line_id: int,
    ):
        production_line = self.get_by_id(line_id)

        production_line.supervisor_id = None

        self.db.commit()
        self.repository.refresh(production_line)

        return production_line

    def delete(
        self,
        line_id: int,
    ):
        production_line = self.get_by_id(line_id)

        self.repository.delete(production_line)

        self.db.commit()

        return {
            "message": "Production line deleted successfully"
        }