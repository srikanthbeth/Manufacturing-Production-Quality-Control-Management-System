from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import AccountStatus, UserRole
from models.quality_inspection import QualityInspection
from repositories.quality_inspection_repository import (
    QualityInspectionRepository,
)
from schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionUpdate,
)


class QualityInspectionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = QualityInspectionRepository(db)

    def create_inspection(
        self,
        data: QualityInspectionCreate,
    ) -> QualityInspection:
        existing = self.repository.get_by_inspection_number(
            data.inspection_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inspection number already exists",
            )

        inspector = self.db.query(
            self.db.get_bind().mapper_registry._class_registry.get(
                "User"
            )
        ).filter(False).first() if False else None

        from models.user import User
        from models.production_batch import ProductionBatch

        inspector = (
            self.db.query(User)
            .filter(User.id == data.inspector_id)
            .first()
        )

        if not inspector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspector not found",
            )

        if hasattr(inspector, "status"):
            if inspector.status == AccountStatus.INACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inspector is inactive",
                )

        batch = (
            self.db.query(ProductionBatch)
            .filter(
                ProductionBatch.id
                == data.production_batch_id
            )
            .first()
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production batch not found",
            )

        inspection = QualityInspection(
            inspection_number=data.inspection_number,
            inspection_type=data.inspection_type.value,
            inspector_id=data.inspector_id,
            production_batch_id=data.production_batch_id,
            inspection_date=data.inspection_date,
            parameters=data.parameters,
            expected_value=data.expected_value,
            actual_value=data.actual_value,
            result=data.result.value,
            remarks=data.remarks,
        )

        return self.repository.create(inspection)

    def get_inspection(
        self,
        inspection_id: int,
    ) -> QualityInspection:
        inspection = self.repository.get_by_id(
            inspection_id
        )

        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality inspection not found",
            )

        return inspection

    def list_inspections(
        self,
        search: Optional[str] = None,
        inspection_type: Optional[str] = None,
        result: Optional[str] = None,
        production_batch_id: Optional[int] = None,
        inspector_id: Optional[int] = None,
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

        skip = (page - 1) * limit

        inspections, total = self.repository.get_all(
            search=search,
            inspection_type=inspection_type,
            result=result,
            production_batch_id=production_batch_id,
            inspector_id=inspector_id,
            skip=skip,
            limit=limit,
        )

        pages = ceil(total / limit) if total else 0

        return {
            "items": inspections,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    def update_inspection(
        self,
        inspection_id: int,
        data: QualityInspectionUpdate,
    ) -> QualityInspection:
        inspection = self.get_inspection(
            inspection_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "inspection_number" in update_data:
            existing = (
                self.repository.get_by_inspection_number(
                    update_data["inspection_number"]
                )
            )

            if existing and existing.id != inspection_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inspection number already exists",
                )

        if "inspector_id" in update_data:
            from models.user import User

            inspector = (
                self.db.query(User)
                .filter(
                    User.id
                    == update_data["inspector_id"]
                )
                .first()
            )

            if not inspector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspector not found",
                )

            if hasattr(inspector, "status"):
                if inspector.status == AccountStatus.INACTIVE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Inspector is inactive",
                    )

        if "production_batch_id" in update_data:
            from models.production_batch import ProductionBatch

            batch = (
                self.db.query(ProductionBatch)
                .filter(
                    ProductionBatch.id
                    == update_data["production_batch_id"]
                )
                .first()
            )

            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Production batch not found",
                )

        if "inspection_type" in update_data:
            update_data["inspection_type"] = (
                update_data["inspection_type"].value
            )

        if "result" in update_data:
            update_data["result"] = (
                update_data["result"].value
            )

        for field, value in update_data.items():
            setattr(
                inspection,
                field,
                value,
            )

        return self.repository.update(inspection)

    def delete_inspection(
        self,
        inspection_id: int,
    ) -> None:
        inspection = self.get_inspection(
            inspection_id
        )

        self.repository.delete(inspection)