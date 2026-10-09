from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


if TYPE_CHECKING:
    from models.bom import BOM


class BOMItem(Base):
    __tablename__ = "bom_items"

    __table_args__ = (
        UniqueConstraint(
            "bom_id",
            "material_id",
            name="uq_bom_material",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    bom_id: Mapped[int] = mapped_column(
        ForeignKey(
            "boms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    material_id: Mapped[int] = mapped_column(
        ForeignKey(
            "raw_materials.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    quantity_required: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    bom: Mapped["BOM"] = relationship(
        "BOM",
        back_populates="items",
    )