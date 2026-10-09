from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import MaterialStatus, MaterialTransactionType
from models.material_transaction import MaterialTransaction
from models.raw_material import RawMaterial
from repositories.material_transaction_repository import (
    MaterialTransactionRepository,
)
from repositories.raw_material_repository import RawMaterialRepository
from schemas.raw_material import (
    MaterialAdjustmentRequest,
    MaterialStockRequest,
    RawMaterialCreate,
    RawMaterialUpdate,
)


class RawMaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = RawMaterialRepository(db)
        self.transaction_repository = MaterialTransactionRepository(db)

    # ============================================================
    # MATERIAL MASTER
    # ============================================================

    def create(
        self,
        data: RawMaterialCreate,
    ) -> RawMaterial:
        existing_material = self.repository.get_by_code(
            data.material_code
        )

        if existing_material:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Material code already exists",
            )

        if data.reorder_level > data.minimum_stock_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Reorder level cannot be greater "
                    "than minimum stock level"
                ),
            )

        material = RawMaterial(
            name=data.name,
            material_code=data.material_code,
            category=data.category,
            unit=data.unit,
            available_quantity=data.available_quantity,
            minimum_stock_level=data.minimum_stock_level,
            reorder_level=data.reorder_level,
            supplier_reference=data.supplier_reference,
            status=data.status,
        )

        return self.repository.create(material)

    def get_by_id(
        self,
        material_id: int,
    ) -> RawMaterial:
        material = self.repository.get_by_id(material_id)

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Raw material not found",
            )

        return material

    def list(
        self,
        search=None,
        category=None,
        status_value=None,
        page=1,
        page_size=10,
    ):
        materials, total = self.repository.search(
            search=search,
            category=category,
            status=status_value,
            page=page,
            page_size=page_size,
        )

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return {
            "items": materials,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update(
        self,
        material_id: int,
        data: RawMaterialUpdate,
    ) -> RawMaterial:
        material = self.get_by_id(material_id)

        if data.material_code is not None:
            existing_material = self.repository.get_by_code(
                data.material_code
            )

            if (
                existing_material
                and existing_material.id != material.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Material code already exists",
                )

        new_minimum_level = (
            data.minimum_stock_level
            if data.minimum_stock_level is not None
            else material.minimum_stock_level
        )

        new_reorder_level = (
            data.reorder_level
            if data.reorder_level is not None
            else material.reorder_level
        )

        if new_reorder_level > new_minimum_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Reorder level cannot be greater "
                    "than minimum stock level"
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(material, field, value)

        return self.repository.save(material)

    def update_status(
        self,
        material_id: int,
        status_value: MaterialStatus,
    ) -> RawMaterial:
        material = self.get_by_id(material_id)

        material.status = status_value

        return self.repository.save(material)

    def delete(
        self,
        material_id: int,
    ) -> None:
        material = self.get_by_id(material_id)

        self.repository.delete(material)

    # ============================================================
    # STOCK-IN
    # ============================================================

    def stock_in(
        self,
        material_id: int,
        data: MaterialStockRequest,
        user_id: int,
    ) -> RawMaterial:
        material = self.get_by_id(material_id)

        if material.status != MaterialStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot stock-in inactive material",
            )

        quantity_before = material.available_quantity

        quantity_after = (
            quantity_before + data.quantity
        )

        material.available_quantity = quantity_after

        transaction = MaterialTransaction(
            material_id=material.id,
            transaction_type=MaterialTransactionType.STOCK_IN,
            quantity=data.quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=data.reason,
            created_by=user_id,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(material)

        return material

    # ============================================================
    # STOCK-OUT
    # ============================================================

    def stock_out(
        self,
        material_id: int,
        data: MaterialStockRequest,
        user_id: int,
    ) -> RawMaterial:
        material = self.get_by_id(material_id)

        if material.status != MaterialStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot stock-out inactive material",
            )

        quantity_before = material.available_quantity

        if data.quantity > quantity_before:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient material stock",
            )

        quantity_after = (
            quantity_before - data.quantity
        )

        if quantity_after < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inventory cannot become negative",
            )

        material.available_quantity = quantity_after

        transaction = MaterialTransaction(
            material_id=material.id,
            transaction_type=MaterialTransactionType.STOCK_OUT,
            quantity=data.quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=data.reason,
            created_by=user_id,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(material)

        return material

    # ============================================================
    # ADJUSTMENT
    # ============================================================

    def adjustment(
        self,
        material_id: int,
        data: MaterialAdjustmentRequest,
        user_id: int,
    ) -> RawMaterial:
        material = self.get_by_id(material_id)

        if material.status != MaterialStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot adjust inactive material",
            )

        quantity_before = material.available_quantity

        quantity_after = (
            quantity_before + data.quantity
        )

        if quantity_after < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inventory cannot become negative",
            )

        material.available_quantity = quantity_after

        transaction = MaterialTransaction(
            material_id=material.id,
            transaction_type=MaterialTransactionType.ADJUSTMENT,
            quantity=data.quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=data.reason,
            created_by=user_id,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(material)

        return material

    # ============================================================
    # MATERIAL HISTORY
    # ============================================================

    def history(
        self,
        material_id: int,
        page: int = 1,
        page_size: int = 10,
    ):
        self.get_by_id(material_id)

        transactions, total = (
            self.transaction_repository.get_history(
                material_id=material_id,
                page=page,
                page_size=page_size,
            )
        )

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return {
            "items": transactions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }