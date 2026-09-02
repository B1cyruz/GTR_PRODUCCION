from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    user_role: Optional[str]
    action: str
    module: str
    target_id: Optional[str]
    ip_address: Optional[str]
    details: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
