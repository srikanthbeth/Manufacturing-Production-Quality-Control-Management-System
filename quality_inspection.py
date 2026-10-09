from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InspectionType(str, Enum):
    INCOMING_MATERIAL = "Incoming Material Inspection"
    IN_PROCESS = "In-Process Inspection"
    FINAL_PRODUCT = "Final Product Inspection"


class InspectionResult(str, Enum):
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"


class QualityInspectionBase(BaseModel):
    inspection_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    inspection_type: InspectionType

    inspector_id: int = Field(
        ...,
        gt=0,
    )

    production_batch_id: int = Field(
        ...,
        gt=0,
    )

    inspection_date: datetime

    parameters: str = Field(
        ...,
        min_length=1,
    )

    expected_value: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    actual_value: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    result: InspectionResult = InspectionResult.PENDING

    remarks: Optional[str] = None


class QualityInspectionCreate(QualityInspectionBase):
    pass


class QualityInspectionUpdate(BaseModel):
    inspection_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    inspection_type: Optional[InspectionType] = None

    inspector_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    production_batch_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    inspection_date: Optional[datetime] = None

    parameters: Optional[str] = Field(
        default=None,
        min_length=1,
    )

    expected_value: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    actual_value: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    result: Optional[InspectionResult] = None

    remarks: Optional[str] = None


class QualityInspectionResponse(QualityInspectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class QualityInspectionListResponse(BaseModel):
    items: list[QualityInspectionResponse]
    total: int
    page: int
    limit: int
    pages: int