from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.production_order import ProductionOrder


class ProductionOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        order_id: int,
    ):
        return self.db.scalar(
            select(ProductionOrder).where(
                ProductionOrder.id == order_id
            )
        )

    def get_by_order_number(
        self,
        order_number: str,
    ):
        return self.db.scalar(
            select(ProductionOrder).where(
                ProductionOrder.order_number == order_number
            )
        )

    def list(
        self,
        search: str | None = None,
        product_id: int | None = None,
        production_line_id: int | None = None,
        supervisor_id: int | None = None,
        priority=None,
        status=None,
        page: int = 1,
        page_size: int = 10,
    ):
        query = select(ProductionOrder)

        if search:
            search_value = f"%{search}%"

            query = query.where(
                ProductionOrder.order_number.ilike(
                    search_value
                )
            )

        if product_id is not None:
            query = query.where(
                ProductionOrder.product_id == product_id
            )

        if production_line_id is not None:
            query = query.where(
                ProductionOrder.production_line_id
                == production_line_id
            )

        if supervisor_id is not None:
            query = query.where(
                ProductionOrder.supervisor_id
                == supervisor_id
            )

        if priority is not None:
            query = query.where(
                ProductionOrder.priority == priority
            )

        if status is not None:
            query = query.where(
                ProductionOrder.status == status
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        query = query.order_by(
            ProductionOrder.id.desc()
        )

        query = query.offset(
            (page - 1) * page_size
        ).limit(page_size)

        items = self.db.scalars(query).all()

        return total, items

    def create(
        self,
        order: ProductionOrder,
    ):
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def update(
        self,
        order: ProductionOrder,
    ):
        self.db.commit()
        self.db.refresh(order)

        return order

    def delete(
        self,
        order: ProductionOrder,
    ):
        self.db.delete(order)
        self.db.commit()