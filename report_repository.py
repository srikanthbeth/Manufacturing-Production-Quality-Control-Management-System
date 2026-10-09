from sqlalchemy import func
from sqlalchemy.orm import Session

from models.production_order import ProductionOrder
from models.production_batch import ProductionBatch
from models.machine import Machine
from models.product import Product
from models.quality_inspection import QualityInspection
from models.defect import Defect
from models.raw_material import RawMaterial
from models.inventory_movement import InventoryMovement
from models.downtime import Downtime
from models.maintenance import Maintenance
from models.worker import Worker
from models.shift import Shift
from models.shift_worker import ShiftWorker
from models.shift_production_output import ShiftProductionOutput


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_daily_production(self):
        rows = (
            self.db.query(
                func.date(ProductionBatch.created_at).label("report_date"),
                func.count(
                    func.distinct(ProductionOrder.id)
                ).label("total_orders"),
                func.coalesce(
                    func.sum(ProductionBatch.planned_quantity),
                    0,
                ).label("planned_quantity"),
                func.coalesce(
                    func.sum(ProductionBatch.produced_quantity),
                    0,
                ).label("produced_quantity"),
                func.coalesce(
                    func.sum(ProductionBatch.rejected_quantity),
                    0,
                ).label("rejected_quantity"),
            )
            .join(
                ProductionOrder,
                ProductionOrder.id == ProductionBatch.production_order_id,
            )
            .group_by(func.date(ProductionBatch.created_at))
            .order_by(func.date(ProductionBatch.created_at))
            .all()
        )

        result = []

        for row in rows:
            planned = int(row.planned_quantity or 0)
            produced = int(row.produced_quantity or 0)
            rejected = int(row.rejected_quantity or 0)

            efficiency = (
                (produced / planned) * 100
                if planned > 0
                else 0
            )

            rejection_rate = (
                (rejected / (produced + rejected)) * 100
                if produced + rejected > 0
                else 0
            )

            completed = (
                self.db.query(
                    func.count(ProductionOrder.id)
                )
                .join(
                    ProductionBatch,
                    ProductionBatch.production_order_id
                    == ProductionOrder.id,
                )
                .filter(
                    func.date(
                        ProductionBatch.created_at
                    )
                    == row.report_date,
                    ProductionOrder.status == "Completed",
                )
                .scalar()
                or 0
            )

            result.append(
                {
                    "date": row.report_date,
                    "total_production_orders": int(
                        row.total_orders or 0
                    ),
                    "planned_quantity": planned,
                    "produced_quantity": produced,
                    "rejected_quantity": rejected,
                    "completed_orders": int(completed),
                    "production_efficiency": round(
                        efficiency,
                        2,
                    ),
                    "rejection_rate": round(
                        rejection_rate,
                        2,
                    ),
                }
            )

        return result

    def get_monthly_production(self):
        rows = (
            self.db.query(
                func.extract(
                    "year",
                    ProductionBatch.created_at,
                ).label("year"),
                func.extract(
                    "month",
                    ProductionBatch.created_at,
                ).label("month"),
                func.count(
                    func.distinct(ProductionOrder.id)
                ).label("total_orders"),
                func.coalesce(
                    func.sum(ProductionBatch.planned_quantity),
                    0,
                ).label("planned_quantity"),
                func.coalesce(
                    func.sum(ProductionBatch.produced_quantity),
                    0,
                ).label("produced_quantity"),
                func.coalesce(
                    func.sum(ProductionBatch.rejected_quantity),
                    0,
                ).label("rejected_quantity"),
            )
            .join(
                ProductionOrder,
                ProductionOrder.id == ProductionBatch.production_order_id,
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
            .all()
        )

        result = []

        for row in rows:
            planned = int(row.planned_quantity or 0)
            produced = int(row.produced_quantity or 0)
            rejected = int(row.rejected_quantity or 0)

            efficiency = (
                (produced / planned) * 100
                if planned > 0
                else 0
            )

            rejection_rate = (
                (rejected / (produced + rejected)) * 100
                if produced + rejected > 0
                else 0
            )

            completed = (
                self.db.query(
                    func.count(ProductionOrder.id)
                )
                .join(
                    ProductionBatch,
                    ProductionBatch.production_order_id
                    == ProductionOrder.id,
                )
                .filter(
                    func.extract(
                        "year",
                        ProductionBatch.created_at,
                    )
                    == row.year,
                    func.extract(
                        "month",
                        ProductionBatch.created_at,
                    )
                    == row.month,
                    ProductionOrder.status == "Completed",
                )
                .scalar()
                or 0
            )

            result.append(
                {
                    "year": int(row.year),
                    "month": int(row.month),
                    "total_production_orders": int(
                        row.total_orders or 0
                    ),
                    "planned_quantity": planned,
                    "produced_quantity": produced,
                    "rejected_quantity": rejected,
                    "completed_orders": int(completed),
                    "production_efficiency": round(
                        efficiency,
                        2,
                    ),
                    "rejection_rate": round(
                        rejection_rate,
                        2,
                    ),
                }
            )

        return result

    def get_machine_performance(self):
        machines = self.db.query(Machine).all()

        result = []

        for machine in machines:
            downtime = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            Downtime.duration_minutes
                        ),
                        0,
                    )
                )
                .filter(
                    Downtime.machine_id == machine.id
                )
                .scalar()
                or 0
            )

            production = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ProductionBatch.produced_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ProductionBatch.machine_id
                    == machine.id
                )
                .scalar()
                or 0
            )

            rejected = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ProductionBatch.rejected_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ProductionBatch.machine_id
                    == machine.id
                )
                .scalar()
                or 0
            )

            maintenance_count = (
                self.db.query(
                    func.count(Maintenance.id)
                )
                .filter(
                    Maintenance.machine_id
                    == machine.id
                )
                .scalar()
                or 0
            )

            operating_hours = float(
                machine.operating_hours or 0
            )

            downtime_hours = float(downtime) / 60

            total_hours = (
                operating_hours + downtime_hours
            )

            utilization = (
                (operating_hours / total_hours) * 100
                if total_hours > 0
                else 0
            )

            rejection_rate = (
                (
                    float(rejected)
                    / (
                        float(production)
                        + float(rejected)
                    )
                )
                * 100
                if float(production)
                + float(rejected)
                > 0
                else 0
            )

            result.append(
                {
                    "machine_id": machine.id,
                    "machine_code": machine.machine_code,
                    "machine_type": machine.machine_type,
                    "production_line_id": (
                        machine.production_line_id
                    ),
                    "operating_hours": operating_hours,
                    "downtime_hours": round(
                        downtime_hours,
                        2,
                    ),
                    "utilization_percentage": round(
                        utilization,
                        2,
                    ),
                    "production_quantity": int(
                        production
                    ),
                    "rejected_quantity": int(
                        rejected
                    ),
                    "rejection_rate": round(
                        rejection_rate,
                        2,
                    ),
                    "maintenance_count": int(
                        maintenance_count
                    ),
                    "machine_status": (
                        machine.status.value
                        if hasattr(
                            machine.status,
                            "value",
                        )
                        else str(machine.status)
                    ),
                }
            )

        return result

    def get_product_production(self):
        products = self.db.query(Product).all()

        result = []

        for product in products:
            orders = (
                self.db.query(ProductionOrder)
                .filter(
                    ProductionOrder.product_id
                    == product.id
                )
                .all()
            )

            order_ids = [
                order.id
                for order in orders
            ]

            if order_ids:
                planned = (
                    self.db.query(
                        func.coalesce(
                            func.sum(
                                ProductionBatch.planned_quantity
                            ),
                            0,
                        )
                    )
                    .filter(
                        ProductionBatch.production_order_id.in_(
                            order_ids
                        )
                    )
                    .scalar()
                    or 0
                )

                produced = (
                    self.db.query(
                        func.coalesce(
                            func.sum(
                                ProductionBatch.produced_quantity
                            ),
                            0,
                        )
                    )
                    .filter(
                        ProductionBatch.production_order_id.in_(
                            order_ids
                        )
                    )
                    .scalar()
                    or 0
                )

                rejected = (
                    self.db.query(
                        func.coalesce(
                            func.sum(
                                ProductionBatch.rejected_quantity
                            ),
                            0,
                        )
                    )
                    .filter(
                        ProductionBatch.production_order_id.in_(
                            order_ids
                        )
                    )
                    .scalar()
                    or 0
                )
            else:
                planned = 0
                produced = 0
                rejected = 0

            completed = sum(
                1
                for order in orders
                if (
                    order.status.value
                    if hasattr(
                        order.status,
                        "value",
                    )
                    else str(order.status)
                )
                == "Completed"
            )

            efficiency = (
                (float(produced) / float(planned))
                * 100
                if planned
                else 0
            )

            rejection_rate = (
                (
                    float(rejected)
                    / (
                        float(produced)
                        + float(rejected)
                    )
                )
                * 100
                if float(produced)
                + float(rejected)
                > 0
                else 0
            )

            result.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_code": product.sku,
                    "total_production_orders": len(
                        orders
                    ),
                    "planned_quantity": int(
                        planned
                    ),
                    "produced_quantity": int(
                        produced
                    ),
                    "rejected_quantity": int(
                        rejected
                    ),
                    "completed_orders": completed,
                    "production_efficiency": round(
                        efficiency,
                        2,
                    ),
                    "rejection_rate": round(
                        rejection_rate,
                        2,
                    ),
                }
            )

        return result

    def get_quality_report(self):
        total = (
            self.db.query(
                func.count(QualityInspection.id)
            ).scalar()
            or 0
        )

        passed = (
            self.db.query(
                func.count(QualityInspection.id)
            )
            .filter(
                func.lower(
                    QualityInspection.result
                )
                == "pass"
            )
            .scalar()
            or 0
        )

        failed = (
            self.db.query(
                func.count(QualityInspection.id)
            )
            .filter(
                func.lower(
                    QualityInspection.result
                )
                == "fail"
            )
            .scalar()
            or 0
        )

        pending = (
            self.db.query(
                func.count(QualityInspection.id)
            )
            .filter(
                func.lower(
                    QualityInspection.result
                )
                == "pending"
            )
            .scalar()
            or 0
        )

        pass_percentage = (
            (passed / total) * 100
            if total > 0
            else 0
        )

        fail_percentage = (
            (failed / total) * 100
            if total > 0
            else 0
        )

        return {
            "total_inspections": int(total),
            "passed_inspections": int(passed),
            "failed_inspections": int(failed),
            "pending_inspections": int(pending),
            "pass_percentage": round(
                pass_percentage,
                2,
            ),
            "fail_percentage": round(
                fail_percentage,
                2,
            ),
        }

    def get_defect_analysis(self):
        rows = (
            self.db.query(
                Defect.defect_type,
                Defect.severity,
                func.count(
                    Defect.id
                ).label("defect_count"),
                func.coalesce(
                    func.sum(
                        Defect.quantity_affected
                    ),
                    0,
                ).label("quantity_affected"),
            )
            .group_by(
                Defect.defect_type,
                Defect.severity,
            )
            .order_by(
                Defect.defect_type,
                Defect.severity,
            )
            .all()
        )

        result = []

        for row in rows:
            resolved = (
                self.db.query(
                    func.count(Defect.id)
                )
                .filter(
                    Defect.defect_type
                    == row.defect_type,
                    Defect.severity
                    == row.severity,
                    func.lower(
                        Defect.resolution_status
                    ).in_(
                        [
                            "resolved",
                            "closed",
                        ]
                    ),
                )
                .scalar()
                or 0
            )

            open_defects = (
                int(row.defect_count or 0)
                - int(resolved or 0)
            )

            result.append(
                {
                    "defect_type": row.defect_type,
                    "severity": row.severity,
                    "defect_count": int(
                        row.defect_count or 0
                    ),
                    "quantity_affected": int(
                        row.quantity_affected or 0
                    ),
                    "resolved_defects": int(
                        resolved or 0
                    ),
                    "open_defects": int(
                        open_defects
                    ),
                }
            )

        return result

    def get_material_consumption(self):
        materials = (
            self.db.query(RawMaterial)
            .order_by(RawMaterial.id)
            .all()
        )

        stock_in_types = [
            "stock in",
            "stock-in",
            "in",
            "receipt",
            "purchase",
        ]

        stock_out_types = [
            "stock out",
            "stock-out",
            "out",
            "issue",
            "consumption",
        ]

        result = []

        for material in materials:
            stock_in = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            InventoryMovement.quantity
                        ),
                        0,
                    )
                )
                .filter(
                    InventoryMovement.raw_material_id
                    == material.id,
                    func.lower(
                        InventoryMovement.movement_type
                    ).in_(stock_in_types),
                )
                .scalar()
                or 0
            )

            stock_out = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            InventoryMovement.quantity
                        ),
                        0,
                    )
                )
                .filter(
                    InventoryMovement.raw_material_id
                    == material.id,
                    func.lower(
                        InventoryMovement.movement_type
                    ).in_(stock_out_types),
                )
                .scalar()
                or 0
            )

            current_stock = float(
                material.available_quantity or 0
            )

            minimum_stock = float(
                material.minimum_stock_level or 0
            )

            reorder_level = float(
                material.reorder_level or 0
            )

            if current_stock <= minimum_stock:
                stock_status = "Critical"
            elif current_stock <= reorder_level:
                stock_status = "Low Stock"
            else:
                stock_status = "Normal"

            result.append(
                {
                    "material_id": material.id,
                    "material_name": material.name,
                    "material_code": material.material_code,
                    "stock_in": round(
                        float(stock_in or 0),
                        2,
                    ),
                    "stock_out": round(
                        float(stock_out or 0),
                        2,
                    ),
                    "consumption": round(
                        float(stock_out or 0),
                        2,
                    ),
                    "current_stock": round(
                        current_stock,
                        2,
                    ),
                    "minimum_stock_level": round(
                        minimum_stock,
                        2,
                    ),
                    "reorder_level": round(
                        reorder_level,
                        2,
                    ),
                    "stock_status": stock_status,
                }
            )

        return result

    def get_worker_performance(self):
        workers = (
            self.db.query(Worker)
            .order_by(Worker.id)
            .all()
        )

        result = []

        for worker in workers:
            assigned_batches = (
                self.db.query(
                    func.count(
                        ProductionBatch.id
                    )
                )
                .filter(
                    ProductionBatch.supervisor_id
                    == worker.user_id
                )
                .scalar()
                or 0
            )

            completed_batches = (
                self.db.query(
                    func.count(
                        ProductionBatch.id
                    )
                )
                .join(
                    ProductionOrder,
                    ProductionOrder.id
                    == ProductionBatch.production_order_id,
                )
                .filter(
                    ProductionBatch.supervisor_id
                    == worker.user_id,
                    ProductionOrder.status
                    == "Completed",
                )
                .scalar()
                or 0
            )

            produced_quantity = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ProductionBatch.produced_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ProductionBatch.supervisor_id
                    == worker.user_id
                )
                .scalar()
                or 0
            )

            rejected_quantity = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ProductionBatch.rejected_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ProductionBatch.supervisor_id
                    == worker.user_id
                )
                .scalar()
                or 0
            )

            planned_quantity = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ProductionBatch.planned_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ProductionBatch.supervisor_id
                    == worker.user_id
                )
                .scalar()
                or 0
            )

            production_efficiency = (
                (
                    float(produced_quantity)
                    / float(planned_quantity)
                )
                * 100
                if float(planned_quantity) > 0
                else 0
            )

            rejection_rate = (
                (
                    float(rejected_quantity)
                    / (
                        float(produced_quantity)
                        + float(rejected_quantity)
                    )
                )
                * 100
                if (
                    float(produced_quantity)
                    + float(rejected_quantity)
                ) > 0
                else 0
            )

            worker_name = (
                worker.employee_code
            )

            if hasattr(worker, "user") and worker.user:
                worker_name = (
                    worker.user.full_name
                    or worker.employee_code
                )

            result.append(
                {
                    "worker_id": worker.id,
                    "worker_name": worker_name,
                    "employee_code": worker.employee_code,
                    "assigned_batches": int(
                        assigned_batches
                    ),
                    "completed_batches": int(
                        completed_batches
                    ),
                    "produced_quantity": int(
                        produced_quantity
                    ),
                    "rejected_quantity": int(
                        rejected_quantity
                    ),
                    "production_efficiency": round(
                        production_efficiency,
                        2,
                    ),
                    "rejection_rate": round(
                        rejection_rate,
                        2,
                    ),
                }
            )

        return result

    def get_shift_performance(self):
        shifts = (
            self.db.query(Shift)
            .order_by(Shift.id)
            .all()
        )

        result = []

        for shift in shifts:
            total_workers = (
                self.db.query(
                    func.count(
                        ShiftWorker.id
                    )
                )
                .filter(
                    ShiftWorker.shift_id
                    == shift.id
                )
                .scalar()
                or 0
            )

            production_outputs = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ShiftProductionOutput.produced_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ShiftProductionOutput.shift_id
                    == shift.id
                )
                .scalar()
                or 0
            )

            rejected_outputs = (
                self.db.query(
                    func.coalesce(
                        func.sum(
                            ShiftProductionOutput.rejected_quantity
                        ),
                        0,
                    )
                )
                .filter(
                    ShiftProductionOutput.shift_id
                    == shift.id
                )
                .scalar()
                or 0
            )

            batch_ids_query = (
                self.db.query(
                    ShiftProductionOutput.production_batch_id
                )
                .filter(
                    ShiftProductionOutput.shift_id
                    == shift.id
                )
                .distinct()
            )

            batch_ids = [
                row[0]
                for row in batch_ids_query.all()
            ]

            production_orders = 0
            completed_orders = 0
            planned_quantity = 0

            if batch_ids:
                production_orders = (
                    self.db.query(
                        func.count(
                            func.distinct(
                                ProductionBatch.production_order_id
                            )
                        )
                    )
                    .filter(
                        ProductionBatch.id.in_(
                            batch_ids
                        )
                    )
                    .scalar()
                    or 0
                )

                completed_orders = (
                    self.db.query(
                        func.count(
                            func.distinct(
                                ProductionOrder.id
                            )
                        )
                    )
                    .join(
                        ProductionBatch,
                        ProductionBatch.production_order_id
                        == ProductionOrder.id,
                    )
                    .filter(
                        ProductionBatch.id.in_(
                            batch_ids
                        ),
                        ProductionOrder.status
                        == "Completed",
                    )
                    .scalar()
                    or 0
                )

                planned_quantity = (
                    self.db.query(
                        func.coalesce(
                            func.sum(
                                ProductionBatch.planned_quantity
                            ),
                            0,
                        )
                    )
                    .filter(
                        ProductionBatch.id.in_(
                            batch_ids
                        )
                    )
                    .scalar()
                    or 0
                )

            production_efficiency = (
                (
                    float(production_outputs)
                    / float(planned_quantity)
                )
                * 100
                if float(planned_quantity) > 0
                else 0
            )

            rejection_rate = (
                (
                    float(rejected_outputs)
                    / (
                        float(production_outputs)
                        + float(rejected_outputs)
                    )
                )
                * 100
                if (
                    float(production_outputs)
                    + float(rejected_outputs)
                ) > 0
                else 0
            )

            result.append(
                {
                    "shift_id": shift.id,
                    "shift_name": shift.name,
                    "total_workers": int(
                        total_workers
                    ),
                    "production_orders": int(
                        production_orders
                    ),
                    "completed_orders": int(
                        completed_orders
                    ),
                    "produced_quantity": int(
                        production_outputs
                    ),
                    "rejected_quantity": int(
                        rejected_outputs
                    ),
                    "production_efficiency": round(
                        production_efficiency,
                        2,
                    ),
                    "rejection_rate": round(
                        rejection_rate,
                        2,
                    ),
                }
            )

        return result

    def get_downtime_analysis(self):
        rows = (
            self.db.query(
                Downtime.machine_id,
                Machine.machine_code,
                Machine.production_line_id,
                func.count(
                    Downtime.id
                ).label("downtime_events"),
                func.coalesce(
                    func.sum(
                        Downtime.duration_minutes
                    ),
                    0,
                ).label(
                    "total_downtime_minutes"
                ),
            )
            .join(
                Machine,
                Machine.id
                == Downtime.machine_id,
            )
            .group_by(
                Downtime.machine_id,
                Machine.machine_code,
                Machine.production_line_id,
            )
            .order_by(
                Machine.machine_code
            )
            .all()
        )

        result = []

        for row in rows:
            total_minutes = float(
                row.total_downtime_minutes
                or 0
            )

            result.append(
                {
                    "machine_id": row.machine_id,
                    "machine_code": row.machine_code,
                    "production_line_id": (
                        row.production_line_id
                    ),
                    "downtime_events": int(
                        row.downtime_events
                        or 0
                    ),
                    "total_downtime_minutes": round(
                        total_minutes,
                        2,
                    ),
                    "total_downtime_hours": round(
                        total_minutes / 60,
                        2,
                    ),
                }
            )

        return result