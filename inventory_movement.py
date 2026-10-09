from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InventoryMovementType(str, Enum):
    RAW_MATERIAL_RECEIPT = "Raw Material Receipt"
    MATERIAL_CONSUMPTION = "Material Consumption"
    FINISHED_GOODS_PRODUCTION = "Finished Goods Production"
    REJECTED_GOODS = "Rejected Goods"
    STOCK_ADJUSTMENT = "Stock Adjustment"


class InventoryMovementCreate(BaseModel):
    raw_material_id: int = Field(
        ...,
        gt=0,
    )

    movement_type: InventoryMovementType

    quantity: Decimal = Field(
        ...,
        gt=0,
    )

    reference_number: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    reason: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


class InventoryMovementResponse(BaseModel):
    id: int
    transaction_number: str
    raw_material_id: int
    movement_type: InventoryMovementType
    quantity: Decimal
    stock_before: Decimal
    stock_after: Decimal
    reference_number: Optional[str]
    reason: Optional[str]
    created_by_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class InventoryMovementListResponse(BaseModel):
    items: list[InventoryMovementResponse]
    total: int
    page: int
    limit: int
    pages: int


class InventoryStockResponse(BaseModel):
    raw_material_id: int
    available_quantity: Decimal
    minimum_stock_level: Decimal
    reorder_level: Decimal
    stock_status: str


class InventoryTransactionHistoryResponse(BaseModel):
    raw_material_id: int
    total_transactions: int
    total_receipts: Decimal
    total_consumption: Decimal
    total_adjustments: Decimal
    total_rejected: Decimal
    current_stock: Decimal