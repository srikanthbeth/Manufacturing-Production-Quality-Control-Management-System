from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from core.enums import PlantStatus, UserRole
from database import get_db
from models.user import User
from schemas.plant import PlantCreate, PlantResponse, PlantUpdate
from services.plant_service import PlantService


router = APIRouter(
    prefix="/api/v1/plants",
    tags=["Plants"],
)


@router.post(
    "",
    response_model=PlantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plant(
    data: PlantCreate,
    _: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.create(
        name=data.name,
        code=data.code,
        address=data.address,
        city=data.city,
        state=data.state,
        country=data.country,
        production_capacity=data.production_capacity,
        status_value=data.status,
        manager_id=data.manager_id,
    )


@router.get(
    "",
    response_model=list[PlantResponse],
)
def list_plants(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.get_all()


@router.get(
    "/{plant_id}",
    response_model=PlantResponse,
)
def get_plant(
    plant_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.get_by_id(plant_id)


@router.put(
    "/{plant_id}",
    response_model=PlantResponse,
)
def update_plant(
    plant_id: int,
    data: PlantUpdate,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.update(
        plant_id=plant_id,
        data=data,
    )


@router.patch(
    "/{plant_id}/status",
    response_model=PlantResponse,
)
def update_plant_status(
    plant_id: int,
    status_value: PlantStatus,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.update_status(
        plant_id=plant_id,
        status_value=status_value,
    )


@router.patch(
    "/{plant_id}/manager/{manager_id}",
    response_model=PlantResponse,
)
def assign_plant_manager(
    plant_id: int,
    manager_id: int,
    _: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.assign_manager(
        plant_id=plant_id,
        manager_id=manager_id,
    )


@router.delete(
    "/{plant_id}/manager",
    response_model=PlantResponse,
)
def remove_plant_manager(
    plant_id: int,
    _: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.remove_manager(plant_id)


@router.patch(
    "/{plant_id}/deactivate",
    response_model=PlantResponse,
)
def deactivate_plant(
    plant_id: int,
    _: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = PlantService(db)

    return service.deactivate(plant_id)