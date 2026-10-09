from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BOMItemCreate(BaseModel):
    material_id: int = Field(
        ...,
        gt=0,
    )

    quantity_required: float = Field(
        ...,
        gt=0,
    )


class BOMItemUpdate(BaseModel):
    quantity_required: float = Field(
        ...,
        gt=0,
    )


class BOMCreate(BaseModel):
    product_id: int = Field(
        ...,
        gt=0,
    )

    version: int = Field(
        ...,
        gt=0,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    is_active: bool = False

    items: list[BOMItemCreate] = Field(
        ...,
        min_length=1,
    )


class BOMUpdate(BaseModel):
    version: int | None = Field(
        default=None,
        gt=0,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class BOMItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    bom_id: int
    material_id: int
    quantity_required: float
    created_at: datetime
    updated_at: datetime


class BOMResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    product_id: int
    version: int
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[BOMItemResponse]


class BOMListResponse(BaseModel):
    id: int
    product_id: int
    version: int
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime