from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from core.enums import ProductStatus
from models.product import Product


class ProductRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        return product

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_by_sku(self, sku: str) -> Product | None:
        statement = select(Product).where(
            Product.sku == sku
        )

        return self.db.execute(statement).scalar_one_or_none()

    def search(
        self,
        search: str | None = None,
        category: str | None = None,
        status: ProductStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:

        statement = select(Product)

        if search:
            search_value = f"%{search}%"

            statement = statement.where(
                or_(
                    Product.name.ilike(search_value),
                    Product.sku.ilike(search_value),
                    Product.category.ilike(search_value),
                )
            )

        if category:
            statement = statement.where(
                Product.category.ilike(category)
            )

        if status:
            statement = statement.where(
                Product.status == status
            )

        count_statement = select(
            func.count()
        ).select_from(
            statement.subquery()
        )

        total = self.db.execute(
            count_statement
        ).scalar_one()

        offset = (page - 1) * page_size

        statement = (
            statement
            .order_by(Product.id)
            .offset(offset)
            .limit(page_size)
        )

        products = list(
            self.db.execute(statement).scalars().all()
        )

        return products, total

    def save(self, product: Product) -> Product:
        self.db.commit()
        self.db.refresh(product)

        return product

    def delete(self, product: Product) -> None:
        self.db.delete(product)
        self.db.commit()