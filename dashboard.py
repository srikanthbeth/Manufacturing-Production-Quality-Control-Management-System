from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db
from schemas.dashboard import DashboardResponse
from services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Manufacturing Dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = DashboardService(db)

    return service.get_dashboard()