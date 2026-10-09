from sqlalchemy import select
from sqlalchemy.orm import Session

from models.production_approval import ProductionApproval


class ProductionApprovalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_order_id(
        self,
        production_order_id: int,
    ):
        return self.db.scalar(
            select(ProductionApproval).where(
                ProductionApproval.production_order_id
                == production_order_id
            )
        )

    def create(
        self,
        approval: ProductionApproval,
    ):
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)

        return approval

    def update(
        self,
        approval: ProductionApproval,
    ):
        self.db.commit()
        self.db.refresh(approval)

        return approval