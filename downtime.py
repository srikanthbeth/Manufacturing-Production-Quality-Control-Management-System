from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DowntimeCategory(str, Enum):
    MACHINE_BREAKDOWN = "Machine Breakdown"
    MATERIAL_SHORTAGE = "Material Shortage"
    QUALITY_ISSUE = "Quality Issue"
    POWER_FAILURE = "Power Failure"
    MAINTENANCE = "Maintenance"
    OPERATOR_ISSUE = "Operator Issue"


class DowntimeBase(BaseModel):
    downtime_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    machine_id: int = Field(
        ...,
        gt=0,
    )

    production_line_id: int = Field(
        ...,
        gt=0,
    )

    responsible_person_id: int = Field(
        ...,
        gt=0,
    )

    category: DowntimeCategory

    reason: str = Field(
        ...,
        min_length=1,
    )

    start_time: datetime

    end_time: Optional[datetime] = None


class DowntimeCreate(DowntimeBase):
    pass


class DowntimeUpdate(BaseModel):
    downtime_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    machine_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    production_line_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    responsible_person_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    category: Optional[DowntimeCategory] = None

    reason: Optional[str] = Field(
        default=None,
        min_length=1,
    )

    start_time: Optional[datetime] = None

    end_time: Optional[datetime] = None


class DowntimeResponse(DowntimeBase):
    id: int
    duration_minutes: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class DowntimeListResponse(BaseModel):
    items: list[DowntimeResponse]
    total: int
    page: int
    limit: int
    pages: int


class DowntimePercentageResponse(BaseModel):
    machine_id: int
    start_time: datetime
    end_time: datetime
    total_available_minutes: Decimal
    total_downtime_minutes: Decimal
    downtime_percentage: Decimal