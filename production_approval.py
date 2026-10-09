from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProductionWorkflowStatus(str, Enum):
    PENDING_SUPERVISOR_REVIEW = "Pending Supervisor Review"
    SUPERVISOR_APPROVED = "Supervisor Approved"
    MATERIAL_CHECKED = "Material Checked"
    PRODUCTION_STARTED = "Production Started"
    QUALITY_INSPECTED = "Quality Inspected"
    PRODUCTION_COMPLETED = "Production Completed"
    PENDING_MANAGER_APPROVAL = "Pending Manager Approval"
    MANAGER_APPROVED = "Manager Approved"
    SUPERVISOR_REJECTED = "Supervisor Rejected"
    MANAGER_REJECTED = "Manager Rejected"


class WorkflowCommentRequest(BaseModel):
    comment: str | None = Field(
        default=None,
        max_length=2000,
    )


class ProductionApprovalResponse(BaseModel):
    id: int
    production_order_id: int
    workflow_status: ProductionWorkflowStatus

    supervisor_id: int | None
    supervisor_reviewed_at: datetime | None
    supervisor_comment: str | None

    material_checked_by_id: int | None
    material_checked_at: datetime | None
    material_comment: str | None

    production_started_by_id: int | None
    production_started_at: datetime | None

    quality_inspected_by_id: int | None
    quality_inspected_at: datetime | None
    quality_comment: str | None

    production_completed_by_id: int | None
    production_completed_at: datetime | None

    manager_id: int | None
    manager_approved_at: datetime | None
    manager_comment: str | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )