from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class DeliveryBase(BaseModel):
    recipient_name: str
    recipient_phone: str
    recipient_email: Optional[str] = None
    address: str
    neighborhood: Optional[str] = None
    city: str = "Cartagena"
    latitude: float
    longitude: float
    reference_point: Optional[str] = None
    package_type: str = "PAQUETE_MEDIANO"
    weight_kg: float = 1.0
    priority: str = "MEDIA"
    time_window_start: str = "08:00"
    time_window_end: str = "18:00"
    notes: Optional[str] = None

class DeliveryCreate(DeliveryBase):
    pass

class DeliveryUpdate(BaseModel):
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_email: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class DeliveryStatusUpdate(BaseModel):
    status: str
    recipient_id_card: Optional[str] = None
    signature_svg: Optional[str] = None
    proof_photo_url: Optional[str] = None
    incident_reason: Optional[str] = None

class DeliveryOut(DeliveryBase):
    id: int
    tracking_code: str
    status: str
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
