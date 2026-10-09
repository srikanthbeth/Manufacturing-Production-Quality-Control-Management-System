from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductionBatchCreate(BaseModel):
    batch_number: str = Field(
        min_length=1,
        max_length=100,
    )

    production_order_id: int = Field(
        gt=0,
    )

    planned_quantity: int = Field(
        gt=0,
    )

    produced_quantity: int = Field(
        default=0,
        ge=0,
    )

    rejected_quantity: int = Field(
        default=0,
        ge=0,
    )

    start_time: datetime | None = None

    end_time: datetime | None = None

    production_line_id: int = Field(
        gt=0,
    )

    machine_id: int = Field(
        gt=0,
    )

    supervisor_id: int = Field(
        gt=0,
    )


class ProductionBatchUpdate(BaseModel):
    planned_quantity: int | None = Field(
        default=None,
        gt=0,
    )

    produced_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    rejected_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    start_time: datetime | None = None

    end_time: datetime | None = None

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    machine_id: int | None = Field(
        default=None,
        gt=0,
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionBatchResponse(BaseModel):
    id: int
    batch_number: str
    production_order_id: int
    planned_quantity: int
    produced_quantity: int
    rejected_quantity: int
    start_time: datetime | None
    end_time: datetime | None
    production_line_id: int
    machine_id: int
    supervisor_id: int
    completion_percentage: float
    rejection_percentage: float
    production_efficiency: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductionBatchListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductionBatchResponse]