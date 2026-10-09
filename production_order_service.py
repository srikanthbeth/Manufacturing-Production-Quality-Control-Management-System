from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.enums import (
    AccountStatus,
    ProductStatus,
    ProductionLineStatus,
    ProductionOrderStatus,
    UserRole,
)


from models.production_order import ProductionOrder
from repositories.production_line_repository import (
    ProductionLineRepository,
)
from repositories.product_repository import ProductRepository
from repositories.production_order_repository import (
    ProductionOrderRepository,
)
from repositories.user_repository import UserRepository

from models.production_approval import ProductionApproval
from schemas.production_approval import ProductionWorkflowStatus

class ProductionOrderService:
    def __init__(self, db: Session):
        self.db = db

        self.repository = ProductionOrderRepository(db)
        self.product_repository = ProductRepository(db)
        self.production_line_repository = (
            ProductionLineRepository(db)
        )
        self.user_repository = UserRepository(db)

    def create(
        self,
        data,
    ):
        existing = self.repository.get_by_order_number(
            data.order_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Production order number already exists",
            )

        product = self.product_repository.get_by_id(
            data.product_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        if product.status != ProductStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not active",
            )

        production_line = (
            self.production_line_repository.get_by_id(
                data.production_line_id
            )
        )

        if not production_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production line not found",
            )

        if production_line.status != ProductionLineStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Production line is not active",
            )

        supervisor = self.user_repository.get_by_id(
            data.supervisor_id
        )

        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supervisor not found",
            )

        if supervisor.status != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supervisor account is inactive",
            )

        if supervisor.role not in (
            UserRole.PRODUCTION_SUPERVISOR,
            UserRole.PRODUCTION_MANAGER,
            UserRole.PLANT_MANAGER,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user is not eligible as a production supervisor",
            )

        order = ProductionOrder(
            order_number=data.order_number,
            product_id=data.product_id,
            quantity=data.quantity,
            target_date=data.target_date,
            production_line_id=data.production_line_id,
            priority=data.priority,
            supervisor_id=data.supervisor_id,
            status=ProductionOrderStatus.DRAFT,
        )

        
        self.db.add(order)
        self.db.flush()

        approval = ProductionApproval(
        production_order_id=order.id,
        workflow_status=(
        ProductionWorkflowStatus.PENDING_SUPERVISOR_REVIEW.value
             ),
            )

        self.db.add(approval)
        self.db.commit()
        self.db.refresh(order)

        return order

    def get(
        self,
        order_id: int,
    ):
        order = self.repository.get_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production order not found",
            )

        return order

    def list(
        self,
        search=None,
        product_id=None,
        production_line_id=None,
        supervisor_id=None,
        priority=None,
        status_value=None,
        page=1,
        page_size=10,
    ):
        return self.repository.list(
            search=search,
            product_id=product_id,
            production_line_id=production_line_id,
            supervisor_id=supervisor_id,
            priority=priority,
            status=status_value,
            page=page,
            page_size=page_size,
        )

    def update(
        self,
        order_id: int,
        data,
    ):
        order = self.get(order_id)

        if order.status in (
            ProductionOrderStatus.COMPLETED,
            ProductionOrderStatus.CANCELLED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed or cancelled production orders cannot be modified",
            )

        if data.product_id is not None:
            product = self.product_repository.get_by_id(
                data.product_id
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )

            if product.status != ProductStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product is not active",
                )

            order.product_id = data.product_id

        if data.production_line_id is not None:
            production_line = (
                self.production_line_repository.get_by_id(
                    data.production_line_id
                )
            )

            if not production_line:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Production line not found",
                )

            if (
                production_line.status
                != ProductionLineStatus.ACTIVE
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Production line is not active",
                )

            order.production_line_id = (
                data.production_line_id
            )

        if data.supervisor_id is not None:
            supervisor = self.user_repository.get_by_id(
                data.supervisor_id
            )

            if not supervisor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Supervisor not found",
                )

            if supervisor.status != AccountStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Supervisor account is inactive",
                )

            if supervisor.role not in (
                UserRole.PRODUCTION_SUPERVISOR,
                UserRole.PRODUCTION_MANAGER,
                UserRole.PLANT_MANAGER,
                UserRole.SUPER_ADMIN,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned user is not eligible as a production supervisor",
                )

            order.supervisor_id = data.supervisor_id

        if data.quantity is not None:
            order.quantity = data.quantity

        if data.target_date is not None:
            order.target_date = data.target_date

        if data.priority is not None:
            order.priority = data.priority

        return self.repository.update(order)

    def update_status(
        self,
        order_id: int,
        new_status: ProductionOrderStatus,
    ):
        order = self.get(order_id)

        current_status = order.status

        allowed_transitions = {
            ProductionOrderStatus.DRAFT: {
                ProductionOrderStatus.SCHEDULED,
                ProductionOrderStatus.CANCELLED,
            },
            ProductionOrderStatus.SCHEDULED: {
                ProductionOrderStatus.IN_PROGRESS,
                ProductionOrderStatus.CANCELLED,
            },
            ProductionOrderStatus.IN_PROGRESS: {
                ProductionOrderStatus.PAUSED,
                ProductionOrderStatus.COMPLETED,
                ProductionOrderStatus.CANCELLED,
            },
            ProductionOrderStatus.PAUSED: {
                ProductionOrderStatus.IN_PROGRESS,
                ProductionOrderStatus.CANCELLED,
            },
            ProductionOrderStatus.COMPLETED: set(),
            ProductionOrderStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions[
            current_status
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid production order status transition: "
                    f"{current_status.value} -> {new_status.value}"
                ),
            )

        order.status = new_status

        return self.repository.update(order)

    def delete(
        self,
        order_id: int,
    ):
        order = self.get(order_id)

        if order.status not in (
            ProductionOrderStatus.DRAFT,
            ProductionOrderStatus.CANCELLED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only draft or cancelled production orders "
                    "can be deleted"
                ),
            )

        self.repository.delete(order)