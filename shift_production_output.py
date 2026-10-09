from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy.sql import func

from database import Base


class ShiftProductionOutput(Base):
    __tablename__ = "shift_production_outputs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    shift_id = Column(
        Integer,
        ForeignKey(
            "shifts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    production_batch_id = Column(
        Integer,
        ForeignKey(
            "production_batches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    produced_quantity = Column(
        Numeric(12, 2),
        nullable=False,
    )

    rejected_quantity = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    recorded_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )