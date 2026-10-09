from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    user_id: int
    action: str
    entity: str
    entity_id: Optional[int] = None
    previous_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    entity: str
    entity_id: Optional[int]
    timestamp: datetime
    previous_value: Optional[dict[str, Any]]
    new_value: Optional[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)