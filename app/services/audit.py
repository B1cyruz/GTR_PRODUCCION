import json
from typing import Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User

def log_audit_event(
    db: Session,
    user: Optional[User] = None,
    action: str = "ACTION",
    module: str = "SYSTEM",
    target_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Any] = None,
    status: str = "SUCCESS"
) -> AuditLog:
    """
    Registra un evento estructurado en la tabla de auditoría del sistema.
    """
    try:
        user_id = user.id if user else None
        user_email = user.email if user else "ANONIMO"
        user_role = user.role if user else "PUBLIC"

        details_str = None
        if details is not None:
            if isinstance(details, (dict, list)):
                details_str = json.dumps(details, ensure_ascii=False, default=str)
            else:
                details_str = str(details)

        audit_entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            action=action,
            module=module,
            target_id=str(target_id) if target_id is not None else None,
            ip_address=ip_address,
            details=details_str,
            status=status,
            created_at=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        return audit_entry
    except Exception as e:
        # En caso de error de auditoría, no interrumpir el flujo principal
        print(f"[Audit Error] Falló el registro de auditoría: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return None
