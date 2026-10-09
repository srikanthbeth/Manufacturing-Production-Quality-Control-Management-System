from datetime import datetime
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.maintenance import Maintenance


class MaintenanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        maintenance: Maintenance,
    ) -> Maintenance:
        self.db.add(maintenance)
        self.db.commit()
        self.db.refresh(maintenance)

        return maintenance

    def get_by_id(
        self,
        maintenance_id: int,
    ) -> Optional[Maintenance]:
        return (
            self.db.query(Maintenance)
            .filter(
                Maintenance.id == maintenance_id
            )
            .first()
        )

    def get_by_number(
        self,
        maintenance_number: str,
    ) -> Optional[Maintenance]:
        return (
            self.db.query(Maintenance)
            .filter(
                Maintenance.maintenance_number
                == maintenance_number
            )
            .first()
        )

    def get_all(
        self,
        search: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        maintenance_status: Optional[str] = None,
        machine_id: Optional[int] = None,
        technician_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ):
        query = self.db.query(Maintenance)

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                or_(
                    Maintenance.maintenance_number.ilike(
                        search_value
                    ),
                    Maintenance.issue_description.ilike(
                        search_value
                    ),
                    Maintenance.maintenance_description.ilike(
                        search_value
                    ),
                    Maintenance.root_cause.ilike(
                        search_value
                    ),
                    Maintenance.corrective_action.ilike(
                        search_value
                    ),
                )
            )

        if maintenance_type:
            query = query.filter(
                Maintenance.maintenance_type
                == maintenance_type
            )

        if maintenance_status:
            query = query.filter(
                Maintenance.maintenance_status
                == maintenance_status
            )

        if machine_id:
            query = query.filter(
                Maintenance.machine_id
                == machine_id
            )

        if technician_id:
            query = query.filter(
                Maintenance.technician_id
                == technician_id
            )

        total = query.count()

        skip = (page - 1) * limit

        items = (
            query.order_by(
                Maintenance.id.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    def get_due_maintenance(
        self,
        current_time: datetime,
    ):
        return (
            self.db.query(Maintenance)
            .filter(
                Maintenance.maintenance_status.in_(
                    [
                        "Scheduled",
                        "In Progress",
                    ]
                ),
                or_(
                    Maintenance.scheduled_date
                    <= current_time,
                    Maintenance.next_due_date
                    <= current_time,
                ),
            )
            .order_by(
                Maintenance.scheduled_date.asc()
            )
            .all()
        )

    def update(
        self,
        maintenance: Maintenance,
    ) -> Maintenance:
        self.db.commit()
        self.db.refresh(maintenance)

        return maintenance

    def delete(
        self,
        maintenance: Maintenance,
    ) -> None:
        self.db.delete(maintenance)
        self.db.commit()