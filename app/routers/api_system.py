from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.schemas.system import SystemSettingOut, SystemSettingUpdate
from app.services.auth import require_root_user, get_client_ip
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/system", tags=["System Configuration (ROOT)"])

DEFAULT_SETTINGS = [
    {
        "key": "GPS_DUPLICATE_RADIUS_METERS",
        "value": "50",
        "description": "Radio de proximidad en metros para detección de puntos GPS duplicados",
        "category": "GPS"
    },
    {
        "key": "DEFAULT_CITY",
        "value": "Cartagena",
        "description": "Ciudad principal de operaciones de la flota",
        "category": "LOGISTICS"
    },
    {
        "key": "DEFAULT_DEPOT_NAME",
        "value": "Centro Logístico GTR - Manga",
        "description": "Nombre del depósito o hub central de salida",
        "category": "LOGISTICS"
    },
    {
        "key": "DEFAULT_DEPOT_LAT",
        "value": "10.4075",
        "description": "Latitud del centro logístico",
        "category": "GPS"
    },
    {
        "key": "DEFAULT_DEPOT_LNG",
        "value": "-75.5342",
        "description": "Longitud del centro logístico",
        "category": "GPS"
    }
]

def seed_system_settings_if_empty(db: Session):
    for ds in DEFAULT_SETTINGS:
        item = db.query(SystemSetting).filter(SystemSetting.key == ds["key"]).first()
        if not item:
            db.add(SystemSetting(**ds))
    db.commit()

@router.get("/settings", response_model=List[SystemSettingOut])
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Consulta todas las configuraciones del sistema (Solo ROOT)."""
    seed_system_settings_if_empty(db)
    return db.query(SystemSetting).all()

@router.put("/settings/{key}", response_model=SystemSettingOut)
def update_system_setting(
    key: str,
    payload: SystemSettingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Actualiza un parámetro de configuración global del sistema (Solo ROOT)."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(
            key=key,
            value=payload.value,
            description=payload.description,
            category="GENERAL"
        )
        db.add(setting)
    else:
        old_val = setting.value
        setting.value = payload.value
        if payload.description is not None:
            setting.description = payload.description
        setting.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(setting)

    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_SYSTEM_CONFIG",
        module="SYSTEM",
        target_id=setting.key,
        ip_address=get_client_ip(request),
        details={"key": setting.key, "value": setting.value},
        status="SUCCESS"
    )

    return setting
