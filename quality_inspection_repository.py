from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.quality_inspection import QualityInspection


class QualityInspectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        inspection: QualityInspection,
    ) -> QualityInspection:
        self.db.add(inspection)
        self.db.commit()
        self.db.refresh(inspection)
        return inspection

    def get_by_id(
        self,
        inspection_id: int,
    ) -> Optional[QualityInspection]:
        return (
            self.db.query(QualityInspection)
            .filter(QualityInspection.id == inspection_id)
            .first()
        )

    def get_by_inspection_number(
        self,
        inspection_number: str,
    ) -> Optional[QualityInspection]:
        return (
            self.db.query(QualityInspection)
            .filter(
                QualityInspection.inspection_number
                == inspection_number
            )
            .first()
        )

    def get_all(
        self,
        search: Optional[str] = None,
        inspection_type: Optional[str] = None,
        result: Optional[str] = None,
        production_batch_id: Optional[int] = None,
        inspector_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 10,
    ):
        query = self.db.query(QualityInspection)

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                or_(
                    QualityInspection.inspection_number.ilike(
                        search_value
                    ),
                    QualityInspection.parameters.ilike(
                        search_value
                    ),
                    QualityInspection.expected_value.ilike(
                        search_value
                    ),
                    QualityInspection.actual_value.ilike(
                        search_value
                    ),
                    QualityInspection.remarks.ilike(
                        search_value
                    ),
                )
            )

        if inspection_type:
            query = query.filter(
                QualityInspection.inspection_type
                == inspection_type
            )

        if result:
            query = query.filter(
                QualityInspection.result == result
            )

        if production_batch_id:
            query = query.filter(
                QualityInspection.production_batch_id
                == production_batch_id
            )

        if inspector_id:
            query = query.filter(
                QualityInspection.inspector_id
                == inspector_id
            )

        total = query.count()

        inspections = (
            query.order_by(
                QualityInspection.id.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return inspections, total

    def update(
        self,
        inspection: QualityInspection,
    ) -> QualityInspection:
        self.db.commit()
        self.db.refresh(inspection)
        return inspection

    def delete(
        self,
        inspection: QualityInspection,
    ) -> None:
        self.db.delete(inspection)
        self.db.commit()