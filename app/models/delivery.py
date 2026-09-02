from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String(50), unique=True, index=True, nullable=False) # GTR-XXXX
    
    # Vinculación opcional a Cliente y Punto de la Base General
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    delivery_point_id = Column(Integer, ForeignKey("delivery_points.id"), nullable=True, index=True)

    # Destinatario & Cliente
    recipient_name = Column(String(255), nullable=False)
    recipient_phone = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    
    # Ubicación (Cartagena y alrededores)
    address = Column(String(500), nullable=False)
    neighborhood = Column(String(100), nullable=True) # Barrio (Bocagrande, Castillogrande, Manga, etc.)
    city = Column(String(100), default="Cartagena")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    reference_point = Column(String(255), nullable=True)
    
    # Detalles del paquete y entrega
    package_type = Column(String(100), default="PAQUETE_MEDIANO") # DOCUMENTO, PAQUETE_PEQUEÑO, PAQUETE_MEDIANO, VOLUMINOSO, REFRIGERADO
    weight_kg = Column(Float, default=1.0)
    priority = Column(String(50), default="MEDIA") # ALTA, MEDIA, BAJA
    time_window_start = Column(String(10), default="08:00") # HH:MM
    time_window_end = Column(String(10), default="18:00")
    notes = Column(Text, nullable=True)
    
    # Estado del envío
    status = Column(String(50), default="PENDIENTE") # PENDIENTE, ASIGNADO, EN_CAMINO, ENTREGADO, INCIDENCIA, CANCELADO
    
    # Evidencias de entrega
    delivered_at = Column(DateTime, nullable=True)
    recipient_id_card = Column(String(50), nullable=True)
    signature_svg = Column(Text, nullable=True)
    proof_photo_url = Column(String(500), nullable=True)
    incident_reason = Column(Text, nullable=True)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    client = relationship("Client", back_populates="deliveries")
    delivery_point = relationship("DeliveryPoint", back_populates="deliveries")
    route_stop = relationship("RouteStop", back_populates="delivery", uselist=False)
