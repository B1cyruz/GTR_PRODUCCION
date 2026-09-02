from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    vehicle_type = Column(String(50), default="MOTO") # MOTO, FURGON, CAMION, BICICLETA
    vehicle_plate = Column(String(20), nullable=False)
    capacity_kg = Column(Float, default=50.0)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    status = Column(String(50), default="DISPONIBLE") # DISPONIBLE, EN_RUTA, PAUSA, INACTIVO
    avatar_url = Column(String(500), nullable=True)
    rating = Column(Float, default=5.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    routes = relationship("Route", back_populates="driver")
