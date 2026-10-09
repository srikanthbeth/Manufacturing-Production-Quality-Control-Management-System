from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.enums import ProductionOrderStatus
from models.defect import Defect
from models.downtime import Downtime
from models.inventory_movement import InventoryMovement
from models.machine import Machine
from models.maintenance import Maintenance
from models.production_batch import ProductionBatch
from models.production_order import ProductionOrder
from models.quality_inspection import QualityInspection
from models.raw_material import RawMaterial


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_production_orders(self):
        return (
            self.db.scalar(
                select(
                    func.count(ProductionOrder.id)
                )
            )
            or 0
        )

    def get_active_production_orders(self):
        return (
            self.db.scalar(
                select(
                    func.count(ProductionOrder.id)
                ).where(
                    ProductionOrder.status.in_(
                        [
                            ProductionOrderStatus.SCHEDULED,
                            ProductionOrderStatus.IN_PROGRESS,
                            ProductionOrderStatus.PAUSED,
                        ]
                    )
                )
            )
            or 0
        )

    def get_completed_orders(self):
        return (
            self.db.scalar(
                select(
                    func.count(ProductionOrder.id)
                ).where(
                    ProductionOrder.status
                    == ProductionOrderStatus.COMPLETED
                )
            )
            or 0
        )

    def get_daily_production(self):
        rows = self.db.execute(
            select(
                func.date(
                    ProductionBatch.created_at
                ).label("production_date"),
                func.coalesce(
                    func.sum(
                        ProductionBatch.produced_quantity
                    ),
                    0,
                ).label("quantity"),
            )
            .group_by(
                func.date(
                    ProductionBatch.created_at
                )
            )
            .order_by(
                func.date(
                    ProductionBatch.created_at
                )
            )
        ).all()

        return [
            {
                "date": row.production_date,
                "quantity": int(
                    row.quantity or 0
                ),
            }
            for row in rows
        ]

    def get_monthly_production(self):
        rows = self.db.execute(
            select(
                func.extract(
                    "year",
                    ProductionBatch.created_at,
                ).label("year"),
                func.extract(
                    "month",
                    ProductionBatch.created_at,
                ).label("month"),
                func.coalesce(
                    func.sum(
                        ProductionBatch.produced_quantity
                    ),
                    0,
                ).label("quantity"),
            )
            .group_by(
                func.extract(
                    "year",
                    ProductionBatch.created_at,
                ),
                func.extract(
                    "month",
                    ProductionBatch.created_at,
                ),
            )
            .order_by(
                func.extract(
                    "year",
                    ProductionBatch.created_at,
                ),
                func.extract(
                    "month",
                    ProductionBatch.created_at,
                ),
            )
        ).all()

        return [
            {
                "year": int(row.year),
                "month": int(row.month),
                "quantity": int(
                    row.quantity or 0
                ),
            }
            for row in rows
        ]

    def get_production_efficiency(self):
        value = self.db.scalar(
            select(
                func.avg(
                    ProductionBatch.production_efficiency
                )
            )
        )

        return round(
            float(value or 0),
            2,
        )

    def get_machine_utilization(self):
        total_operating_hours = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        Machine.operating_hours
                    ),
                    0,
                )
            )
        ) or 0

        total_downtime_minutes = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        Downtime.duration_minutes
                    ),
                    0,
                )
            )
        ) or 0

        downtime_hours = (
            float(total_downtime_minutes) / 60
        )

        total_time = (
            float(total_operating_hours)
            + downtime_hours
        )

        if total_time <= 0:
            return 0.0

        utilization = (
            float(total_operating_hours)
            / total_time
        ) * 100

        return round(
            utilization,
            2,
        )

    def get_machine_downtime(self):
        value = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        Downtime.duration_minutes
                    ),
                    0,
                )
            )
        )

        return round(
            float(value or 0),
            2,
        )

    def get_rejection_rate(self):
        produced = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        ProductionBatch.produced_quantity
                    ),
                    0,
                )
            )
        ) or 0

        rejected = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        ProductionBatch.rejected_quantity
                    ),
                    0,
                )
            )
        ) or 0

        total = (
            float(produced)
            + float(rejected)
        )

        if total <= 0:
            return 0.0

        return round(
            (
                float(rejected)
                / total
            ) * 100,
            2,
        )

    def get_quality_pass_percentage(self):
        total = self.db.scalar(
            select(
                func.count(
                    QualityInspection.id
                )
            )
        ) or 0

        passed = self.db.scalar(
            select(
                func.count(
                    QualityInspection.id
                )
            ).where(
                func.lower(
                    QualityInspection.result
                ) == "pass"
            )
        ) or 0

        if total == 0:
            return 0.0

        return round(
            (
                float(passed)
                / float(total)
            ) * 100,
            2,
        )

    def get_material_consumption(self):
        rows = self.db.execute(
            select(
                RawMaterial.id.label(
                    "material_id"
                ),
                RawMaterial.name.label(
                    "material_name"
                ),
                RawMaterial.material_code.label(
                    "material_code"
                ),
                func.coalesce(
                    func.sum(
                        InventoryMovement.quantity
                    ),
                    0,
                ).label("quantity"),
            )
            .join(
                InventoryMovement,
                InventoryMovement.raw_material_id
                == RawMaterial.id,
            )
            .where(
                func.lower(
                    InventoryMovement.movement_type
                ).in_(
                    [
                        "stock out",
                        "stock-out",
                        "out",
                        "issue",
                        "consumption",
                    ]
                )
            )
            .group_by(
                RawMaterial.id,
                RawMaterial.name,
                RawMaterial.material_code,
            )
            .order_by(
                RawMaterial.name
            )
        ).all()

        return [
            {
                "material_id": row.material_id,
                "material_name": row.material_name,
                "material_code": row.material_code,
                "quantity": float(
                    row.quantity or 0
                ),
            }
            for row in rows
        ]

    def get_low_stock_materials(self):
        rows = self.db.scalars(
            select(RawMaterial)
            .where(
                RawMaterial.available_quantity
                <= RawMaterial.reorder_level
            )
            .order_by(
                RawMaterial.available_quantity
            )
        ).all()

        return [
            {
                "id": material.id,
                "name": material.name,
                "material_code": material.material_code,
                "available_quantity": (
                    material.available_quantity
                ),
                "minimum_stock_level": (
                    material.minimum_stock_level
                ),
                "reorder_level": (
                    material.reorder_level
                ),
                "status": (
                    material.status.value
                    if hasattr(
                        material.status,
                        "value",
                    )
                    else str(material.status)
                ),
            }
            for material in rows
        ]

    def get_maintenance_due(self):
        now = datetime.utcnow()

        rows = self.db.scalars(
            select(Maintenance)
            .where(
                Maintenance.next_due_date.is_not(None),
                Maintenance.next_due_date <= now,
                func.lower(
                    Maintenance.maintenance_status
                ).notin_(
                    [
                        "completed",
                        "cancelled",
                    ]
                ),
            )
            .order_by(
                Maintenance.next_due_date
            )
        ).all()

        return [
            {
                "id": maintenance.id,
                "maintenance_number": (
                    maintenance.maintenance_number
                ),
                "machine_id": maintenance.machine_id,
                "maintenance_type": (
                    maintenance.maintenance_type
                ),
                "maintenance_status": (
                    maintenance.maintenance_status
                ),
                "next_due_date": (
                    maintenance.next_due_date
                ),
            }
            for maintenance in rows
        ]

    def get_defect_statistics(self):
        rows = self.db.execute(
            select(
                Defect.defect_type.label(
                    "defect_type"
                ),
                Defect.severity.label(
                    "severity"
                ),
                func.count(
                    Defect.id
                ).label("count"),
                func.coalesce(
                    func.sum(
                        Defect.quantity_affected
                    ),
                    0,
                ).label(
                    "quantity_affected"
                ),
            )
            .group_by(
                Defect.defect_type,
                Defect.severity,
            )
            .order_by(
                Defect.defect_type,
                Defect.severity,
            )
        ).all()

        return [
            {
                "defect_type": row.defect_type,
                "severity": row.severity,
                "count": int(
                    row.count or 0
                ),
                "quantity_affected": int(
                    row.quantity_affected or 0
                ),
            }
            for row in rows
        ]