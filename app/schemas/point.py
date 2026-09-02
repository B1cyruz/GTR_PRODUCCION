from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# --- Schemas de Cliente ---
class ClientBase(BaseModel):
    name: str
    document_id: Optional[str] = None
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str = "Cartagena"
    notes: Optional[str] = None
    is_active: bool = True

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    document_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class ClientOut(ClientBase):
    id: int
    created_by_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Schemas de Puntos de Entrega ---
class DeliveryPointBase(BaseModel):
    name: str
    address: str
    neighborhood: Optional[str] = "Cartagena"
    city: str = "Cartagena"
    reference_point: Optional[str] = None
    latitude: float
    longitude: float
    gps_accuracy: Optional[float] = None
    location_source: str = "GPS_DEVICE"
    status: str = "ACTIVO"
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    client_id: Optional[int] = None

class DeliveryPointCreate(DeliveryPointBase):
    # Permite crear el cliente al vuelo si no existe
    client_name: Optional[str] = None
    client_document: Optional[str] = None
    client_phone: Optional[str] = None
    delivery_id: Optional[int] = None # Para vincular automáticamente al envío actual
    force_create_duplicate: bool = False # Para confirmar si se desea crear a pesar de advertencia de duplicado
    photo_data: Optional[str] = None # Imagen base64 capturada con la cámara del dispositivo móvil

class DeliveryPointUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    reference_point: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy: Optional[float] = None
    location_source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    photo_data: Optional[str] = None # Para actualizar fotografía desde la cámara
    client_id: Optional[int] = None
    delivery_id: Optional[int] = None

class NearbyPointOut(BaseModel):
    point_id: int
    name: str
    address: str
    neighborhood: Optional[str]
    city: str
    reference_point: Optional[str]
    latitude: float
    longitude: float
    distance_meters: float
    photo_url: Optional[str] = None
    client_id: Optional[int]
    client_name: Optional[str]
    client_document: Optional[str]
    client_phone: Optional[str]
    updated_at: Optional[datetime]

class DeliveryPointHistoryOut(BaseModel):
    id: int
    delivery_point_id: int
    user_id: Optional[int]
    user_name: Optional[str] = None
    action: str
    previous_latitude: Optional[float]
    previous_longitude: Optional[float]
    new_latitude: float
    new_longitude: float
    gps_accuracy: Optional[float]
    photo_url: Optional[str] = None
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryPointOut(DeliveryPointBase):
    id: int
    created_by_user_id: Optional[int]
    created_by_user_name: Optional[str] = None
    created_by_user_role: Optional[str] = None
    updated_by_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    client: Optional[ClientOut] = None

    class Config:
        from_attributes = True

