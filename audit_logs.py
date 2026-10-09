from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.audit_log import AuditLogResponse
from services.audit_log_service import AuditLogService
from core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuditLogService(db)

    return service.get_all(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuditLogService(db)

    audit_log = service.get_by_id(
        audit_log_id
    )

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return audit_log


@router.get(
    "/user/{user_id}",
    response_model=list[AuditLogResponse],
)
def get_user_audit_logs(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuditLogService(db)

    return service.get_by_user(
        user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/entity/{entity}/{entity_id}",
    response_model=list[AuditLogResponse],
)
def get_entity_audit_logs(
    entity: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuditLogService(db)

    return service.get_by_entity(
        entity=entity,
        entity_id=entity_id,
        skip=skip,
        limit=limit,
    )