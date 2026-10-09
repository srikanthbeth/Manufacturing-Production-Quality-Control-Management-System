from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.defect import Defect


class DefectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        defect: Defect,
    ) -> Defect:
        self.db.add(defect)
        self.db.commit()
        self.db.refresh(defect)
        return defect

    def get_by_id(
        self,
        defect_id: int,
    ) -> Optional[Defect]:
        return (
            self.db.query(Defect)
            .filter(
                Defect.id == defect_id
            )
            .first()
        )

    def get_by_defect_number(
        self,
        defect_number: str,
    ) -> Optional[Defect]:
        return (
            self.db.query(Defect)
            .filter(
                Defect.defect_number
                == defect_number
            )
            .first()
        )

    def get_all(
        self,
        search: Optional[str] = None,
        defect_type: Optional[str] = None,
        severity: Optional[str] = None,
        resolution_status: Optional[str] = None,
        production_batch_id: Optional[int] = None,
        product_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 10,
    ):
        query = self.db.query(Defect)

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                or_(
                    Defect.defect_number.ilike(
                        search_value
                    ),
                    Defect.defect_type.ilike(
                        search_value
                    ),
                    Defect.root_cause.ilike(
                        search_value
                    ),
                    Defect.corrective_action.ilike(
                        search_value
                    ),
                )
            )

        if defect_type:
            query = query.filter(
                Defect.defect_type
                == defect_type
            )

        if severity:
            query = query.filter(
                Defect.severity == severity
            )

        if resolution_status:
            query = query.filter(
                Defect.resolution_status
                == resolution_status
            )

        if production_batch_id:
            query = query.filter(
                Defect.production_batch_id
                == production_batch_id
            )

        if product_id:
            query = query.filter(
                Defect.product_id == product_id
            )

        total = query.count()

        defects = (
            query.order_by(
                Defect.id.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return defects, total

    def update(
        self,
        defect: Defect,
    ) -> Defect:
        self.db.commit()
        self.db.refresh(defect)
        return defect

    def delete(
        self,
        defect: Defect,
    ) -> None:
        self.db.delete(defect)
        self.db.commit()