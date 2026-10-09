from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import ProductStatus
from models.product import Product
from repositories.product_repository import ProductRepository
from schemas.product import (
    ProductCreate,
    ProductUpdate,
)


class ProductService:

    def __init__(self, db: Session):
        self.repository = ProductRepository(db)

    def create(
        self,
        data: ProductCreate,
    ) -> Product:

        existing_product = self.repository.get_by_sku(
            data.sku
        )

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product SKU already exists",
            )

        product = Product(
            name=data.name,
            category=data.category,
            sku=data.sku,
            unit_of_measurement=data.unit_of_measurement,
            status=data.status,
            standard_production_time=data.standard_production_time,
        )

        return self.repository.create(product)

    def get_by_id(
        self,
        product_id: int,
    ) -> Product:

        product = self.repository.get_by_id(
            product_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        return product

    def list(
        self,
        search: str | None = None,
        category: str | None = None,
        status_value: ProductStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ):

        products, total = self.repository.search(
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
            "items": products,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> Product:

        product = self.get_by_id(product_id)

        if data.sku is not None:
            existing_product = (
                self.repository.get_by_sku(data.sku)
            )

            if (
                existing_product
                and existing_product.id != product.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product SKU already exists",
                )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(product, field, value)

        return self.repository.save(product)

    def update_status(
        self,
        product_id: int,
        status_value: ProductStatus,
    ) -> Product:

        product = self.get_by_id(product_id)

        product.status = status_value

        return self.repository.save(product)

    def delete(
        self,
        product_id: int,
    ) -> None:

        product = self.get_by_id(product_id)

        self.repository.delete(product)