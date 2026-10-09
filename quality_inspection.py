from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import UserRole
from database import get_db
from schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionListResponse,
    QualityInspectionResponse,
    QualityInspectionUpdate,
)
from services.quality_inspection_service import (
    QualityInspectionService,
)


router = APIRouter(
    prefix="/api/v1/quality-inspections",
    tags=["Quality Inspections"],
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
    response_model=QualityInspectionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_roles(*MANAGE_ROLES))
    ],
)
def create_quality_inspection(
    data: QualityInspectionCreate,
    db: Session = Depends(get_db),
):
    service = QualityInspectionService(db)

    return service.create_inspection(data)


@router.get(
    "",
    response_model=QualityInspectionListResponse,
    dependencies=[
        Depends(require_roles(*VIEW_ROLES))
    ],
)
def list_quality_inspections(
    search: Optional[str] = Query(
        default=None,
    ),
    inspection_type: Optional[str] = Query(
        default=None,
    ),
    result: Optional[str] = Query(
        default=None,
    ),
    production_batch_id: Optional[int] = Query(
        default=None,
        gt=0,
    ),
    inspector_id: Optional[int] = Query(
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
    service = QualityInspectionService(db)

    return service.list_inspections(
        search=search,
        inspection_type=inspection_type,
        result=result,
        production_batch_id=production_batch_id,
        inspector_id=inspector_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/{inspection_id}",
    response_model=QualityInspectionResponse,
    dependencies=[
        Depends(require_roles(*VIEW_ROLES))
    ],
)
def get_quality_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
):
    service = QualityInspectionService(db)

    return service.get_inspection(
        inspection_id
    )


@router.put(
    "/{inspection_id}",
    response_model=QualityInspectionResponse,
    dependencies=[
        Depends(require_roles(*MANAGE_ROLES))
    ],
)
def update_quality_inspection(
    inspection_id: int,
    data: QualityInspectionUpdate,
    db: Session = Depends(get_db),
):
    service = QualityInspectionService(db)

    return service.update_inspection(
        inspection_id,
        data,
    )


@router.delete(
    "/{inspection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_roles(*MANAGE_ROLES))
    ],
)
def delete_quality_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
):
    service = QualityInspectionService(db)

    service.delete_inspection(
        inspection_id
    )

    return None