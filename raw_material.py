from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import MaterialStatus, UserRole
from database import get_db
from schemas.raw_material import (
    MaterialAdjustmentRequest,
    MaterialHistoryResponse,
    MaterialStockRequest,
    MaterialTransactionResponse,
    RawMaterialCreate,
    RawMaterialListResponse,
    RawMaterialResponse,
    RawMaterialUpdate,
)
from services.raw_material_service import RawMaterialService


router = APIRouter(
    prefix="/api/v1/raw-materials",
    tags=["Raw Materials"],
)


# ============================================================
# MATERIAL MASTER
# ============================================================


@router.post(
    "",
    response_model=RawMaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_raw_material(
    data: RawMaterialCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = RawMaterialService(db)

    return service.create(data)


@router.get(
    "",
    response_model=RawMaterialListResponse,
)
def list_raw_materials(
    search: str | None = Query(
        default=None,
    ),
    category: str | None = Query(
        default=None,
    ),
    status_value: MaterialStatus | None = Query(
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
    service = RawMaterialService(db)

    return service.list(
        search=search,
        category=category,
        status_value=status_value,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{material_id}",
    response_model=RawMaterialResponse,
)
def get_raw_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RawMaterialService(db)

    return service.get_by_id(material_id)


@router.put(
    "/{material_id}",
    response_model=RawMaterialResponse,
)
def update_raw_material(
    material_id: int,
    data: RawMaterialUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = RawMaterialService(db)

    return service.update(
        material_id,
        data,
    )


@router.patch(
    "/{material_id}/status",
    response_model=RawMaterialResponse,
)
def update_raw_material_status(
    material_id: int,
    status_value: MaterialStatus,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = RawMaterialService(db)

    return service.update_status(
        material_id,
        status_value,
    )


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_raw_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = RawMaterialService(db)

    service.delete(material_id)

    return None


# ============================================================
# STOCK-IN
# ============================================================


@router.post(
    "/{material_id}/stock-in",
    response_model=RawMaterialResponse,
)
def stock_in(
    material_id: int,
    data: MaterialStockRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
        )
    ),
):
    service = RawMaterialService(db)

    return service.stock_in(
        material_id=material_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# STOCK-OUT
# ============================================================


@router.post(
    "/{material_id}/stock-out",
    response_model=RawMaterialResponse,
)
def stock_out(
    material_id: int,
    data: MaterialStockRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
        )
    ),
):
    service = RawMaterialService(db)

    return service.stock_out(
        material_id=material_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# MATERIAL ADJUSTMENT
# ============================================================


@router.post(
    "/{material_id}/adjustment",
    response_model=RawMaterialResponse,
)
def material_adjustment(
    material_id: int,
    data: MaterialAdjustmentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = RawMaterialService(db)

    return service.adjustment(
        material_id=material_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# MATERIAL USAGE / TRANSACTION HISTORY
# ============================================================


@router.get(
    "/{material_id}/history",
    response_model=MaterialHistoryResponse,
)
def material_history(
    material_id: int,
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
    service = RawMaterialService(db)

    return service.history(
        material_id=material_id,
        page=page,
        page_size=page_size,
    )