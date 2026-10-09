from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import ProductionLineStatus


class ProductionLineCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=50,
    )

    production_capacity: int = Field(
        gt=0,
    )

    plant_id: int = Field(
        gt=0,
    )

    status: ProductionLineStatus = ProductionLineStatus.ACTIVE

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionLineUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    production_capacity: int | None = Field(
        default=None,
        gt=0,
    )

    plant_id: int | None = Field(
        default=None,
        gt=0,
    )

    status: ProductionLineStatus | None = None

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionLineResponse(BaseModel):
    id: int
    name: str
    code: str
    production_capacity: int
    plant_id: int
    status: ProductionLineStatus
    supervisor_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductionLineListResponse(BaseModel):
    items: list[ProductionLineResponse]
    total: int
    page: int
    page_size: int
    total_pages: int