from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from core.enums import (
    ProductionOrderPriority,
    ProductionOrderStatus,
    UserRole,
)
from database import get_db
from schemas.production_order import (
    ProductionOrderCreate,
    ProductionOrderListResponse,
    ProductionOrderResponse,
    ProductionOrderStatusUpdate,
    ProductionOrderUpdate,
)
from services.production_order_service import (
    ProductionOrderService,
)


router = APIRouter(
    prefix="/api/v1/production-orders",
    tags=["Production Orders"],
)


MANAGE_ORDER_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)


@router.post(
    "",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_production_order(
    data: ProductionOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ORDER_ROLES)
    ),
):
    service = ProductionOrderService(db)

    return service.create(data)


@router.get(
    "",
    response_model=ProductionOrderListResponse,
)
def list_production_orders(
    search: str | None = Query(
        default=None,
    ),
    product_id: int | None = Query(
        default=None,
        gt=0,
    ),
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    supervisor_id: int | None = Query(
        default=None,
        gt=0,
    ),
    priority: ProductionOrderPriority | None = Query(
        default=None,
    ),
    order_status: ProductionOrderStatus | None = Query(
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
    service = ProductionOrderService(db)

    total, items = service.list(
        search=search,
        product_id=product_id,
        production_line_id=production_line_id,
        supervisor_id=supervisor_id,
        priority=priority,
        status_value=order_status,
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
    "/{order_id}",
    response_model=ProductionOrderResponse,
)
def get_production_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductionOrderService(db)

    return service.get(order_id)


@router.put(
    "/{order_id}",
    response_model=ProductionOrderResponse,
)
def update_production_order(
    order_id: int,
    data: ProductionOrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ORDER_ROLES)
    ),
):
    service = ProductionOrderService(db)

    return service.update(
        order_id,
        data,
    )


@router.patch(
    "/{order_id}/status",
    response_model=ProductionOrderResponse,
)
def update_production_order_status(
    order_id: int,
    data: ProductionOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ORDER_ROLES)
    ),
):
    service = ProductionOrderService(db)

    return service.update_status(
        order_id,
        data.status,
    )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_production_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ORDER_ROLES)
    ),
):
    service = ProductionOrderService(db)

    service.delete(order_id)

    return None