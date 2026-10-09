from sqlalchemy.orm import Session

from repositories.report_repository import ReportRepository


class ReportService:
    def __init__(self, db: Session):
        self.repository = ReportRepository(db)

    def get_daily_production(self):
        return self.repository.get_daily_production()

    def get_monthly_production(self):
        return self.repository.get_monthly_production()

    def get_machine_performance(self):
        return self.repository.get_machine_performance()

    def get_product_production(self):
        return self.repository.get_product_production()

    def get_quality_report(self):
        return self.repository.get_quality_report()

    def get_defect_analysis(self):
        return self.repository.get_defect_analysis()

    def get_material_consumption(self):
        return self.repository.get_material_consumption()

    def get_worker_performance(self):
        return self.repository.get_worker_performance()

    def get_shift_performance(self):
        return self.repository.get_shift_performance()

    def get_downtime_analysis(self):
        return self.repository.get_downtime_analysis()