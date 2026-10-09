from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from core.enums import MaterialStatus
from models.raw_material import RawMaterial


class RawMaterialRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        material: RawMaterial,
    ) -> RawMaterial:
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)

        return material

    def get_by_id(
        self,
        material_id: int,
    ) -> RawMaterial | None:
        return self.db.get(
            RawMaterial,
            material_id,
        )

    def get_by_code(
        self,
        material_code: str,
    ) -> RawMaterial | None:
        statement = select(RawMaterial).where(
            RawMaterial.material_code == material_code
        )

        return self.db.execute(
            statement
        ).scalar_one_or_none()

    def search(
        self,
        search: str | None = None,
        category: str | None = None,
        status: MaterialStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[RawMaterial], int]:

        statement = select(RawMaterial)

        if search:
            search_value = f"%{search}%"

            statement = statement.where(
                or_(
                    RawMaterial.name.ilike(
                        search_value
                    ),
                    RawMaterial.material_code.ilike(
                        search_value
                    ),
                    RawMaterial.category.ilike(
                        search_value
                    ),
                    RawMaterial.supplier_reference.ilike(
                        search_value
                    ),
                )
            )

        if category:
            statement = statement.where(
                RawMaterial.category.ilike(
                    category
                )
            )

        if status:
            statement = statement.where(
                RawMaterial.status == status
            )

        count_statement = select(
            func.count()
        ).select_from(
            statement.subquery()
        )

        total = self.db.execute(
            count_statement
        ).scalar_one()

        offset = (page - 1) * page_size

        statement = (
            statement
            .order_by(RawMaterial.id)
            .offset(offset)
            .limit(page_size)
        )

        materials = list(
            self.db.execute(
                statement
            ).scalars().all()
        )

        return materials, total

    def save(
        self,
        material: RawMaterial,
    ) -> RawMaterial:
        self.db.commit()
        self.db.refresh(material)

        return material

    def delete(
        self,
        material: RawMaterial,
    ) -> None:
        self.db.delete(material)
        self.db.commit()