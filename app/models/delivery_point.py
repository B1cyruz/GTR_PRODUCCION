from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class DeliveryPoint(Base):
    __tablename__ = "delivery_points"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    
    # Nombre o alias identificativo del punto
    name = Column(String(255), nullable=False) # Ej. "Sede Principal", "Ferretería Centro", "Bodega Manga"
    address = Column(String(500), nullable=False)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), default="Cartagena")
    reference_point = Column(String(255), nullable=True) # Punto de referencia (ej. "Frente al parque")
    
    # Coordenadas y Precisión GPS
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    gps_accuracy = Column(Float, nullable=True) # Precisión en metros reportada por el GPS del móvil
    location_source = Column(String(50), default="GPS_DEVICE") # GPS_DEVICE, MANUAL, GEOCODING
    status = Column(String(50), default="ACTIVO") # ACTIVO, INACTIVO, VERIFICADO
    notes = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True) # Fotografía de la fachada o dirección real
    
    # Trazabilidad de Usuarios
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    client = relationship("Client", back_populates="points")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])
    deliveries = relationship("Delivery", back_populates="delivery_point")
    history = relationship("DeliveryPointHistory", back_populates="delivery_point", cascade="all, delete-orphan", order_by="desc(DeliveryPointHistory.created_at)")

    @property
    def created_by_user_name(self) -> str:
        return self.created_by_user.full_name if self.created_by_user else "Sistema"

    @property
    def created_by_user_role(self) -> str:
        return self.created_by_user.role if self.created_by_user else "SISTEMA"


class DeliveryPointHistory(Base):
    __tablename__ = "delivery_point_history"

    id = Column(Integer, primary_key=True, index=True)
    delivery_point_id = Column(Integer, ForeignKey("delivery_points.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    action = Column(String(50), default="CREACION") # CREACION, ACTUALIZACION_GPS, EDICION_DATOS, VALIDACION
    previous_latitude = Column(Float, nullable=True)
    previous_longitude = Column(Float, nullable=True)
    new_latitude = Column(Float, nullable=False)
    new_longitude = Column(Float, nullable=False)
    gps_accuracy = Column(Float, nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relaciones
    delivery_point = relationship("DeliveryPoint", back_populates="history")
    user = relationship("User", foreign_keys=[user_id])

    @property
    def user_name(self) -> str:
        return self.user.full_name if self.user else "Sistema"


