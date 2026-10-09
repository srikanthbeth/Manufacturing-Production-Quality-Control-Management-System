from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.downtime import Downtime
from models.machine import Machine
from models.production_line import ProductionLine
from models.user import User
from repositories.downtime_repository import DowntimeRepository
from schemas.downtime import (
    DowntimeCreate,
    DowntimeUpdate,
)


class DowntimeService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DowntimeRepository(db)

    def _calculate_duration(
        self,
        start_time: datetime,
        end_time: Optional[datetime],
    ) -> Decimal:
        if end_time is None:
            return Decimal("0")

        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            )

        seconds = (
            end_time - start_time
        ).total_seconds()

        return Decimal(
            str(round(seconds / 60, 2))
        )

    def _validate_references(
        self,
        machine_id: int,
        production_line_id: int,
        responsible_person_id: int,
    ):
        machine = (
            self.db.query(Machine)
            .filter(
                Machine.id == machine_id
            )
            .first()
        )

        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

        production_line = (
            self.db.query(ProductionLine)
            .filter(
                ProductionLine.id
                == production_line_id
            )
            .first()
        )

        if not production_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production line not found",
            )

        responsible_person = (
            self.db.query(User)
            .filter(
                User.id
                == responsible_person_id
            )
            .first()
        )

        if not responsible_person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Responsible person not found",
            )

        if (
            hasattr(machine, "production_line_id")
            and machine.production_line_id
            != production_line_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Machine does not belong to "
                    "the selected production line"
                ),
            )

        return (
            machine,
            production_line,
            responsible_person,
        )

    def create_downtime(
        self,
        data: DowntimeCreate,
    ) -> Downtime:
        existing = (
            self.repository.get_by_number(
                data.downtime_number
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Downtime number already exists",
            )

        self._validate_references(
            data.machine_id,
            data.production_line_id,
            data.responsible_person_id,
        )

        duration = self._calculate_duration(
            data.start_time,
            data.end_time,
        )

        downtime = Downtime(
            downtime_number=(
                data.downtime_number
            ),
            machine_id=data.machine_id,
            production_line_id=(
                data.production_line_id
            ),
            responsible_person_id=(
                data.responsible_person_id
            ),
            category=data.category.value,
            reason=data.reason,
            start_time=data.start_time,
            end_time=data.end_time,
            duration_minutes=duration,
        )

        return self.repository.create(
            downtime
        )

    def get_downtime(
        self,
        downtime_id: int,
    ) -> Downtime:
        downtime = (
            self.repository.get_by_id(
                downtime_id
            )
        )

        if not downtime:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Downtime record not found",
            )

        return downtime

    def list_downtime(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        machine_id: Optional[int] = None,
        production_line_id: Optional[int] = None,
        responsible_person_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ):
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100",
            )

        items, total = (
            self.repository.get_all(
                search=search,
                category=category,
                machine_id=machine_id,
                production_line_id=production_line_id,
                responsible_person_id=(
                    responsible_person_id
                ),
                page=page,
                limit=limit,
            )
        )

        pages = (
            ceil(total / limit)
            if total
            else 0
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    def update_downtime(
        self,
        downtime_id: int,
        data: DowntimeUpdate,
    ) -> Downtime:
        downtime = self.get_downtime(
            downtime_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        machine_id = update_data.get(
            "machine_id",
            downtime.machine_id,
        )

        production_line_id = update_data.get(
            "production_line_id",
            downtime.production_line_id,
        )

        responsible_person_id = (
            update_data.get(
                "responsible_person_id",
                downtime.responsible_person_id,
            )
        )

        self._validate_references(
            machine_id,
            production_line_id,
            responsible_person_id,
        )

        if "downtime_number" in update_data:
            existing = (
                self.repository.get_by_number(
                    update_data[
                        "downtime_number"
                    ]
                )
            )

            if (
                existing
                and existing.id != downtime_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Downtime number already exists"
                    ),
                )

        if "category" in update_data:
            update_data["category"] = (
                update_data["category"].value
            )

        new_start_time = update_data.get(
            "start_time",
            downtime.start_time,
        )

        new_end_time = update_data.get(
            "end_time",
            downtime.end_time,
        )

        duration = self._calculate_duration(
            new_start_time,
            new_end_time,
        )

        update_data[
            "duration_minutes"
        ] = duration

        for field, value in update_data.items():
            setattr(
                downtime,
                field,
                value,
            )

        return self.repository.update(
            downtime
        )

    def delete_downtime(
        self,
        downtime_id: int,
    ) -> None:
        downtime = self.get_downtime(
            downtime_id
        )

        self.repository.delete(downtime)

    def calculate_downtime_percentage(
        self,
        machine_id: int,
        start_time: datetime,
        end_time: datetime,
    ):
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            )

        machine = (
            self.db.query(Machine)
            .filter(
                Machine.id == machine_id
            )
            .first()
        )

        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

        total_available_minutes = Decimal(
            str(
                (
                    end_time - start_time
                ).total_seconds()
                / 60
            )
        )

        records = (
            self.repository.get_machine_downtime(
                machine_id,
                start_time,
                end_time,
            )
        )

        total_downtime_minutes = Decimal(
            "0"
        )

        for record in records:
            overlap_start = max(
                record.start_time,
                start_time,
            )

            if record.end_time is None:
                overlap_end = end_time
            else:
                overlap_end = min(
                    record.end_time,
                    end_time,
                )

            if overlap_end > overlap_start:
                minutes = Decimal(
                    str(
                        (
                            overlap_end
                            - overlap_start
                        ).total_seconds()
                        / 60
                    )
                )

                total_downtime_minutes += (
                    minutes
                )

        if total_available_minutes <= 0:
            percentage = Decimal("0")
        else:
            percentage = (
                total_downtime_minutes
                / total_available_minutes
                * Decimal("100")
            )

        return {
            "machine_id": machine_id,
            "start_time": start_time,
            "end_time": end_time,
            "total_available_minutes": (
                total_available_minutes.quantize(
                    Decimal("0.01")
                )
            ),
            "total_downtime_minutes": (
                total_downtime_minutes.quantize(
                    Decimal("0.01")
                )
            ),
            "downtime_percentage": (
                percentage.quantize(
                    Decimal("0.01")
                )
            ),
        }