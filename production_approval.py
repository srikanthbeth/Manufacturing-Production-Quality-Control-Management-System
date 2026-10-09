from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.production_approval import (
    ProductionApprovalResponse,
    WorkflowCommentRequest,
)
from services.production_approval_service import (
    ProductionApprovalService,
)


router = APIRouter(
    prefix="/api/v1/production-orders",
    tags=["Production Approval Workflow"],
)


@router.get(
    "/{production_order_id}/workflow",
    response_model=ProductionApprovalResponse,
)
def get_workflow(
    production_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.get(
        production_order_id
    )


@router.post(
    "/{production_order_id}/workflow/supervisor-approve",
    response_model=ProductionApprovalResponse,
)
def supervisor_approve(
    production_order_id: int,
    data: WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.supervisor_approve(
        production_order_id=production_order_id,
        current_user=current_user,
        comment=data.comment,
    )


@router.post(
    "/{production_order_id}/workflow/supervisor-reject",
    response_model=ProductionApprovalResponse,
)
def supervisor_reject(
    production_order_id: int,
    data: WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.supervisor_reject(
        production_order_id=production_order_id,
        current_user=current_user,
        comment=data.comment,
    )


@router.post(
    "/{production_order_id}/workflow/material-check",
    response_model=ProductionApprovalResponse,
)
def material_check(
    production_order_id: int,
    data: WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.material_check(
        production_order_id=production_order_id,
        current_user=current_user,
        comment=data.comment,
    )


@router.post(
    "/{production_order_id}/workflow/start",
    response_model=ProductionApprovalResponse,
)
def start_production(
    production_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.start_production(
        production_order_id=production_order_id,
        current_user=current_user,
    )


@router.post(
    "/{production_order_id}/workflow/quality-inspection",
    response_model=ProductionApprovalResponse,
)
def quality_inspection(
    production_order_id: int,
    data: WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.quality_inspected(
        production_order_id=production_order_id,
        current_user=current_user,
        comment=data.comment,
    )


@router.post(
    "/{production_order_id}/workflow/complete",
    response_model=ProductionApprovalResponse,
)
def complete_production(
    production_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.complete_production(
        production_order_id=production_order_id,
        current_user=current_user,
    )


@router.post(
    "/{production_order_id}/workflow/manager-approve",
    response_model=ProductionApprovalResponse,
)
def manager_approve(
    production_order_id: int,
    data: WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.manager_approve(
        production_order_id=production_order_id,
        current_user=current_user,
        comment=data.comment,
    )


@router.post(
    "/{production_order_id}/workflow/manager-reject",
    response_model=ProductionApprovalResponse,
)
def manager_reject(
    production_order_id: int,
    data: WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProductionApprovalService(db)

    return service.manager_reject(
        production_order_id=production_order_id,
        current_user=current_user,
        comment=data.comment,
    )