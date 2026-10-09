from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import MachineStatus, UserRole
from database import get_db
from schemas.machine import (
    MachineCreate,
    MachineResponse,
    MachineStatusUpdate,
    MachineUpdate,
)
from services.machine_service import MachineService


router = APIRouter(
    prefix="/api/v1/machines",
    tags=["Machines"],
)


MANAGE_MACHINE_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PRODUCTION_MANAGER,
)


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_machine(
    data: MachineCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_MACHINE_ROLES)
    ),
):
    service = MachineService(db)

    return service.create(data)


@router.get(
    "",
)
def list_machines(
    search: str | None = Query(
        default=None,
    ),
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    machine_status: MachineStatus | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MachineService(db)

    return service.list(
        search=search,
        production_line_id=production_line_id,
        status=machine_status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MachineService(db)

    return service.get(machine_id)


@router.get(
    "/production-line/{production_line_id}",
    response_model=list[MachineResponse],
)
def get_machines_by_production_line(
    production_line_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MachineService(db)

    return service.get_by_production_line(
        production_line_id
    )


@router.put(
    "/{machine_id}",
    response_model=MachineResponse,
)
def update_machine(
    machine_id: int,
    data: MachineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_MACHINE_ROLES)
    ),
):
    service = MachineService(db)

    return service.update(
        machine_id,
        data,
    )


@router.patch(
    "/{machine_id}/status",
    response_model=MachineResponse,
)
def update_machine_status(
    machine_id: int,
    data: MachineStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_MACHINE_ROLES)
    ),
):
    service = MachineService(db)

    return service.update_status(
        machine_id,
        data,
    )


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_MACHINE_ROLES)
    ),
):
    service = MachineService(db)

    service.delete(machine_id)

    return None