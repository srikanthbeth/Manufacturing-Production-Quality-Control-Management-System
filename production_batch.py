from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import UserRole
from database import get_db
from schemas.production_batch import (
    ProductionBatchCreate,
    ProductionBatchListResponse,
    ProductionBatchResponse,
    ProductionBatchUpdate,
)
from services.production_batch_service import (
    ProductionBatchService,
)


router = APIRouter(
    prefix="/api/v1/production-batches",
    tags=["Production Batches"],
)


MANAGE_BATCH_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


@router.post(
    "",
    response_model=ProductionBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_production_batch(
    payload: ProductionBatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_BATCH_ROLES)
    ),
):
    service = ProductionBatchService(db)

    return service.create(
        batch_number=payload.batch_number,
        production_order_id=payload.production_order_id,
        planned_quantity=payload.planned_quantity,
        produced_quantity=payload.produced_quantity,
        rejected_quantity=payload.rejected_quantity,
        start_time=payload.start_time,
        end_time=payload.end_time,
        production_line_id=payload.production_line_id,
        machine_id=payload.machine_id,
        supervisor_id=payload.supervisor_id,
    )


@router.get(
    "",
    response_model=ProductionBatchListResponse,
)
def list_production_batches(
    search: str | None = None,
    production_order_id: int | None = Query(
        default=None,
        gt=0,
    ),
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    machine_id: int | None = Query(
        default=None,
        gt=0,
    ),
    supervisor_id: int | None = Query(
        default=None,
        gt=0,
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
    service = ProductionBatchService(db)

    total, items = service.list(
        search=search,
        production_order_id=production_order_id,
        production_line_id=production_line_id,
        machine_id=machine_id,
        supervisor_id=supervisor_id,
        page=page,
        page_size=page_size,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get(
    "/{batch_id}",
    response_model=ProductionBatchResponse,
)
def get_production_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductionBatchService(db)

    return service.get(batch_id)


@router.put(
    "/{batch_id}",
    response_model=ProductionBatchResponse,
)
def update_production_batch(
    batch_id: int,
    payload: ProductionBatchUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_BATCH_ROLES)
    ),
):
    service = ProductionBatchService(db)

    return service.update(
        batch_id=batch_id,
        planned_quantity=payload.planned_quantity,
        produced_quantity=payload.produced_quantity,
        rejected_quantity=payload.rejected_quantity,
        start_time=payload.start_time,
        end_time=payload.end_time,
        production_line_id=payload.production_line_id,
        machine_id=payload.machine_id,
        supervisor_id=payload.supervisor_id,
    )


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_production_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_BATCH_ROLES)
    ),
):
    service = ProductionBatchService(db)

    service.delete(batch_id)

    return None