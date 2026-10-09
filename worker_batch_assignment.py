from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

from database import Base


class WorkerBatchAssignment(Base):
    __tablename__ = "worker_batch_assignments"

    id = Column(
        Integer,
        primary_key=True,
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

    production_batch_id = Column(
        Integer,
        ForeignKey(
            "production_batches.id",
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
            "worker_id",
            "production_batch_id",
            name="uq_worker_batch_assignment",
        ),
    )