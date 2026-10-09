from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import require_roles
from core.enums import UserRole
from database import get_db
from schemas.downtime import (
    DowntimeCreate,
    DowntimeListResponse,
    DowntimePercentageResponse,
    DowntimeResponse,
    DowntimeUpdate,
)
from services.downtime_service import DowntimeService


router = APIRouter(
    prefix="/api/v1/downtime",
    tags=["Downtime Management"],
)


VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PRODUCTION_SUPERVISOR,
]


MANAGE_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PRODUCTION_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PRODUCTION_SUPERVISOR,
]


@router.post(
    "",
    response_model=DowntimeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def create_downtime(
    data: DowntimeCreate,
    db: Session = Depends(get_db),
):
    service = DowntimeService(db)

    return service.create_downtime(data)


@router.get(
    "",
    response_model=DowntimeListResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def list_downtime(
    search: Optional[str] = Query(
        default=None
    ),
    category: Optional[str] = Query(
        default=None
    ),
    machine_id: Optional[int] = Query(
        default=None,
        gt=0,
    ),
    production_line_id: Optional[int] = Query(
        default=None,
        gt=0,
    ),
    responsible_person_id: Optional[int] = Query(
        default=None,
        gt=0,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    service = DowntimeService(db)

    return service.list_downtime(
        search=search,
        category=category,
        machine_id=machine_id,
        production_line_id=production_line_id,
        responsible_person_id=(
            responsible_person_id
        ),
        page=page,
        limit=limit,
    )


@router.get(
    "/percentage",
    response_model=DowntimePercentageResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def calculate_downtime_percentage(
    machine_id: int = Query(
        ...,
        gt=0,
    ),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db),
):
    service = DowntimeService(db)

    return service.calculate_downtime_percentage(
        machine_id=machine_id,
        start_time=start_time,
        end_time=end_time,
    )


@router.get(
    "/{downtime_id}",
    response_model=DowntimeResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_downtime(
    downtime_id: int,
    db: Session = Depends(get_db),
):
    service = DowntimeService(db)

    return service.get_downtime(
        downtime_id
    )


@router.put(
    "/{downtime_id}",
    response_model=DowntimeResponse,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def update_downtime(
    downtime_id: int,
    data: DowntimeUpdate,
    db: Session = Depends(get_db),
):
    service = DowntimeService(db)

    return service.update_downtime(
        downtime_id,
        data,
    )


@router.delete(
    "/{downtime_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def delete_downtime(
    downtime_id: int,
    db: Session = Depends(get_db),
):
    service = DowntimeService(db)

    service.delete_downtime(
        downtime_id
    )

    return None