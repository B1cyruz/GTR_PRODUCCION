from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.services.auth import require_root_user

router = APIRouter(prefix="/api/audit", tags=["Audit & Logs (ROOT)"])

@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    module: Optional[str] = Query(None, description="Filtrar por módulo (AUTH, USERS, CLIENTS, POINTS, ROUTES, DELIVERIES)"),
    action: Optional[str] = Query(None, description="Filtrar por acción"),
    user_email: Optional[str] = Query(None, description="Filtrar por correo de usuario"),
    status_filter: Optional[str] = Query(None, description="Filtrar por estado (SUCCESS, FAILED, FORBIDDEN)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """
    Obtiene los registros de auditoría del sistema (Solo ROOT).
    Permite monitorear quién realizó cada acción, fecha, hora, IP y entidad afectada.
    """
    query = db.query(AuditLog)
    if module:
        query = query.filter(AuditLog.module == module.upper())
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
    if user_email:
        query = query.filter(AuditLog.user_email.ilike(f"%{user_email.strip()}%"))
    if status_filter:
        query = query.filter(AuditLog.status == status_filter.upper())
        
    return query.order_by(desc(AuditLog.created_at)).limit(limit).all()
