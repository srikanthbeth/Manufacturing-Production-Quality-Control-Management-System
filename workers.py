from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from core.dependencies import get_current_user, require_roles
from core.enums import UserRole
from schemas.worker import (
    WorkerCreate,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdate,
    WorkerBatchAssignmentResponse,
)
from services.worker_service import WorkerService


router = APIRouter(
    prefix="/api/v1/workers",
    tags=["Workers"],
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
    response_model=WorkerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_worker(
    data: WorkerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = WorkerService(db)

    return service.create_worker(data)


@router.get(
    "",
    response_model=WorkerListResponse,
)
def list_workers(
    search: str | None = Query(default=None),
    department: str | None = Query(default=None),
    shift: str | None = Query(default=None),
    status: str | None = Query(default=None),
    production_line_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = WorkerService(db)

    items, total = service.list_workers(
        search=search,
        department=department,
        shift=shift,
        status=status,
        production_line_id=production_line_id,
        page=page,
        page_size=page_size,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/{worker_id}/batches/{production_batch_id}",
    response_model=WorkerBatchAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_worker_to_batch(
    worker_id: int,
    production_batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = WorkerService(db)

    return service.assign_worker_to_batch(
        worker_id,
        production_batch_id,
    )


@router.delete(
    "/{worker_id}/batches/{production_batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_worker_from_batch(
    worker_id: int,
    production_batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = WorkerService(db)

    service.remove_worker_from_batch(
        worker_id,
        production_batch_id,
    )

    return None


@router.get(
    "/batch/{production_batch_id}",
    response_model=list[WorkerBatchAssignmentResponse],
)
def get_batch_workers(
    production_batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = WorkerService(db)

    return service.get_batch_workers(
        production_batch_id
    )


@router.get(
    "/{worker_id}/batches",
    response_model=list[WorkerBatchAssignmentResponse],
)
def get_worker_batches(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = WorkerService(db)

    return service.get_worker_batches(
        worker_id
    )


@router.get(
    "/{worker_id}",
    response_model=WorkerResponse,
)
def get_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = WorkerService(db)

    return service.get_worker(worker_id)


@router.put(
    "/{worker_id}",
    response_model=WorkerResponse,
)
def update_worker(
    worker_id: int,
    data: WorkerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = WorkerService(db)

    return service.update_worker(
        worker_id,
        data,
    )


@router.delete(
    "/{worker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*DELETE_ROLES)
    ),
):
    service = WorkerService(db)

    service.delete_worker(worker_id)

    return None