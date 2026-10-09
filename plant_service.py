from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.enums import AccountStatus, PlantStatus, UserRole
from models.plant import Plant
from models.user import User
from repositories.plant_repository import PlantRepository


class PlantService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PlantRepository(db)

    def _validate_manager(self, manager_id: int | None):
        if manager_id is None:
            return None

        manager = self.db.get(User, manager_id)

        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plant manager not found",
            )

        if manager.status == AccountStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an inactive user as plant manager",
            )

        if manager.role != UserRole.PLANT_MANAGER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user must have Plant Manager role",
            )

        return manager

    def create(
        self,
        name: str,
        code: str,
        address: str,
        city: str,
        state: str,
        country: str,
        production_capacity: int,
        status_value: PlantStatus,
        manager_id: int | None,
    ):
        code = code.strip().upper()

        existing = self.repository.get_by_code(code)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plant code already exists",
            )

        self._validate_manager(manager_id)

        plant = Plant(
            name=name.strip(),
            code=code,
            address=address.strip(),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            production_capacity=production_capacity,
            status=status_value,
            manager_id=manager_id,
        )

        self.repository.create(plant)
        self.db.commit()
        self.repository.refresh(plant)

        return plant

    def get_by_id(self, plant_id: int):
        plant = self.repository.get_by_id(plant_id)

        if not plant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plant not found",
            )

        return plant

    def get_all(self):
        return self.repository.get_all()

    def update(
        self,
        plant_id: int,
        data,
    ):
        plant = self.get_by_id(plant_id)

        if data.name is not None:
            plant.name = data.name.strip()

        if data.address is not None:
            plant.address = data.address.strip()

        if data.city is not None:
            plant.city = data.city.strip()

        if data.state is not None:
            plant.state = data.state.strip()

        if data.country is not None:
            plant.country = data.country.strip()

        if data.production_capacity is not None:
            plant.production_capacity = data.production_capacity

        if data.status is not None:
            plant.status = data.status

        if data.manager_id is not None:
            self._validate_manager(data.manager_id)
            plant.manager_id = data.manager_id

        self.db.commit()
        self.repository.refresh(plant)

        return plant

    def update_status(
        self,
        plant_id: int,
        status_value: PlantStatus,
    ):
        plant = self.get_by_id(plant_id)

        plant.status = status_value

        self.db.commit()
        self.repository.refresh(plant)

        return plant

    def assign_manager(
        self,
        plant_id: int,
        manager_id: int,
    ):
        plant = self.get_by_id(plant_id)

        self._validate_manager(manager_id)

        plant.manager_id = manager_id

        self.db.commit()
        self.repository.refresh(plant)

        return plant

    def remove_manager(
        self,
        plant_id: int,
    ):
        plant = self.get_by_id(plant_id)

        plant.manager_id = None

        self.db.commit()
        self.repository.refresh(plant)

        return plant

    def deactivate(self, plant_id: int):
        plant = self.get_by_id(plant_id)

        plant.status = PlantStatus.INACTIVE

        self.db.commit()
        self.repository.refresh(plant)

        return plant