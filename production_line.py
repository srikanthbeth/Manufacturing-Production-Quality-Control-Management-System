from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import ProductionLineStatus, UserRole
from database import get_db
from models.user import User
from schemas.production_line import (
    ProductionLineCreate,
    ProductionLineListResponse,
    ProductionLineResponse,
    ProductionLineUpdate,
)
from services.production_line_service import (
    ProductionLineService,
)


router = APIRouter(
    prefix="/api/v1/production-lines",
    tags=["Production Lines"],
)


@router.post(
    "",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_production_line(
    data: ProductionLineCreate,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.create(
        name=data.name,
        code=data.code,
        production_capacity=data.production_capacity,
        plant_id=data.plant_id,
        status_value=data.status,
        supervisor_id=data.supervisor_id,
    )


@router.get(
    "",
    response_model=ProductionLineListResponse,
)
def list_production_lines(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    plant_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status_value: ProductionLineStatus | None = Query(
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.list_lines(
        search=search,
        plant_id=plant_id,
        status_value=status_value,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{line_id}",
    response_model=ProductionLineResponse,
)
def get_production_line(
    line_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.get_by_id(line_id)


@router.put(
    "/{line_id}",
    response_model=ProductionLineResponse,
)
def update_production_line(
    line_id: int,
    data: ProductionLineUpdate,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.update(
        line_id=line_id,
        data=data,
    )


@router.patch(
    "/{line_id}/status",
    response_model=ProductionLineResponse,
)
def update_production_line_status(
    line_id: int,
    status_value: ProductionLineStatus,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.update_status(
        line_id=line_id,
        status_value=status_value,
    )


@router.patch(
    "/{line_id}/supervisor/{supervisor_id}",
    response_model=ProductionLineResponse,
)
def assign_supervisor(
    line_id: int,
    supervisor_id: int,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.assign_supervisor(
        line_id=line_id,
        supervisor_id=supervisor_id,
    )


@router.delete(
    "/{line_id}/supervisor",
    response_model=ProductionLineResponse,
)
def remove_supervisor(
    line_id: int,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.remove_supervisor(
        line_id=line_id
    )


@router.delete(
    "/{line_id}",
)
def delete_production_line(
    line_id: int,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ProductionLineService(db)

    return service.delete(line_id)