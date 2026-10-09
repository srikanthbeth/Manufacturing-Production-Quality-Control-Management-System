from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from core.enums import UserRole
from database import get_db
from models.user import User
from schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementListResponse,
    InventoryMovementResponse,
    InventoryStockResponse,
    InventoryTransactionHistoryResponse,
)
from services.inventory_movement_service import (
    InventoryMovementService,
)


router = APIRouter(
    prefix="/api/v1/inventory-movements",
    tags=["Inventory Movement"],
)


VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
]


MANAGE_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PRODUCTION_MANAGER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
]


@router.post(
    "",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(*MANAGE_ROLES)
        )
    ],
)
def create_inventory_movement(
    data: InventoryMovementCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = InventoryMovementService(db)

    return service.create_movement(
        data=data,
        created_by_id=current_user.id,
    )


@router.get(
    "",
    response_model=InventoryMovementListResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def list_inventory_movements(
    search: Optional[str] = Query(
        default=None
    ),
    movement_type: Optional[str] = Query(
        default=None
    ),
    raw_material_id: Optional[int] = Query(
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
    service = InventoryMovementService(db)

    return service.list_movements(
        search=search,
        movement_type=movement_type,
        raw_material_id=raw_material_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/stock/{raw_material_id}",
    response_model=InventoryStockResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_inventory_stock(
    raw_material_id: int,
    db: Session = Depends(get_db),
):
    service = InventoryMovementService(db)

    return service.get_stock(
        raw_material_id
    )


@router.get(
    "/history/{raw_material_id}",
    response_model=InventoryTransactionHistoryResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_transaction_history(
    raw_material_id: int,
    db: Session = Depends(get_db),
):
    service = InventoryMovementService(db)

    return service.get_transaction_history(
        raw_material_id
    )


@router.get(
    "/{movement_id}",
    response_model=InventoryMovementResponse,
    dependencies=[
        Depends(
            require_roles(*VIEW_ROLES)
        )
    ],
)
def get_inventory_movement(
    movement_id: int,
    db: Session = Depends(get_db),
):
    service = InventoryMovementService(db)

    return service.get_movement(
        movement_id
    )