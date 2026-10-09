from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import (
    ProductionOrderStatus,
    UserRole,
)
from models.production_approval import ProductionApproval
from models.user import User
from repositories.production_approval_repository import (
    ProductionApprovalRepository,
)
from repositories.production_order_repository import (
    ProductionOrderRepository,
)
from schemas.production_approval import (
    ProductionWorkflowStatus,
)


class ProductionApprovalService:
    def __init__(self, db: Session):
        self.db = db

        self.repository = ProductionApprovalRepository(db)

        self.production_order_repository = (
            ProductionOrderRepository(db)
        )

    def get_or_create(
        self,
        production_order_id: int,
    ):
        order = self.production_order_repository.get_by_id(
            production_order_id
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production order not found",
            )

        approval = self.repository.get_by_order_id(
            production_order_id
        )

        if not approval:
            approval = ProductionApproval(
                production_order_id=production_order_id,
                workflow_status=(
                    ProductionWorkflowStatus
                    .PENDING_SUPERVISOR_REVIEW
                    .value
                ),
            )

            approval = self.repository.create(
                approval
            )

        return approval

    def get(
        self,
        production_order_id: int,
    ):
        return self.get_or_create(
            production_order_id
        )

    def _require_status(
        self,
        approval: ProductionApproval,
        expected_status: ProductionWorkflowStatus,
    ):
        if (
            approval.workflow_status
            != expected_status.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid workflow transition. "
                    f"Current status: "
                    f"{approval.workflow_status}. "
                    f"Required status: "
                    f"{expected_status.value}"
                ),
            )

    def supervisor_approve(
        self,
        production_order_id: int,
        current_user: User,
        comment: str | None = None,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_SUPERVISOR,
            UserRole.PRODUCTION_MANAGER,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only authorized production supervisors "
                    "can review orders"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .PENDING_SUPERVISOR_REVIEW,
        )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .SUPERVISOR_APPROVED
            .value
        )

        approval.supervisor_id = current_user.id

        approval.supervisor_reviewed_at = (
            datetime.now(timezone.utc)
        )

        approval.supervisor_comment = comment

        order = self.production_order_repository.get_by_id(
            production_order_id
        )

        if order.status == ProductionOrderStatus.DRAFT:
            order.status = (
                ProductionOrderStatus.SCHEDULED
            )

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def supervisor_reject(
        self,
        production_order_id: int,
        current_user: User,
        comment: str | None = None,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_SUPERVISOR,
            UserRole.PRODUCTION_MANAGER,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only authorized production supervisors "
                    "can reject orders"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .PENDING_SUPERVISOR_REVIEW,
        )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .SUPERVISOR_REJECTED
            .value
        )

        approval.supervisor_id = current_user.id

        approval.supervisor_reviewed_at = (
            datetime.now(timezone.utc)
        )

        approval.supervisor_comment = comment

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def material_check(
        self,
        production_order_id: int,
        current_user: User,
        comment: str | None = None,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_MANAGER,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "User is not authorized to check "
                    "material availability"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .SUPERVISOR_APPROVED,
        )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .MATERIAL_CHECKED
            .value
        )

        approval.material_checked_by_id = (
            current_user.id
        )

        approval.material_checked_at = (
            datetime.now(timezone.utc)
        )

        approval.material_comment = comment

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def start_production(
        self,
        production_order_id: int,
        current_user: User,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "User is not authorized to start "
                    "production"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .MATERIAL_CHECKED,
        )

        order = self.production_order_repository.get_by_id(
            production_order_id
        )

        if order.status != ProductionOrderStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Production order must be scheduled "
                    "before production can start"
                ),
            )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .PRODUCTION_STARTED
            .value
        )

        approval.production_started_by_id = (
            current_user.id
        )

        approval.production_started_at = (
            datetime.now(timezone.utc)
        )

        order.status = (
            ProductionOrderStatus.IN_PROGRESS
        )

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def quality_inspected(
        self,
        production_order_id: int,
        current_user: User,
        comment: str | None = None,
    ):
        if current_user.role not in (
            UserRole.QUALITY_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only quality-authorized users can "
                    "complete quality inspection"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .PRODUCTION_STARTED,
        )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .QUALITY_INSPECTED
            .value
        )

        approval.quality_inspected_by_id = (
            current_user.id
        )

        approval.quality_inspected_at = (
            datetime.now(timezone.utc)
        )

        approval.quality_comment = comment

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def complete_production(
        self,
        production_order_id: int,
        current_user: User,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "User is not authorized to complete "
                    "production"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .QUALITY_INSPECTED,
        )

        order = self.production_order_repository.get_by_id(
            production_order_id
        )

        if (
            order.status
            != ProductionOrderStatus.IN_PROGRESS
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Production order is not currently "
                    "in progress"
                ),
            )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .PENDING_MANAGER_APPROVAL
            .value
        )

        approval.production_completed_by_id = (
            current_user.id
        )

        approval.production_completed_at = (
            datetime.now(timezone.utc)
        )

        order.status = (
            ProductionOrderStatus.COMPLETED
        )

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def manager_approve(
        self,
        production_order_id: int,
        current_user: User,
        comment: str | None = None,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_MANAGER,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only production managers can approve "
                    "completed production"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .PENDING_MANAGER_APPROVAL,
        )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .MANAGER_APPROVED
            .value
        )

        approval.manager_id = current_user.id

        approval.manager_approved_at = (
            datetime.now(timezone.utc)
        )

        approval.manager_comment = comment

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def manager_reject(
        self,
        production_order_id: int,
        current_user: User,
        comment: str | None = None,
    ):
        if current_user.role not in (
            UserRole.PRODUCTION_MANAGER,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only production managers can reject "
                    "completed production"
                ),
            )

        approval = self.get_or_create(
            production_order_id
        )

        self._require_status(
            approval,
            ProductionWorkflowStatus
            .PENDING_MANAGER_APPROVAL,
        )

        approval.workflow_status = (
            ProductionWorkflowStatus
            .MANAGER_REJECTED
            .value
        )

        approval.manager_id = current_user.id

        approval.manager_approved_at = (
            datetime.now(timezone.utc)
        )

        approval.manager_comment = comment

        self.db.commit()
        self.db.refresh(approval)

        return approval