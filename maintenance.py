from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from core.dependencies import require_roles
from core.enums import UserRole
from database import get_db
from schemas.maintenance import (
    MaintenanceAlertListResponse,
    MaintenanceCreate,
    MaintenanceListResponse,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from services.maintenance_service import (
    MaintenanceService,
)


router = APIRouter(
    prefix="/api/v1/maintenance",
    tags=["Machine Maintenance"],
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
    UserRole.MAINTENANCE_ENGINEER,
]


@router.post(
    "",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def create_maintenance(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)

    return service.create_maintenance(
        data
    )


@router.get(
    "",
    response_model=MaintenanceListResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def list_maintenance(
    search: Optional[str] = Query(
        default=None
    ),
    maintenance_type: Optional[str] = Query(
        default=None
    ),
    maintenance_status: Optional[str] = Query(
        default=None
    ),
    machine_id: Optional[int] = Query(
        default=None,
        gt=0,
    ),
    technician_id: Optional[int] = Query(
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
    service = MaintenanceService(db)

    return service.list_maintenance(
        search=search,
        maintenance_type=maintenance_type,
        maintenance_status=(
            maintenance_status
        ),
        machine_id=machine_id,
        technician_id=technician_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/alerts/due",
    response_model=MaintenanceAlertListResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_due_maintenance_alerts(
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)

    alerts = service.get_due_alerts()

    return {
        "items": alerts,
        "total": len(alerts),
    }


@router.get(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)

    return service.get_maintenance(
        maintenance_id
    )


@router.put(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def update_maintenance(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)

    return service.update_maintenance(
        maintenance_id,
        data,
    )


@router.delete(
    "/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)

    service.delete_maintenance(
        maintenance_id
    )

    return None