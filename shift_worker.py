from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

from database import Base


class ShiftWorker(Base):
    __tablename__ = "shift_workers"

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

    worker_id = Column(
        Integer,
        ForeignKey(
            "workers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    assigned_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "shift_id",
            "worker_id",
            name="uq_shift_worker",
        ),
    )