from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.inventory_movement import InventoryMovement


class InventoryMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        movement: InventoryMovement,
    ) -> InventoryMovement:
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)

        return movement

    def get_by_id(
        self,
        movement_id: int,
    ) -> Optional[InventoryMovement]:
        return (
            self.db.query(InventoryMovement)
            .filter(
                InventoryMovement.id
                == movement_id
            )
            .first()
        )

    def get_by_transaction_number(
        self,
        transaction_number: str,
    ) -> Optional[InventoryMovement]:
        return (
            self.db.query(InventoryMovement)
            .filter(
                InventoryMovement.transaction_number
                == transaction_number
            )
            .first()
        )

    def get_all(
        self,
        search: Optional[str] = None,
        movement_type: Optional[str] = None,
        raw_material_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ):
        query = self.db.query(
            InventoryMovement
        )

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                or_(
                    InventoryMovement.transaction_number.ilike(
                        search_value
                    ),
                    InventoryMovement.reference_number.ilike(
                        search_value
                    ),
                    InventoryMovement.reason.ilike(
                        search_value
                    ),
                )
            )

        if movement_type:
            query = query.filter(
                InventoryMovement.movement_type
                == movement_type
            )

        if raw_material_id:
            query = query.filter(
                InventoryMovement.raw_material_id
                == raw_material_id
            )

        total = query.count()

        skip = (page - 1) * limit

        items = (
            query.order_by(
                InventoryMovement.id.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return items, total

    def get_by_raw_material(
        self,
        raw_material_id: int,
    ):
        return (
            self.db.query(InventoryMovement)
            .filter(
                InventoryMovement.raw_material_id
                == raw_material_id
            )
            .order_by(
                InventoryMovement.id.desc()
            )
            .all()
        )