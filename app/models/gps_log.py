from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class GPSLocationLog(Base):
    __tablename__ = "gps_location_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=True)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True) # Precisión en metros
    speed = Column(Float, nullable=True) # Velocidad km/h
    battery_level = Column(Float, nullable=True)
    
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relaciones
    user = relationship("User", foreign_keys=[user_id])
    driver = relationship("Driver", foreign_keys=[driver_id])
    route = relationship("Route", foreign_keys=[route_id])
