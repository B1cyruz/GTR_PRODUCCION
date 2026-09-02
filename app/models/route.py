from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # RUT-2026-001
    name = Column(String(255), nullable=False)
    
    # Asignación
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    # Métricas calculadas por el optimizador
    total_stops = Column(Integer, default=0)
    completed_stops = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    estimated_duration_min = Column(Integer, default=0)
    
    # Puntos de origen y fin (Depósito / Hub)
    depot_name = Column(String(255), default="Centro Logístico GTR - Manga")
    depot_lat = Column(Float, default=10.4075)
    depot_lng = Column(Float, default=-75.5342)
    
    # Estado de la ruta
    status = Column(String(50), default="BORRADOR") # BORRADOR, OPTIMIZADA, EN_PROGRESO, FINALIZADA, CANCELADA
    
    # Geometría OSRM / Polilínea geojson
    route_geometry = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    driver = relationship("Driver", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.sequence_order")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False)
    
    sequence_order = Column(Integer, nullable=False) # 1, 2, 3... orden optimizado
    estimated_arrival = Column(String(10), nullable=True) # HH:MM
    distance_from_prev_km = Column(Float, default=0.0)
    travel_time_min = Column(Integer, default=0)
    
    status = Column(String(50), default="PENDIENTE") # PENDIENTE, EN_CAMINO, COMPLETADO, INCIDENCIA
    arrival_time = Column(DateTime, nullable=True)
    completion_time = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relaciones
    route = relationship("Route", back_populates="stops")
    delivery = relationship("Delivery", back_populates="route_stop")
