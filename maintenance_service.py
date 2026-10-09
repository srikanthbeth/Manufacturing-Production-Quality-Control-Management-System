from datetime import datetime
from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.machine import Machine
from models.maintenance import Maintenance
from models.user import User
from repositories.maintenance_repository import (
    MaintenanceRepository,
)
from schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
)


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MaintenanceRepository(db)

    def create_maintenance(
        self,
        data: MaintenanceCreate,
    ) -> Maintenance:
        existing = (
            self.repository.get_by_number(
                data.maintenance_number
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maintenance number already exists",
            )

        machine = (
            self.db.query(Machine)
            .filter(
                Machine.id == data.machine_id
            )
            .first()
        )

        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

        if data.technician_id:
            technician = (
                self.db.query(User)
                .filter(
                    User.id == data.technician_id
                )
                .first()
            )

            if not technician:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Technician not found",
                )

        if (
            data.completed_date
            and data.completed_date < data.scheduled_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed date cannot be before scheduled date",
            )

        maintenance = Maintenance(
            maintenance_number=(
                data.maintenance_number
            ),
            machine_id=data.machine_id,
            maintenance_type=(
                data.maintenance_type.value
            ),
            maintenance_status=(
                data.maintenance_status.value
            ),
            scheduled_date=data.scheduled_date,
            completed_date=data.completed_date,
            next_due_date=data.next_due_date,
            technician_id=data.technician_id,
            issue_description=(
                data.issue_description
            ),
            maintenance_description=(
                data.maintenance_description
            ),
            root_cause=data.root_cause,
            corrective_action=(
                data.corrective_action
            ),
            spare_parts_used=(
                [
                    item.model_dump(mode="json")
                    for item in (
                        data.spare_parts_used or []
                    )
                ]
            ),
            maintenance_cost=(
                data.maintenance_cost
            ),
            alert_sent="No",
        )

        return self.repository.create(
            maintenance
        )

    def get_maintenance(
        self,
        maintenance_id: int,
    ) -> Maintenance:
        maintenance = (
            self.repository.get_by_id(
                maintenance_id
            )
        )

        if not maintenance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Maintenance record not found",
            )

        return maintenance

    def list_maintenance(
        self,
        search: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        maintenance_status: Optional[str] = None,
        machine_id: Optional[int] = None,
        technician_id: Optional[int] = None,
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
                maintenance_type=maintenance_type,
                maintenance_status=(
                    maintenance_status
                ),
                machine_id=machine_id,
                technician_id=technician_id,
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

    def update_maintenance(
        self,
        maintenance_id: int,
        data: MaintenanceUpdate,
    ) -> Maintenance:
        maintenance = self.get_maintenance(
            maintenance_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "maintenance_number" in update_data:
            existing = (
                self.repository.get_by_number(
                    update_data[
                        "maintenance_number"
                    ]
                )
            )

            if (
                existing
                and existing.id != maintenance_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maintenance number already exists",
                )

        if "machine_id" in update_data:
            machine = (
                self.db.query(Machine)
                .filter(
                    Machine.id
                    == update_data["machine_id"]
                )
                .first()
            )

            if not machine:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Machine not found",
                )

        if "technician_id" in update_data:
            if update_data["technician_id"]:
                technician = (
                    self.db.query(User)
                    .filter(
                        User.id
                        == update_data[
                            "technician_id"
                        ]
                    )
                    .first()
                )

                if not technician:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Technician not found",
                    )

        if "maintenance_type" in update_data:
            update_data[
                "maintenance_type"
            ] = update_data[
                "maintenance_type"
            ].value

        if "maintenance_status" in update_data:
            update_data[
                "maintenance_status"
            ] = update_data[
                "maintenance_status"
            ].value

        if "spare_parts_used" in update_data:
            update_data[
                "spare_parts_used"
            ] = [
                item.model_dump(mode="json")
                if hasattr(item, "model_dump")
                else item
                for item in (
                    update_data[
                        "spare_parts_used"
                    ]
                    or []
                )
            ]

        if (
            "scheduled_date" in update_data
            and "completed_date" in update_data
            and update_data["completed_date"]
            and update_data["completed_date"]
            < update_data["scheduled_date"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed date cannot be before scheduled date",
            )

        for field, value in update_data.items():
            setattr(
                maintenance,
                field,
                value,
            )

        if (
            maintenance.maintenance_status
            == "Completed"
        ):
            maintenance.alert_sent = "No"

        return self.repository.update(
            maintenance
        )

    def delete_maintenance(
        self,
        maintenance_id: int,
    ) -> None:
        maintenance = self.get_maintenance(
            maintenance_id
        )

        self.repository.delete(
            maintenance
        )

    def get_due_alerts(
        self,
    ):
        current_time = datetime.utcnow()

        items = (
            self.repository.get_due_maintenance(
                current_time
            )
        )

        alerts = []

        for item in items:
            if item.next_due_date:
                due_date = item.next_due_date
            else:
                due_date = item.scheduled_date

            if due_date <= current_time:
                alert_message = (
                    f"Maintenance {item.maintenance_number} "
                    f"is due for machine {item.machine_id}."
                )
            else:
                alert_message = (
                    f"Maintenance {item.maintenance_number} "
                    f"is scheduled for {due_date}."
                )

            if item.alert_sent != "Yes":
                item.alert_sent = "Yes"

            alerts.append(
                {
                    "id": item.id,
                    "maintenance_number": (
                        item.maintenance_number
                    ),
                    "machine_id": item.machine_id,
                    "maintenance_type": (
                        item.maintenance_type
                    ),
                    "scheduled_date": (
                        item.scheduled_date
                    ),
                    "next_due_date": (
                        item.next_due_date
                    ),
                    "maintenance_status": (
                        item.maintenance_status
                    ),
                    "technician_id": (
                        item.technician_id
                    ),
                    "alert_message": (
                        alert_message
                    ),
                }
            )

        self.db.commit()

        return alerts