from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    category = Column(String(50), default="GENERAL") # GPS, SECURITY, LOGISTICS, GENERAL
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
