from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "COORDINADOR" # ROOT, COORDINADOR, REPARTIDOR
    provider: Optional[str] = "LOCAL"
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    driver_id: Optional[int] = None
    is_active: bool = True

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "COORDINADOR" # ROOT, COORDINADOR, REPARTIDOR
    phone: Optional[str] = None
    driver_id: Optional[int] = None
    is_active: bool = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

    role: Optional[str] = None
    phone: Optional[str] = None
    driver_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserPasswordReset(BaseModel):
    new_password: str

class UserToggleStatus(BaseModel):
    is_active: bool

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    provider: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    driver_id: Optional[int]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
