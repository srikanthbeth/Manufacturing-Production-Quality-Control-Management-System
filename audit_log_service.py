from typing import Optional

from sqlalchemy.orm import Session

from repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, db: Session):
        self.repository = AuditLogRepository(db)

    def create_log(
        self,
        user_id: int,
        action: str,
        entity: str,
        entity_id: Optional[int] = None,
        previous_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
    ):
        return self.repository.create(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            previous_value=previous_value,
            new_value=new_value,
        )

    def get_by_id(
        self,
        audit_log_id: int,
    ):
        return self.repository.get_by_id(
            audit_log_id
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
        return self.repository.get_all(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            skip=skip,
            limit=limit,
        )

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ):
        return self.repository.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    def get_by_entity(
        self,
        entity: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 100,
    ):
        return self.repository.get_by_entity(
            entity=entity,
            entity_id=entity_id,
            skip=skip,
            limit=limit,
        )