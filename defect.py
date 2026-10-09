from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import require_roles
from core.enums import UserRole
from database import get_db
from schemas.defect import (
    DefectCreate,
    DefectListResponse,
    DefectResponse,
    DefectUpdate,
)
from services.defect_service import DefectService


router = APIRouter(
    prefix="/api/v1/defects",
    tags=["Defects"],
)


VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.QUALITY_MANAGER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
]


MANAGE_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.QUALITY_MANAGER,
]


@router.post(
    "",
    response_model=DefectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def create_defect(
    data: DefectCreate,
    db: Session = Depends(get_db),
):
    service = DefectService(db)

    return service.create_defect(data)


@router.get(
    "",
    response_model=DefectListResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def list_defects(
    search: Optional[str] = Query(
        default=None
    ),
    defect_type: Optional[str] = Query(
        default=None
    ),
    severity: Optional[str] = Query(
        default=None
    ),
    resolution_status: Optional[str] = Query(
        default=None
    ),
    production_batch_id: Optional[int] = Query(
        default=None,
        gt=0,
    ),
    product_id: Optional[int] = Query(
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
    service = DefectService(db)

    return service.list_defects(
        search=search,
        defect_type=defect_type,
        severity=severity,
        resolution_status=resolution_status,
        production_batch_id=production_batch_id,
        product_id=product_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/{defect_id}",
    response_model=DefectResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_defect(
    defect_id: int,
    db: Session = Depends(get_db),
):
    service = DefectService(db)

    return service.get_defect(
        defect_id
    )


@router.put(
    "/{defect_id}",
    response_model=DefectResponse,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def update_defect(
    defect_id: int,
    data: DefectUpdate,
    db: Session = Depends(get_db),
):
    service = DefectService(db)

    return service.update_defect(
        defect_id,
        data,
    )


@router.delete(
    "/{defect_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def delete_defect(
    defect_id: int,
    db: Session = Depends(get_db),
):
    service = DefectService(db)

    service.delete_defect(
        defect_id
    )

    return None