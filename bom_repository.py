from sqlalchemy import select
from sqlalchemy.orm import Session

from models.bom import BOM
from models.bom_item import BOMItem


class BOMRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, bom: BOM) -> BOM:
        self.db.add(bom)
        self.db.flush()
        self.db.refresh(bom)
        return bom

    def get_by_id(self, bom_id: int) -> BOM | None:
        return self.db.get(BOM, bom_id)

    def get_by_product_and_version(
        self,
        product_id: int,
        version: int,
    ) -> BOM | None:
        statement = select(BOM).where(
            BOM.product_id == product_id,
            BOM.version == version,
        )

        return self.db.scalar(statement)

    def get_active_by_product(
        self,
        product_id: int,
    ) -> BOM | None:
        statement = select(BOM).where(
            BOM.product_id == product_id,
            BOM.is_active.is_(True),
        )

        return self.db.scalar(statement)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> list[BOM]:
        statement = (
            select(BOM)
            .order_by(BOM.id.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def list_by_product(
        self,
        product_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> list[BOM]:
        statement = (
            select(BOM)
            .where(BOM.product_id == product_id)
            .order_by(BOM.version.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_item(
        self,
        bom_id: int,
        material_id: int,
    ) -> BOMItem | None:
        statement = select(BOMItem).where(
            BOMItem.bom_id == bom_id,
            BOMItem.material_id == material_id,
        )

        return self.db.scalar(statement)

    def get_item_by_id(
        self,
        item_id: int,
    ) -> BOMItem | None:
        return self.db.get(BOMItem, item_id)

    def add_item(
        self,
        item: BOMItem,
    ) -> BOMItem:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def remove_item(
        self,
        item: BOMItem,
    ) -> None:
        self.db.delete(item)
        self.db.flush()

    def delete(
        self,
        bom: BOM,
    ) -> None:
        self.db.delete(bom)
        self.db.flush()