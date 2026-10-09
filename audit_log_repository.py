from typing import Optional

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        action: str,
        entity: str,
        entity_id: Optional[int] = None,
        previous_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
    ) -> AuditLog:

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            previous_value=previous_value,
            new_value=new_value,
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log

    def get_by_id(
        self,
        audit_log_id: int,
    ) -> Optional[AuditLog]:

        return (
            self.db.query(AuditLog)
            .filter(AuditLog.id == audit_log_id)
            .first()
        )

    def get_all(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        entity_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ):
        query = self.db.query(AuditLog)

        if user_id is not None:
            query = query.filter(
                AuditLog.user_id == user_id
            )

        if action is not None:
            query = query.filter(
                AuditLog.action == action
            )

        if entity is not None:
            query = query.filter(
                AuditLog.entity == entity
            )

        if entity_id is not None:
            query = query.filter(
                AuditLog.entity_id == entity_id
            )

        return (
            query
            .order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ):
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_entity(
        self,
        entity: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 100,
    ):
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.entity == entity,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )