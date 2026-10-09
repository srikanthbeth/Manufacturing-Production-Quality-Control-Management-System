from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

from database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    employee_code = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    skill = Column(
        String(150),
        nullable=False,
    )

    department = Column(
        String(150),
        nullable=False,
    )

    shift = Column(
        String(50),
        nullable=False,
    )

    production_line_id = Column(
        Integer,
        ForeignKey(
            "production_lines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default="Active",
        index=True,
    )

    profile_description = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "employee_code",
            name="uq_workers_employee_code",
        ),
    )