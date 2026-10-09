from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.sql import func

from database import Base


class ShiftMachineUsage(Base):
    __tablename__ = "shift_machine_usage"

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

    machine_id = Column(
        Integer,
        ForeignKey(
            "machines.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    usage_hours = Column(
        Numeric(10, 2),
        nullable=False,
    )

    downtime_hours = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    notes = Column(
        Text,
        nullable=True,
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