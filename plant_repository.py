from sqlalchemy import select
from sqlalchemy.orm import Session

from models.plant import Plant


class PlantRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, plant: Plant):
        self.db.add(plant)
        self.db.flush()
        self.db.refresh(plant)
        return plant

    def get_by_id(self, plant_id: int):
        return self.db.get(Plant, plant_id)

    def get_by_code(self, code: str):
        statement = select(Plant).where(
            Plant.code == code
        )

        return self.db.scalar(statement)

    def get_all(self):
        statement = select(Plant).order_by(
            Plant.id.asc()
        )

        return self.db.scalars(statement).all()

    def save(self):
        self.db.commit()

    def refresh(self, plant: Plant):
        self.db.refresh(plant)

    def delete(self, plant: Plant):
        self.db.delete(plant)
        self.db.flush()