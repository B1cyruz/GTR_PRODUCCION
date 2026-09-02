from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), index=True, nullable=True) # Cédula, NIT o RUT
    name = Column(String(255), index=True, nullable=False) # Nombre de la persona o Razón Social
    phone = Column(String(50), index=True, nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), default="Cartagena")
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Usuario que registró al cliente
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    points = relationship("DeliveryPoint", back_populates="client", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="client")
