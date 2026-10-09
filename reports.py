from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db

from schemas.reports import (
    DailyProductionReportResponse,
    MonthlyProductionReportResponse,
    MachinePerformanceReportResponse,
    ProductProductionReportResponse,
    QualityReportResponse,
    DefectAnalysisResponse,
    MaterialConsumptionReportResponse,
    WorkerPerformanceReportResponse,
    ShiftPerformanceReportResponse,
    DowntimeAnalysisResponse,
)

from services.report_service import ReportService


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Advanced Reports"],
)


@router.get(
    "/daily-production",
    response_model=list[
        DailyProductionReportResponse
    ],
)
def get_daily_production_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_daily_production()


@router.get(
    "/monthly-production",
    response_model=list[
        MonthlyProductionReportResponse
    ],
)
def get_monthly_production_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_monthly_production()


@router.get(
    "/machine-performance",
    response_model=list[
        MachinePerformanceReportResponse
    ],
)
def get_machine_performance_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_machine_performance()


@router.get(
    "/product-production",
    response_model=list[
        ProductProductionReportResponse
    ],
)
def get_product_production_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_product_production()


@router.get(
    "/quality",
    response_model=QualityReportResponse,
)
def get_quality_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_quality_report()


@router.get(
    "/defects",
    response_model=list[
        DefectAnalysisResponse
    ],
)
def get_defect_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_defect_analysis()


@router.get(
    "/material-consumption",
    response_model=list[
        MaterialConsumptionReportResponse
    ],
)
def get_material_consumption_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_material_consumption()


@router.get(
    "/worker-performance",
    response_model=list[
        WorkerPerformanceReportResponse
    ],
)
def get_worker_performance_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_worker_performance()


@router.get(
    "/shift-performance",
    response_model=list[
        ShiftPerformanceReportResponse
    ],
)
def get_shift_performance_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_shift_performance()


@router.get(
    "/downtime",
    response_model=list[
        DowntimeAnalysisResponse
    ],
)
def get_downtime_analysis_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ReportService(db)

    return service.get_downtime_analysis()