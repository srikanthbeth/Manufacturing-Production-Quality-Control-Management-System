from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import (
    ProductionOrderPriority,
    ProductionOrderStatus,
)


class ProductionOrderCreate(BaseModel):
    order_number: str = Field(
        min_length=1,
        max_length=100,
    )

    product_id: int = Field(
        gt=0,
    )

    quantity: int = Field(
        gt=0,
    )

    target_date: date

    production_line_id: int = Field(
        gt=0,
    )

    priority: ProductionOrderPriority = (
        ProductionOrderPriority.MEDIUM
    )

    supervisor_id: int = Field(
        gt=0,
    )


class ProductionOrderUpdate(BaseModel):
    product_id: int | None = Field(
        default=None,
        gt=0,
    )

    quantity: int | None = Field(
        default=None,
        gt=0,
    )

    target_date: date | None = None

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    priority: ProductionOrderPriority | None = None

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionOrderStatusUpdate(BaseModel):
    status: ProductionOrderStatus


class ProductionOrderResponse(BaseModel):
    id: int
    order_number: str
    product_id: int
    quantity: int
    target_date: date
    production_line_id: int
    priority: ProductionOrderPriority
    supervisor_id: int
    status: ProductionOrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductionOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductionOrderResponse]