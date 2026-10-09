from decimal import Decimal
from math import ceil
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.inventory_movement import (
    InventoryMovement,
)
from models.raw_material import RawMaterial
from repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementType,
)


class InventoryMovementService:
    def __init__(self, db: Session):
        self.db = db

        self.repository = (
            InventoryMovementRepository(db)
        )

    def _get_material(
        self,
        raw_material_id: int,
    ) -> RawMaterial:
        material = (
            self.db.query(RawMaterial)
            .filter(
                RawMaterial.id
                == raw_material_id
            )
            .first()
        )

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Raw material not found",
            )

        return material

    def _generate_transaction_number(
        self,
    ) -> str:
        return (
            f"INV-{uuid4().hex[:10].upper()}"
        )

    def _calculate_stock(
        self,
        current_stock: Decimal,
        movement_type: InventoryMovementType,
        quantity: Decimal,
    ) -> Decimal:

        if movement_type in [
            InventoryMovementType.RAW_MATERIAL_RECEIPT,
            InventoryMovementType.FINISHED_GOODS_PRODUCTION,
            InventoryMovementType.STOCK_ADJUSTMENT,
        ]:
            return current_stock + quantity

        if movement_type in [
            InventoryMovementType.MATERIAL_CONSUMPTION,
            InventoryMovementType.REJECTED_GOODS,
        ]:
            new_stock = current_stock - quantity

            if new_stock < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient available stock",
                )

            return new_stock

        return current_stock

    def create_movement(
        self,
        data: InventoryMovementCreate,
        created_by_id: int,
    ) -> InventoryMovement:

        material = self._get_material(
            data.raw_material_id
        )

        if data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero",
            )

        current_stock = Decimal(
            str(
                material.available_quantity
                or 0
            )
        )

        new_stock = self._calculate_stock(
            current_stock=current_stock,
            movement_type=data.movement_type,
            quantity=data.quantity,
        )

        transaction_number = (
            self._generate_transaction_number()
        )

        movement = InventoryMovement(
            transaction_number=transaction_number,
            raw_material_id=data.raw_material_id,
            movement_type=data.movement_type.value,
            quantity=data.quantity,
            stock_before=current_stock,
            stock_after=new_stock,
            reference_number=(
                data.reference_number
            ),
            reason=data.reason,
            created_by_id=created_by_id,
        )

        material.available_quantity = (
            new_stock
        )

        self.db.add(movement)
        self.db.add(material)

        self.db.commit()

        self.db.refresh(movement)

        return movement

    def get_movement(
        self,
        movement_id: int,
    ) -> InventoryMovement:

        movement = (
            self.repository.get_by_id(
                movement_id
            )
        )

        if not movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory movement not found",
            )

        return movement

    def list_movements(
        self,
        search: Optional[str] = None,
        movement_type: Optional[str] = None,
        raw_material_id: Optional[int] = None,
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
                movement_type=movement_type,
                raw_material_id=raw_material_id,
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

    def get_stock(
        self,
        raw_material_id: int,
    ):

        material = self._get_material(
            raw_material_id
        )

        available_quantity = Decimal(
            str(
                material.available_quantity
                or 0
            )
        )

        minimum_stock_level = Decimal(
            str(
                material.minimum_stock_level
                or 0
            )
        )

        reorder_level = Decimal(
            str(
                material.reorder_level
                or 0
            )
        )

        if available_quantity <= 0:
            stock_status = "Out of Stock"

        elif available_quantity <= minimum_stock_level:
            stock_status = "Below Minimum Level"

        elif available_quantity <= reorder_level:
            stock_status = "Reorder Required"

        else:
            stock_status = "Available"

        return {
            "raw_material_id": raw_material_id,
            "available_quantity": available_quantity,
            "minimum_stock_level": minimum_stock_level,
            "reorder_level": reorder_level,
            "stock_status": stock_status,
        }

    def get_transaction_history(
        self,
        raw_material_id: int,
    ):

        material = self._get_material(
            raw_material_id
        )

        movements = (
            self.repository.get_by_raw_material(
                raw_material_id
            )
        )

        total_receipts = Decimal("0")
        total_consumption = Decimal("0")
        total_adjustments = Decimal("0")
        total_rejected = Decimal("0")

        for movement in movements:

            quantity = Decimal(
                str(movement.quantity)
            )

            if (
                movement.movement_type
                == InventoryMovementType.RAW_MATERIAL_RECEIPT.value
            ):
                total_receipts += quantity

            elif (
                movement.movement_type
                == InventoryMovementType.MATERIAL_CONSUMPTION.value
            ):
                total_consumption += quantity

            elif (
                movement.movement_type
                == InventoryMovementType.STOCK_ADJUSTMENT.value
            ):
                total_adjustments += quantity

            elif (
                movement.movement_type
                == InventoryMovementType.REJECTED_GOODS.value
            ):
                total_rejected += quantity

        return {
            "raw_material_id": raw_material_id,
            "total_transactions": len(
                movements
            ),
            "total_receipts": total_receipts,
            "total_consumption": total_consumption,
            "total_adjustments": total_adjustments,
            "total_rejected": total_rejected,
            "current_stock": Decimal(
                str(
                    material.available_quantity
                    or 0
                )
            ),
        }