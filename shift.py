from datetime import datetime
from datetime import time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ShiftCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50,
    )

    start_time: time

    end_time: time

    description: Optional[str] = None

    is_active: bool = True


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    start_time: Optional[time] = None

    end_time: Optional[time] = None

    description: Optional[str] = None

    is_active: Optional[bool] = None


class ShiftResponse(BaseModel):
    id: int
    name: str
    start_time: time
    end_time: time
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ShiftListResponse(BaseModel):
    items: list[ShiftResponse]
    total: int
    page: int
    page_size: int


class ShiftWorkerResponse(BaseModel):
    id: int
    shift_id: int
    worker_id: int
    assigned_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ShiftProductionOutputCreate(BaseModel):
    production_batch_id: int = Field(gt=0)

    produced_quantity: Decimal = Field(
        gt=0
    )

    rejected_quantity: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )


class ShiftProductionOutputResponse(BaseModel):
    id: int
    shift_id: int
    production_batch_id: int
    produced_quantity: Decimal
    rejected_quantity: Decimal
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ShiftMachineUsageCreate(BaseModel):
    machine_id: int = Field(gt=0)

    usage_hours: Decimal = Field(
        gt=0
    )

    downtime_hours: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    notes: Optional[str] = None


class ShiftMachineUsageResponse(BaseModel):
    id: int
    shift_id: int
    machine_id: int
    usage_hours: Decimal
    downtime_hours: Decimal
    notes: Optional[str]
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ShiftPerformanceResponse(BaseModel):
    shift_id: int
    shift_name: str
    worker_count: int
    total_produced_quantity: Decimal
    total_rejected_quantity: Decimal
    total_machine_usage_hours: Decimal
    total_machine_downtime_hours: Decimal
    production_efficiency: float
    output_per_worker: float