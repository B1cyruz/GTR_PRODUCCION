from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SystemSettingOut(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str]
    category: str
    updated_at: datetime

    class Config:
        from_attributes = True

class SystemSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None
