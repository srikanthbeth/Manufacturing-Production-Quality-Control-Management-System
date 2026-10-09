from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import MachineStatus


class MachineCreate(BaseModel):
    machine_code: str = Field(
        min_length=1,
        max_length=100,
    )

    machine_type: str = Field(
        min_length=1,
        max_length=150,
    )

    production_line_id: int = Field(
        gt=0,
    )

    installation_date: date

    status: MachineStatus = MachineStatus.IDLE

    operating_hours: float = Field(
        default=0,
        ge=0,
    )


class MachineUpdate(BaseModel):
    machine_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    installation_date: date | None = None

    operating_hours: float | None = Field(
        default=None,
        ge=0,
    )


class MachineStatusUpdate(BaseModel):
    status: MachineStatus


class MachineResponse(BaseModel):
    id: int
    machine_code: str
    machine_type: str
    production_line_id: int
    installation_date: date
    status: MachineStatus
    operating_hours: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class MachineListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MachineResponse]