from typing import Optional

from sqlalchemy.orm import Session

from models.worker import Worker


class WorkerRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, worker: Worker):
        self.db.add(worker)
        self.db.commit()
        self.db.refresh(worker)
        return worker

    def get_by_id(
        self,
        worker_id: int,
    ) -> Optional[Worker]:
        return (
            self.db.query(Worker)
            .filter(Worker.id == worker_id)
            .first()
        )

    def get_by_user_id(
        self,
        user_id: int,
    ) -> Optional[Worker]:
        return (
            self.db.query(Worker)
            .filter(Worker.user_id == user_id)
            .first()
        )

    def get_by_employee_code(
        self,
        employee_code: str,
    ) -> Optional[Worker]:
        return (
            self.db.query(Worker)
            .filter(
                Worker.employee_code == employee_code
            )
            .first()
        )

    def get_all(
        self,
        search=None,
        department=None,
        shift=None,
        status=None,
        production_line_id=None,
        page=1,
        page_size=10,
    ):
        query = self.db.query(Worker)

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                (Worker.employee_code.ilike(search_value))
                | (Worker.skill.ilike(search_value))
                | (Worker.department.ilike(search_value))
            )

        if department:
            query = query.filter(
                Worker.department == department
            )

        if shift:
            query = query.filter(
                Worker.shift == shift
            )

        if status:
            query = query.filter(
                Worker.status == status
            )

        if production_line_id:
            query = query.filter(
                Worker.production_line_id
                == production_line_id
            )

        total = query.count()

        offset = (page - 1) * page_size

        items = (
            query
            .order_by(Worker.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total

    def update(self, worker: Worker):
        self.db.commit()
        self.db.refresh(worker)
        return worker

    def delete(self, worker: Worker):
        self.db.delete(worker)
        self.db.commit()

    def get_by_line(
        self,
        production_line_id: int,
    ):
        return (
            self.db.query(Worker)
            .filter(
                Worker.production_line_id
                == production_line_id
            )
            .order_by(Worker.id.desc())
            .all()
        )