from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import ProductStatus


class ProductCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    category: str = Field(
        min_length=2,
        max_length=100,
    )

    sku: str = Field(
        min_length=2,
        max_length=100,
    )

    unit_of_measurement: str = Field(
        min_length=1,
        max_length=50,
    )

    status: ProductStatus = ProductStatus.ACTIVE

    standard_production_time: int = Field(
        gt=0,
    )


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    sku: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    unit_of_measurement: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    status: ProductStatus | None = None

    standard_production_time: int | None = Field(
        default=None,
        gt=0,
    )


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    sku: str
    unit_of_measurement: str
    status: ProductStatus
    standard_production_time: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int