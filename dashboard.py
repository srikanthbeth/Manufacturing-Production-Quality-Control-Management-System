from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DailyProductionResponse(BaseModel):
    date: date
    quantity: int


class MonthlyProductionResponse(BaseModel):
    year: int
    month: int
    quantity: int


class MaterialConsumptionResponse(BaseModel):
    material_id: int
    material_name: str
    material_code: str
    quantity: float


class LowStockMaterialResponse(BaseModel):
    id: int
    name: str
    material_code: str
    available_quantity: int
    minimum_stock_level: int
    reorder_level: int
    status: str


class MaintenanceDueResponse(BaseModel):
    id: int
    maintenance_number: str
    machine_id: int
    maintenance_type: str
    maintenance_status: str
    next_due_date: datetime


class DefectStatisticsResponse(BaseModel):
    defect_type: str
    severity: str
    count: int
    quantity_affected: int


class DashboardResponse(BaseModel):
    total_production_orders: int
    active_production_orders: int
    completed_orders: int

    daily_production: list[
        DailyProductionResponse
    ]

    monthly_production: list[
        MonthlyProductionResponse
    ]

    production_efficiency: float
    machine_utilization: float
    machine_downtime: float

    rejection_rate: float
    quality_pass_percentage: float

    material_consumption: list[
        MaterialConsumptionResponse
    ]

    low_stock_materials: list[
        LowStockMaterialResponse
    ]

    maintenance_due: list[
        MaintenanceDueResponse
    ]

    defect_statistics: list[
        DefectStatisticsResponse
    ]

    model_config = ConfigDict(
        from_attributes=True,
    )