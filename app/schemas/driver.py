from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DriverBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    vehicle_type: str = "MOTO"
    vehicle_plate: str
    capacity_kg: float = 50.0
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    status: str = "DISPONIBLE"
    avatar_url: Optional[str] = None
    rating: float = 5.0

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    capacity_kg: Optional[float] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    status: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: Optional[float] = None

class DriverOut(DriverBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

