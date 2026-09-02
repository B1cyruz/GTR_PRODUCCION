from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from app.schemas.delivery import DeliveryOut
from app.schemas.driver import DriverOut

class StopStatusUpdate(BaseModel):
    status_str: Optional[str] = "COMPLETADO"
    notes: Optional[str] = None
    recipient_id_card: Optional[str] = None
    recipient_name: Optional[str] = None
    proof_photo_data: Optional[str] = None

class RouteStopOut(BaseModel):
    id: int
    delivery_id: int
    sequence_order: int
    estimated_arrival: Optional[str] = None
    distance_from_prev_km: float = 0.0
    travel_time_min: int = 0
    status: str
    delivery: DeliveryOut

    class Config:
        from_attributes = True

class RouteBase(BaseModel):
    name: str
    driver_id: Optional[int] = None
    depot_name: str = "Centro Logístico GTR - Manga"
    depot_lat: float = 10.4075
    depot_lng: float = -75.5342

class RouteCreate(RouteBase):
    delivery_ids: List[int]


class RouteOptimizeRequest(BaseModel):
    name: str
    driver_id: Optional[int] = None
    delivery_ids: List[int]
    depot_lat: Optional[float] = 10.4075
    depot_lng: Optional[float] = -75.5342
    depot_name: Optional[str] = "Centro Logístico GTR - Manga"

class RouteOut(RouteBase):
    id: int
    code: str
    total_stops: int
    completed_stops: int
    total_distance_km: float
    estimated_duration_min: int
    status: str
    route_geometry: Optional[Any] = None
    driver: Optional[DriverOut] = None
    stops: List[RouteStopOut] = []
    created_at: datetime

    class Config:
        from_attributes = True
