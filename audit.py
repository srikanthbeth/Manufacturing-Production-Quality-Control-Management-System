from typing import Optional

from sqlalchemy.orm import Session

from services.audit_log_service import AuditLogService


def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    entity: str,
    entity_id: Optional[int] = None,
    previous_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
):
    service = AuditLogService(db)

    return service.create_log(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        previous_value=previous_value,
        new_value=new_value,
    )


def audit_login(
    db: Session,
    user_id: int,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="LOGIN",
        entity="User",
        entity_id=user_id,
        previous_value=None,
        new_value={
            "login": "success",
        },
    )


def audit_production_order_created(
    db: Session,
    user_id: int,
    production_order_id: int,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="CREATE",
        entity="ProductionOrder",
        entity_id=production_order_id,
        previous_value=None,
        new_value=new_value,
    )


def audit_production_order_approved(
    db: Session,
    user_id: int,
    production_order_id: int,
    previous_value: dict,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="APPROVE",
        entity="ProductionOrder",
        entity_id=production_order_id,
        previous_value=previous_value,
        new_value=new_value,
    )


def audit_material_movement(
    db: Session,
    user_id: int,
    movement_id: int,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="MATERIAL_MOVEMENT",
        entity="MaterialMovement",
        entity_id=movement_id,
        previous_value=None,
        new_value=new_value,
    )


def audit_batch_creation(
    db: Session,
    user_id: int,
    batch_id: int,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="CREATE",
        entity="ProductionBatch",
        entity_id=batch_id,
        previous_value=None,
        new_value=new_value,
    )


def audit_quality_inspection(
    db: Session,
    user_id: int,
    inspection_id: int,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="QUALITY_INSPECTION",
        entity="QualityInspection",
        entity_id=inspection_id,
        previous_value=None,
        new_value=new_value,
    )


def audit_defect_creation(
    db: Session,
    user_id: int,
    defect_id: int,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="CREATE",
        entity="Defect",
        entity_id=defect_id,
        previous_value=None,
        new_value=new_value,
    )


def audit_machine_status_change(
    db: Session,
    user_id: int,
    machine_id: int,
    previous_value: dict,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="STATUS_CHANGE",
        entity="Machine",
        entity_id=machine_id,
        previous_value=previous_value,
        new_value=new_value,
    )


def audit_maintenance_record(
    db: Session,
    user_id: int,
    maintenance_id: int,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="CREATE",
        entity="Maintenance",
        entity_id=maintenance_id,
        previous_value=None,
        new_value=new_value,
    )


def audit_inventory_adjustment(
    db: Session,
    user_id: int,
    adjustment_id: int,
    previous_value: dict,
    new_value: dict,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action="INVENTORY_ADJUSTMENT",
        entity="InventoryAdjustment",
        entity_id=adjustment_id,
        previous_value=previous_value,
        new_value=new_value,
    )