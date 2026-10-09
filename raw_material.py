from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import MaterialStatus, MaterialTransactionType


class RawMaterialCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    material_code: str = Field(
        min_length=2,
        max_length=100,
    )

    category: str = Field(
        min_length=2,
        max_length=100,
    )

    unit: str = Field(
        min_length=1,
        max_length=50,
    )

    available_quantity: int = Field(
        default=0,
        ge=0,
    )

    minimum_stock_level: int = Field(
        default=0,
        ge=0,
    )

    reorder_level: int = Field(
        default=0,
        ge=0,
    )

    supplier_reference: str | None = Field(
        default=None,
        max_length=255,
    )

    status: MaterialStatus = MaterialStatus.ACTIVE


class RawMaterialUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    material_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    minimum_stock_level: int | None = Field(
        default=None,
        ge=0,
    )

    reorder_level: int | None = Field(
        default=None,
        ge=0,
    )

    supplier_reference: str | None = Field(
        default=None,
        max_length=255,
    )

    status: MaterialStatus | None = None


class RawMaterialResponse(BaseModel):
    id: int
    name: str
    material_code: str
    category: str
    unit: str
    available_quantity: int
    minimum_stock_level: int
    reorder_level: int
    supplier_reference: str | None
    status: MaterialStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class RawMaterialListResponse(BaseModel):
    items: list[RawMaterialResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MaterialStockRequest(BaseModel):
    quantity: int = Field(
        gt=0,
    )

    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class MaterialAdjustmentRequest(BaseModel):
    quantity: int

    reason: str = Field(
        min_length=2,
        max_length=500,
    )


class MaterialTransactionResponse(BaseModel):
    id: int
    material_id: int
    transaction_type: MaterialTransactionType
    quantity: int
    quantity_before: int
    quantity_after: int
    reason: str | None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class MaterialHistoryResponse(BaseModel):
    items: list[MaterialTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int