from datetime import datetime
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.downtime import Downtime


class DowntimeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        downtime: Downtime,
    ) -> Downtime:
        self.db.add(downtime)
        self.db.commit()
        self.db.refresh(downtime)
        return downtime

    def get_by_id(
        self,
        downtime_id: int,
    ) -> Optional[Downtime]:
        return (
            self.db.query(Downtime)
            .filter(
                Downtime.id == downtime_id
            )
            .first()
        )

    def get_by_number(
        self,
        downtime_number: str,
    ) -> Optional[Downtime]:
        return (
            self.db.query(Downtime)
            .filter(
                Downtime.downtime_number
                == downtime_number
            )
            .first()
        )

    def get_all(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        machine_id: Optional[int] = None,
        production_line_id: Optional[int] = None,
        responsible_person_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ):
        query = self.db.query(Downtime)

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                or_(
                    Downtime.downtime_number.ilike(
                        search_value
                    ),
                    Downtime.reason.ilike(
                        search_value
                    ),
                )
            )

        if category:
            query = query.filter(
                Downtime.category == category
            )

        if machine_id:
            query = query.filter(
                Downtime.machine_id == machine_id
            )

        if production_line_id:
            query = query.filter(
                Downtime.production_line_id
                == production_line_id
            )

        if responsible_person_id:
            query = query.filter(
                Downtime.responsible_person_id
                == responsible_person_id
            )

        total = query.count()

        skip = (page - 1) * limit

        items = (
            query.order_by(
                Downtime.id.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    def get_machine_downtime(
        self,
        machine_id: int,
        start_time: datetime,
        end_time: datetime,
    ):
        return (
            self.db.query(Downtime)
            .filter(
                Downtime.machine_id == machine_id,
                Downtime.start_time < end_time,
                or_(
                    Downtime.end_time.is_(None),
                    Downtime.end_time > start_time,
                ),
            )
            .all()
        )

    def update(
        self,
        downtime: Downtime,
    ) -> Downtime:
        self.db.commit()
        self.db.refresh(downtime)
        return downtime

    def delete(
        self,
        downtime: Downtime,
    ) -> None:
        self.db.delete(downtime)
        self.db.commit()