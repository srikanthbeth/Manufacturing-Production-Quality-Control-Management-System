from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from core.enums import MaterialTransactionType


class MaterialTransaction(Base):
    __tablename__ = "material_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    material_id: Mapped[int] = mapped_column(
        ForeignKey(
            "raw_materials.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[MaterialTransactionType] = mapped_column(
        SQLEnum(
            MaterialTransactionType,
            name="material_transaction_type",
        ),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quantity_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quantity_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )