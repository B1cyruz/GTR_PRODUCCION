from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    
    action = Column(String(100), nullable=False, index=True) # CREATE_USER, EDIT_USER, CREATE_POINT, UPDATE_POINT, CREATE_ROUTE, OPTIMIZE_ROUTE, ASSIGN_ROUTE, UPDATE_DELIVERY_STATUS, LOGIN, LOGOUT, FORBIDDEN_ACCESS
    module = Column(String(50), nullable=False, index=True) # AUTH, USERS, CLIENTS, POINTS, ROUTES, DELIVERIES, SYSTEM
    target_id = Column(String(100), nullable=True) # ID de la entidad afectada (ID usuario, ID punto, Código ruta/envío)
    ip_address = Column(String(100), nullable=True)
    details = Column(Text, nullable=True) # Detalle o payload JSON de la operación
    status = Column(String(50), default="SUCCESS") # SUCCESS, FAILED, FORBIDDEN
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relación
    user = relationship("User", foreign_keys=[user_id])
