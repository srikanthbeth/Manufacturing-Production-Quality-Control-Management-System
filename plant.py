from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import PlantStatus


class PlantCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=50,
    )

    address: str = Field(
        min_length=3,
        max_length=500,
    )

    city: str = Field(
        min_length=2,
        max_length=100,
    )

    state: str = Field(
        min_length=2,
        max_length=100,
    )

    country: str = Field(
        min_length=2,
        max_length=100,
        default="India",
    )

    production_capacity: int = Field(
        gt=0,
    )

    status: PlantStatus = PlantStatus.ACTIVE

    manager_id: int | None = Field(
        default=None,
        gt=0,
    )


class PlantUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    address: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    production_capacity: int | None = Field(
        default=None,
        gt=0,
    )

    status: PlantStatus | None = None

    manager_id: int | None = Field(
        default=None,
        gt=0,
    )


class PlantResponse(BaseModel):
    id: int
    name: str
    code: str
    address: str
    city: str
    state: str
    country: str
    production_capacity: int
    status: PlantStatus
    manager_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )