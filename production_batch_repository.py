from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from models.production_batch import ProductionBatch


class ProductionBatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        batch_id: int,
    ) -> ProductionBatch | None:
        return self.db.get(
            ProductionBatch,
            batch_id,
        )

    def get_by_batch_number(
        self,
        batch_number: str,
    ) -> ProductionBatch | None:
        statement = select(ProductionBatch).where(
            ProductionBatch.batch_number == batch_number
        )

        return self.db.scalar(statement)

    def list(
        self,
        search: str | None = None,
        production_order_id: int | None = None,
        production_line_id: int | None = None,
        machine_id: int | None = None,
        supervisor_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[int, list[ProductionBatch]]:

        statement = select(ProductionBatch)

        count_statement = select(
            func.count(ProductionBatch.id)
        )

        if search:
            search_filter = or_(
                ProductionBatch.batch_number.ilike(
                    f"%{search}%"
                ),
            )

            statement = statement.where(search_filter)
            count_statement = count_statement.where(
                search_filter
            )

        if production_order_id is not None:
            statement = statement.where(
                ProductionBatch.production_order_id
                == production_order_id
            )

            count_statement = count_statement.where(
                ProductionBatch.production_order_id
                == production_order_id
            )

        if production_line_id is not None:
            statement = statement.where(
                ProductionBatch.production_line_id
                == production_line_id
            )

            count_statement = count_statement.where(
                ProductionBatch.production_line_id
                == production_line_id
            )

        if machine_id is not None:
            statement = statement.where(
                ProductionBatch.machine_id
                == machine_id
            )

            count_statement = count_statement.where(
                ProductionBatch.machine_id
                == machine_id
            )

        if supervisor_id is not None:
            statement = statement.where(
                ProductionBatch.supervisor_id
                == supervisor_id
            )

            count_statement = count_statement.where(
                ProductionBatch.supervisor_id
                == supervisor_id
            )

        total = self.db.scalar(
            count_statement
        ) or 0

        offset = (page - 1) * page_size

        statement = (
            statement
            .order_by(ProductionBatch.id.desc())
            .offset(offset)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(statement).all()
        )

        return total, items

    def create(
        self,
        batch: ProductionBatch,
    ) -> ProductionBatch:
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        return batch

    def update(
        self,
        batch: ProductionBatch,
    ) -> ProductionBatch:
        self.db.commit()
        self.db.refresh(batch)

        return batch

    def delete(
        self,
        batch: ProductionBatch,
    ) -> None:
        self.db.delete(batch)
        self.db.commit()