from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)
from core.enums import ProductStatus, UserRole
from database import get_db
from schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from services.product_service import ProductService


router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = ProductService(db)

    return service.create(data)


@router.get(
    "",
    response_model=ProductListResponse,
)
def list_products(
    search: str | None = Query(
        default=None,
    ),
    category: str | None = Query(
        default=None,
    ),
    status_value: ProductStatus | None = Query(
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
    service = ProductService(db)

    return service.list(
        search=search,
        category=category,
        status_value=status_value,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db)

    return service.get_by_id(product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = ProductService(db)

    return service.update(
        product_id,
        data,
    )


@router.patch(
    "/{product_id}/status",
    response_model=ProductResponse,
)
def update_product_status(
    product_id: int,
    status_value: ProductStatus,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = ProductService(db)

    return service.update_status(
        product_id,
        status_value,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
        )
    ),
):
    service = ProductService(db)

    service.delete(product_id)

    return None