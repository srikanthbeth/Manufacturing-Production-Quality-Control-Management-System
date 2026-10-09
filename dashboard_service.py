from sqlalchemy.orm import Session

from repositories.dashboard_repository import (
    DashboardRepository,
)


class DashboardService:
    def __init__(self, db: Session):
        self.repository = DashboardRepository(db)

    def get_dashboard(self):
        return {
            "total_production_orders": (
                self.repository
                .get_total_production_orders()
            ),
            "active_production_orders": (
                self.repository
                .get_active_production_orders()
            ),
            "completed_orders": (
                self.repository
                .get_completed_orders()
            ),
            "daily_production": (
                self.repository
                .get_daily_production()
            ),
            "monthly_production": (
                self.repository
                .get_monthly_production()
            ),
            "production_efficiency": (
                self.repository
                .get_production_efficiency()
            ),
            "machine_utilization": (
                self.repository
                .get_machine_utilization()
            ),
            "machine_downtime": (
                self.repository
                .get_machine_downtime()
            ),
            "rejection_rate": (
                self.repository
                .get_rejection_rate()
            ),
            "quality_pass_percentage": (
                self.repository
                .get_quality_pass_percentage()
            ),
            "material_consumption": (
                self.repository
                .get_material_consumption()
            ),
            "low_stock_materials": (
                self.repository
                .get_low_stock_materials()
            ),
            "maintenance_due": (
                self.repository
                .get_maintenance_due()
            ),
            "defect_statistics": (
                self.repository
                .get_defect_statistics()
            ),
        }