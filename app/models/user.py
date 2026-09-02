from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Roles: ROOT, COORDINADOR, REPARTIDOR
    role = Column(String(50), default="COORDINADOR", nullable=False)
    
    # Proveedor de autenticación: LOCAL, GMAIL, OUTLOOK, CORPORATIVO
    provider = Column(String(50), default="LOCAL")
    
    # Si el usuario es REPARTIDOR, vinculación con su registro en la tabla drivers
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con conductor
    driver = relationship("Driver", foreign_keys=[driver_id])
