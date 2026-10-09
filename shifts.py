from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.dependencies import require_roles
from core.enums import UserRole
from database import get_db

from schemas.shift import (
    ShiftCreate,
    ShiftListResponse,
    ShiftMachineUsageCreate,
    ShiftMachineUsageResponse,
    ShiftPerformanceResponse,
    ShiftProductionOutputCreate,
    ShiftProductionOutputResponse,
    ShiftResponse,
    ShiftUpdate,
    ShiftWorkerResponse,
)

from services.shift_service import ShiftService


router = APIRouter(
    prefix="/api/v1/shifts",
    tags=["Shifts"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
]


DELETE_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PRODUCTION_MANAGER,
]


@router.post(
    "",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shift(
    data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = ShiftService(db)

    return service.create_shift(data)


@router.get(
    "",
    response_model=ShiftListResponse,
)
def list_shifts(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    items, total = service.list_shifts(
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/{shift_id}",
    response_model=ShiftResponse,
)
def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    return service.get_shift(shift_id)


@router.put(
    "/{shift_id}",
    response_model=ShiftResponse,
)
def update_shift(
    shift_id: int,
    data: ShiftUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = ShiftService(db)

    return service.update_shift(
        shift_id,
        data,
    )


@router.delete(
    "/{shift_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*DELETE_ROLES)
    ),
):
    service = ShiftService(db)

    service.delete_shift(shift_id)

    return None


@router.post(
    "/{shift_id}/workers/{worker_id}",
    response_model=ShiftWorkerResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_worker(
    shift_id: int,
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = ShiftService(db)

    return service.assign_worker(
        shift_id,
        worker_id,
    )


@router.delete(
    "/{shift_id}/workers/{worker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_worker(
    shift_id: int,
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = ShiftService(db)

    service.remove_worker(
        shift_id,
        worker_id,
    )

    return None


@router.get(
    "/{shift_id}/workers",
    response_model=list[ShiftWorkerResponse],
)
def get_shift_workers(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    return service.get_shift_workers(
        shift_id
    )


@router.get(
    "/workers/{worker_id}/shifts",
    response_model=list[ShiftWorkerResponse],
)
def get_worker_shifts(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    return service.get_worker_shifts(
        worker_id
    )


@router.post(
    "/{shift_id}/production-output",
    response_model=ShiftProductionOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_production_output(
    shift_id: int,
    data: ShiftProductionOutputCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = ShiftService(db)

    return service.record_production_output(
        shift_id,
        data,
    )


@router.get(
    "/{shift_id}/production-output",
    response_model=list[ShiftProductionOutputResponse],
)
def get_production_output(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    return service.get_production_output(
        shift_id
    )


@router.post(
    "/{shift_id}/machine-usage",
    response_model=ShiftMachineUsageResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_machine_usage(
    shift_id: int,
    data: ShiftMachineUsageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = ShiftService(db)

    return service.record_machine_usage(
        shift_id,
        data,
    )


@router.get(
    "/{shift_id}/machine-usage",
    response_model=list[ShiftMachineUsageResponse],
)
def get_machine_usage(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    return service.get_machine_usage(
        shift_id
    )


@router.get(
    "/{shift_id}/performance",
    response_model=ShiftPerformanceResponse,
)
def get_shift_performance(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShiftService(db)

    return service.get_performance(
        shift_id
    )