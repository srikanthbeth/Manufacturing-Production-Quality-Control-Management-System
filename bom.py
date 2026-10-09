from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.enums import UserRole
from database import get_db
from schemas.bom import (
    BOMCreate,
    BOMItemCreate,
    BOMItemResponse,
    BOMItemUpdate,
    BOMListResponse,
    BOMResponse,
    BOMUpdate,
)
from services.bom_service import BOMService


router = APIRouter(
    prefix="/api/v1/boms",
    tags=["Bill of Materials"],
)


MANAGER_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
}


def check_bom_permission(current_user):
    if current_user.role not in MANAGER_ROLES:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage BOMs",
        )


def build_bom_response(bom):
    return BOMResponse(
        id=bom.id,
        product_id=bom.product_id,
        version=bom.version,
        description=bom.description,
        is_active=bom.is_active,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
        items=[
            BOMItemResponse.model_validate(item)
            for item in bom.items
        ],
    )


@router.post(
    "",
    response_model=BOMResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bom(
    data: BOMCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    bom = service.create_bom(data)

    return build_bom_response(bom)


@router.get(
    "",
    response_model=list[BOMListResponse],
)
def list_boms(
    product_id: int | None = Query(
        default=None,
        gt=0,
    ),
    is_active: bool | None = None,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BOMService(db)

    skip = (page - 1) * page_size

    return service.list_boms(
        skip=skip,
        limit=page_size,
        product_id=product_id,
        is_active=is_active,
    )


@router.get(
    "/product/{product_id}",
    response_model=list[BOMListResponse],
)
def list_product_boms(
    product_id: int,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BOMService(db)

    skip = (page - 1) * page_size

    return service.list_boms(
        skip=skip,
        limit=page_size,
        product_id=product_id,
    )


@router.get(
    "/{bom_id}",
    response_model=BOMResponse,
)
def get_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BOMService(db)

    bom = service.get_bom(bom_id)

    return build_bom_response(bom)


@router.put(
    "/{bom_id}",
    response_model=BOMResponse,
)
def update_bom(
    bom_id: int,
    data: BOMUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    bom = service.update_bom(
        bom_id,
        data,
    )

    return build_bom_response(bom)


@router.post(
    "/{bom_id}/items",
    response_model=BOMItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_bom_item(
    bom_id: int,
    data: BOMItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    return service.add_item(
        bom_id,
        data,
    )


@router.put(
    "/{bom_id}/items/{item_id}",
    response_model=BOMItemResponse,
)
def update_bom_item(
    bom_id: int,
    item_id: int,
    data: BOMItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    return service.update_item(
        bom_id,
        item_id,
        data,
    )


@router.delete(
    "/{bom_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_bom_item(
    bom_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    service.remove_item(
        bom_id,
        item_id,
    )

    return None


@router.post(
    "/{bom_id}/activate",
    response_model=BOMResponse,
)
def activate_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    bom = service.activate_bom(bom_id)

    return build_bom_response(bom)


@router.post(
    "/{bom_id}/deactivate",
    response_model=BOMResponse,
)
def deactivate_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    bom = service.deactivate_bom(bom_id)

    return build_bom_response(bom)


@router.delete(
    "/{bom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_bom_permission(current_user)

    service = BOMService(db)

    service.delete_bom(bom_id)

    return None