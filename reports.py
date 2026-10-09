from datetime import date

from pydantic import BaseModel, ConfigDict


class DailyProductionReportResponse(BaseModel):
    date: date
    total_production_orders: int
    planned_quantity: int
    produced_quantity: int
    rejected_quantity: int
    completed_orders: int
    production_efficiency: float
    rejection_rate: float


class MonthlyProductionReportResponse(BaseModel):
    year: int
    month: int
    total_production_orders: int
    planned_quantity: int
    produced_quantity: int
    rejected_quantity: int
    completed_orders: int
    production_efficiency: float
    rejection_rate: float


class MachinePerformanceReportResponse(BaseModel):
    machine_id: int
    machine_code: str
    machine_type: str
    production_line_id: int | None
    operating_hours: float
    downtime_hours: float
    utilization_percentage: float
    production_quantity: int
    rejected_quantity: int
    rejection_rate: float
    maintenance_count: int
    machine_status: str


class ProductProductionReportResponse(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    total_production_orders: int
    planned_quantity: int
    produced_quantity: int
    rejected_quantity: int
    completed_orders: int
    production_efficiency: float
    rejection_rate: float


class QualityReportResponse(BaseModel):
    total_inspections: int
    passed_inspections: int
    failed_inspections: int
    pending_inspections: int
    pass_percentage: float
    fail_percentage: float


class DefectAnalysisResponse(BaseModel):
    defect_type: str
    severity: str
    defect_count: int
    quantity_affected: int
    resolved_defects: int
    open_defects: int


class MaterialConsumptionReportResponse(BaseModel):
    material_id: int
    material_name: str
    material_code: str
    stock_in: float
    stock_out: float
    consumption: float
    current_stock: float
    minimum_stock_level: float
    reorder_level: float
    stock_status: str


class WorkerPerformanceReportResponse(BaseModel):
    worker_id: int
    worker_name: str
    employee_code: str
    assigned_batches: int
    completed_batches: int
    produced_quantity: int
    rejected_quantity: int
    production_efficiency: float
    rejection_rate: float


class ShiftPerformanceReportResponse(BaseModel):
    shift_id: int
    shift_name: str
    total_workers: int
    production_orders: int
    completed_orders: int
    produced_quantity: int
    rejected_quantity: int
    production_efficiency: float
    rejection_rate: float


class DowntimeAnalysisResponse(BaseModel):
    machine_id: int
    machine_code: str
    production_line_id: int | None
    downtime_events: int
    total_downtime_minutes: float
    total_downtime_hours: float


class ReportsConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)