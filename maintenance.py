from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceType(str, Enum):
    PREVENTIVE = "Preventive"
    BREAKDOWN = "Breakdown"


class MaintenanceStatus(str, Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class AlertStatus(str, Enum):
    YES = "Yes"
    NO = "No"


class SparePartUsage(BaseModel):
    part_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    quantity: int = Field(
        ...,
        gt=0,
    )

    unit_cost: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )


class MaintenanceBase(BaseModel):
    maintenance_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    machine_id: int = Field(
        ...,
        gt=0,
    )

    maintenance_type: MaintenanceType

    maintenance_status: MaintenanceStatus = (
        MaintenanceStatus.SCHEDULED
    )

    scheduled_date: datetime

    completed_date: Optional[datetime] = None

    next_due_date: Optional[datetime] = None

    technician_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    issue_description: Optional[str] = None

    maintenance_description: str = Field(
        ...,
        min_length=1,
    )

    root_cause: Optional[str] = None

    corrective_action: Optional[str] = None

    spare_parts_used: Optional[
        list[SparePartUsage]
    ] = None

    maintenance_cost: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    maintenance_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    machine_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    maintenance_type: Optional[MaintenanceType] = None

    maintenance_status: Optional[
        MaintenanceStatus
    ] = None

    scheduled_date: Optional[datetime] = None

    completed_date: Optional[datetime] = None

    next_due_date: Optional[datetime] = None

    technician_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    issue_description: Optional[str] = None

    maintenance_description: Optional[str] = Field(
        default=None,
        min_length=1,
    )

    root_cause: Optional[str] = None

    corrective_action: Optional[str] = None

    spare_parts_used: Optional[
        list[SparePartUsage]
    ] = None

    maintenance_cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
    )


class MaintenanceResponse(MaintenanceBase):
    id: int
    alert_sent: AlertStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class MaintenanceListResponse(BaseModel):
    items: list[MaintenanceResponse]
    total: int
    page: int
    limit: int
    pages: int


class MaintenanceAlertResponse(BaseModel):
    id: int
    maintenance_number: str
    machine_id: int
    maintenance_type: MaintenanceType
    scheduled_date: datetime
    next_due_date: Optional[datetime]
    maintenance_status: MaintenanceStatus
    technician_id: Optional[int]
    alert_message: str

    model_config = ConfigDict(
        from_attributes=True
    )


class MaintenanceAlertListResponse(BaseModel):
    items: list[MaintenanceAlertResponse]
    total: int