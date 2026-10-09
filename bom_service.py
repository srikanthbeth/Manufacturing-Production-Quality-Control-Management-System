from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from models.bom import BOM
from models.bom_item import BOMItem
from models.product import Product
from models.raw_material import RawMaterial
from repositories.bom_repository import BOMRepository
from schemas.bom import (
    BOMCreate,
    BOMItemCreate,
    BOMItemUpdate,
    BOMUpdate,
)


class BOMService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BOMRepository(db)

    def _validate_product(
        self,
        product_id: int,
    ) -> Product:
        product = self.db.get(Product, product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        return product

    def _validate_material(
        self,
        material_id: int,
    ) -> RawMaterial:
        material = self.db.get(
            RawMaterial,
            material_id,
        )

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Raw material not found",
            )

        return material

    def _validate_items(
        self,
        items: list[BOMItemCreate],
    ) -> None:
        material_ids = [
            item.material_id
            for item in items
        ]

        if len(material_ids) != len(set(material_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate material is not allowed in the same BOM",
            )

        for item in items:
            self._validate_material(
                item.material_id
            )

            if item.quantity_required <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Material quantity must be greater than zero",
                )

    def _deactivate_other_boms(
        self,
        product_id: int,
        exclude_bom_id: int | None = None,
    ) -> None:
        statement = select(BOM).where(
            BOM.product_id == product_id,
            BOM.is_active.is_(True),
        )

        active_boms = list(
            self.db.scalars(statement).all()
        )

        for bom in active_boms:
            if (
                exclude_bom_id is None
                or bom.id != exclude_bom_id
            ):
                bom.is_active = False

    def create_bom(
        self,
        data: BOMCreate,
    ) -> BOM:
        self._validate_product(
            data.product_id
        )

        existing = self.repository.get_by_product_and_version(
            data.product_id,
            data.version,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="BOM version already exists for this product",
            )

        self._validate_items(data.items)

        if data.is_active:
            self._deactivate_other_boms(
                data.product_id
            )

        bom = BOM(
            product_id=data.product_id,
            version=data.version,
            description=data.description,
            is_active=data.is_active,
        )

        self.repository.create(bom)

        for item_data in data.items:
            item = BOMItem(
                bom_id=bom.id,
                material_id=item_data.material_id,
                quantity_required=item_data.quantity_required,
            )

            self.repository.add_item(item)

        self.db.commit()
        self.db.refresh(bom)

        return bom

    def get_bom(
        self,
        bom_id: int,
    ) -> BOM:
        bom = self.repository.get_by_id(
            bom_id
        )

        if not bom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BOM not found",
            )

        return bom

    def list_boms(
        self,
        skip: int = 0,
        limit: int = 20,
        product_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[BOM]:
        statement = select(BOM).order_by(
            BOM.id.desc()
        )

        if product_id is not None:
            statement = statement.where(
                BOM.product_id == product_id
            )

        if is_active is not None:
            statement = statement.where(
                BOM.is_active == is_active
            )

        statement = (
            statement
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update_bom(
        self,
        bom_id: int,
        data: BOMUpdate,
    ) -> BOM:
        bom = self.get_bom(bom_id)

        if data.version is not None:
            existing = (
                self.repository.get_by_product_and_version(
                    bom.product_id,
                    data.version,
                )
            )

            if existing and existing.id != bom.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="BOM version already exists for this product",
                )

            bom.version = data.version

        if data.description is not None:
            bom.description = data.description

        self.db.commit()
        self.db.refresh(bom)

        return bom

    def add_item(
        self,
        bom_id: int,
        data: BOMItemCreate,
    ) -> BOMItem:
        bom = self.get_bom(bom_id)

        if bom.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify an active BOM",
            )

        self._validate_material(
            data.material_id
        )

        existing = self.repository.get_item(
            bom_id,
            data.material_id,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Material already exists in this BOM",
            )

        item = BOMItem(
            bom_id=bom_id,
            material_id=data.material_id,
            quantity_required=data.quantity_required,
        )

        self.repository.add_item(item)

        self.db.commit()
        self.db.refresh(item)

        return item

    def update_item(
        self,
        bom_id: int,
        item_id: int,
        data: BOMItemUpdate,
    ) -> BOMItem:
        bom = self.get_bom(bom_id)

        if bom.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify an active BOM",
            )

        item = self.repository.get_item_by_id(
            item_id
        )

        if not item or item.bom_id != bom_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BOM item not found",
            )

        item.quantity_required = (
            data.quantity_required
        )

        self.db.commit()
        self.db.refresh(item)

        return item

    def remove_item(
        self,
        bom_id: int,
        item_id: int,
    ) -> None:
        bom = self.get_bom(bom_id)

        if bom.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify an active BOM",
            )

        item = self.repository.get_item_by_id(
            item_id
        )

        if not item or item.bom_id != bom_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BOM item not found",
            )

        self.repository.remove_item(item)

        self.db.commit()

    def activate_bom(
        self,
        bom_id: int,
    ) -> BOM:
        bom = self.get_bom(bom_id)

        self._deactivate_other_boms(
            bom.product_id,
            exclude_bom_id=bom.id,
        )

        bom.is_active = True

        self.db.commit()
        self.db.refresh(bom)

        return bom

    def deactivate_bom(
        self,
        bom_id: int,
    ) -> BOM:
        bom = self.get_bom(bom_id)

        bom.is_active = False

        self.db.commit()
        self.db.refresh(bom)

        return bom

    def delete_bom(
        self,
        bom_id: int,
    ) -> None:
        bom = self.get_bom(bom_id)

        if bom.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active BOM cannot be deleted",
            )

        self.repository.delete(bom)

        self.db.commit()