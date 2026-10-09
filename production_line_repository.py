from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from core.enums import ProductionLineStatus
from models.production_line import ProductionLine


class ProductionLineRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, production_line: ProductionLine):
        self.db.add(production_line)
        self.db.flush()
        self.db.refresh(production_line)
        return production_line

    def get_by_id(self, line_id: int):
        return self.db.get(
            ProductionLine,
            line_id,
        )

    def get_by_code(self, code: str):
        statement = select(ProductionLine).where(
            ProductionLine.code == code
        )

        return self.db.scalar(statement)

    def search(
        self,
        search: str | None = None,
        plant_id: int | None = None,
        status: ProductionLineStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        statement = select(ProductionLine)

        count_statement = select(
            func.count(ProductionLine.id)
        )

        if search:
            search_value = f"%{search.strip()}%"

            condition = or_(
                ProductionLine.name.ilike(search_value),
                ProductionLine.code.ilike(search_value),
            )

            statement = statement.where(condition)
            count_statement = count_statement.where(condition)

        if plant_id is not None:
            statement = statement.where(
                ProductionLine.plant_id == plant_id
            )

            count_statement = count_statement.where(
                ProductionLine.plant_id == plant_id
            )

        if status is not None:
            statement = statement.where(
                ProductionLine.status == status
            )

            count_statement = count_statement.where(
                ProductionLine.status == status
            )

        total = self.db.scalar(count_statement) or 0

        offset = (page - 1) * page_size

        statement = (
            statement
            .order_by(ProductionLine.id.asc())
            .offset(offset)
            .limit(page_size)
        )

        items = self.db.scalars(statement).all()

        return items, total

    def save(self):
        self.db.commit()

    def refresh(self, production_line: ProductionLine):
        self.db.refresh(production_line)

    def delete(self, production_line: ProductionLine):
        self.db.delete(production_line)
        self.db.flush()