from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.machine import Machine


class MachineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, machine_id: int):
        return self.db.scalar(
            select(Machine).where(
                Machine.id == machine_id
            )
        )

    def get_by_code(self, machine_code: str):
        return self.db.scalar(
            select(Machine).where(
                Machine.machine_code == machine_code
            )
        )

    def get_by_production_line(
        self,
        production_line_id: int,
    ):
        return self.db.scalars(
            select(Machine)
            .where(
                Machine.production_line_id
                == production_line_id
            )
            .order_by(Machine.id.desc())
        ).all()

    def list(
        self,
        search: str | None = None,
        production_line_id: int | None = None,
        status=None,
        page: int = 1,
        page_size: int = 10,
    ):
        query = select(Machine)

        if search:
            search_value = f"%{search}%"

            query = query.where(
                (Machine.machine_code.ilike(search_value))
                | (Machine.machine_type.ilike(search_value))
            )

        if production_line_id is not None:
            query = query.where(
                Machine.production_line_id
                == production_line_id
            )

        if status is not None:
            query = query.where(
                Machine.status == status
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        query = query.order_by(
            Machine.id.desc()
        )

        query = query.offset(
            (page - 1) * page_size
        ).limit(page_size)

        items = self.db.scalars(query).all()

        return total, items

    def create(self, machine: Machine):
        self.db.add(machine)
        self.db.commit()
        self.db.refresh(machine)

        return machine

    def update(self, machine: Machine):
        self.db.commit()
        self.db.refresh(machine)

        return machine

    def delete(self, machine: Machine):
        self.db.delete(machine)
        self.db.commit()

    def get_by_status(self, status):
        return self.db.scalars(
            select(Machine)
            .where(
                Machine.status == status
            )
            .order_by(Machine.id.desc())
        ).all()