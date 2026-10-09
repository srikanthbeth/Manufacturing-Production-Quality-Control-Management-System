from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class WorkerCreate(BaseModel):
    user_id: int = Field(gt=0)
    employee_code: str = Field(
        min_length=2,
        max_length=50,
    )
    skill: str = Field(
        min_length=2,
        max_length=150,
    )
    department: str = Field(
        min_length=2,
        max_length=150,
    )
    shift: str = Field(
        min_length=2,
        max_length=50,
    )
    production_line_id: Optional[int] = Field(
        default=None,
        gt=0,
    )
    status: str = Field(
        default="Active",
        min_length=2,
        max_length=50,
    )
    profile_description: Optional[str] = None


class WorkerUpdate(BaseModel):
    employee_code: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    skill: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    department: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    shift: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    production_line_id: Optional[int] = Field(
        default=None,
        gt=0,
    )
    status: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    profile_description: Optional[str] = None


class WorkerResponse(BaseModel):
    id: int
    user_id: int
    employee_code: str
    skill: str
    department: str
    shift: str
    production_line_id: Optional[int]
    status: str
    profile_description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class WorkerListResponse(BaseModel):
    items: list[WorkerResponse]
    total: int
    page: int
    page_size: int


class WorkerBatchAssignmentResponse(BaseModel):
    id: int
    worker_id: int
    production_batch_id: int
    assigned_at: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )