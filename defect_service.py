from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.defect import Defect
from models.product import Product
from models.production_batch import ProductionBatch
from repositories.defect_repository import DefectRepository
from schemas.defect import (
    DefectCreate,
    DefectUpdate,
)


class DefectService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DefectRepository(db)

    def create_defect(
        self,
        data: DefectCreate,
    ) -> Defect:
        existing = (
            self.repository.get_by_defect_number(
                data.defect_number
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Defect number already exists",
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

        product = (
            self.db.query(Product)
            .filter(
                Product.id == data.product_id
            )
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        defect = Defect(
            defect_number=data.defect_number,
            defect_type=data.defect_type,
            severity=data.severity.value,
            production_batch_id=data.production_batch_id,
            product_id=data.product_id,
            quantity_affected=data.quantity_affected,
            root_cause=data.root_cause,
            corrective_action=data.corrective_action,
            resolution_status=(
                data.resolution_status.value
            ),
        )

        return self.repository.create(defect)

    def get_defect(
        self,
        defect_id: int,
    ) -> Defect:
        defect = self.repository.get_by_id(
            defect_id
        )

        if not defect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Defect not found",
            )

        return defect

    def list_defects(
        self,
        search: Optional[str] = None,
        defect_type: Optional[str] = None,
        severity: Optional[str] = None,
        resolution_status: Optional[str] = None,
        production_batch_id: Optional[int] = None,
        product_id: Optional[int] = None,
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

        defects, total = (
            self.repository.get_all(
                search=search,
                defect_type=defect_type,
                severity=severity,
                resolution_status=resolution_status,
                production_batch_id=production_batch_id,
                product_id=product_id,
                skip=skip,
                limit=limit,
            )
        )

        pages = (
            ceil(total / limit)
            if total
            else 0
        )

        return {
            "items": defects,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    def update_defect(
        self,
        defect_id: int,
        data: DefectUpdate,
    ) -> Defect:
        defect = self.get_defect(
            defect_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "defect_number" in update_data:
            existing = (
                self.repository
                .get_by_defect_number(
                    update_data[
                        "defect_number"
                    ]
                )
            )

            if (
                existing
                and existing.id != defect_id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Defect number already exists"
                    ),
                )

        if "production_batch_id" in update_data:
            batch = (
                self.db.query(
                    ProductionBatch
                )
                .filter(
                    ProductionBatch.id
                    == update_data[
                        "production_batch_id"
                    ]
                )
                .first()
            )

            if not batch:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail=(
                        "Production batch not found"
                    ),
                )

        if "product_id" in update_data:
            product = (
                self.db.query(Product)
                .filter(
                    Product.id
                    == update_data[
                        "product_id"
                    ]
                )
                .first()
            )

            if not product:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Product not found",
                )

        if "severity" in update_data:
            update_data["severity"] = (
                update_data["severity"].value
            )

        if "resolution_status" in update_data:
            update_data[
                "resolution_status"
            ] = update_data[
                "resolution_status"
            ].value

        for field, value in update_data.items():
            setattr(
                defect,
                field,
                value,
            )

        return self.repository.update(
            defect
        )

    def delete_defect(
        self,
        defect_id: int,
    ) -> None:
        defect = self.get_defect(
            defect_id
        )

        self.repository.delete(defect)