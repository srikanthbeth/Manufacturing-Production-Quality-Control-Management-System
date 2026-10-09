from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DefectSeverity(str, Enum):
    MINOR = "Minor"
    MAJOR = "Major"
    CRITICAL = "Critical"


class ResolutionStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class DefectBase(BaseModel):
    defect_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    defect_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    severity: DefectSeverity

    production_batch_id: int = Field(
        ...,
        gt=0,
    )

    product_id: int = Field(
        ...,
        gt=0,
    )

    quantity_affected: int = Field(
        ...,
        gt=0,
    )

    root_cause: str = Field(
        ...,
        min_length=1,
    )

    corrective_action: Optional[str] = None

    resolution_status: ResolutionStatus = (
        ResolutionStatus.OPEN
    )


class DefectCreate(DefectBase):
    pass


class DefectUpdate(BaseModel):
    defect_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    defect_type: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    severity: Optional[DefectSeverity] = None

    production_batch_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    product_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    quantity_affected: Optional[int] = Field(
        default=None,
        gt=0,
    )

    root_cause: Optional[str] = Field(
        default=None,
        min_length=1,
    )

    corrective_action: Optional[str] = None

    resolution_status: Optional[ResolutionStatus] = None


class DefectResponse(DefectBase):
    id: int
    created_at: object
    updated_at: object

    model_config = ConfigDict(
        from_attributes=True
    )


class DefectListResponse(BaseModel):
    items: list[DefectResponse]
    total: int
    page: int
    limit: int
    pages: int