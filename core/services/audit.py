import json
from typing import Optional, Dict, Any
from core.models import AuditLog, User

def get_client_ip(request) -> str:
    """Extrae la IP real del cliente considerando cabeceras de proxy inverso (Nginx)."""
    if not request:
        return "127.0.0.1"
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def log_audit_event(
    user: Optional[User],
    action: str,
    module: str,
    target_id: Optional[str] = None,
    ip_address: Optional[str] = "127.0.0.1",
    details: Optional[Dict[str, Any]] = None,
    status: str = "SUCCESS"
) -> AuditLog:
    """Registra de forma centralizada un evento de auditoría en la base de datos."""
    details_str = json.dumps(details or {}, ensure_ascii=False) if details else None
    
    log_entry = AuditLog.objects.create(
        user=user if (user and getattr(user, 'is_authenticated', False)) else None,
        action=action,
        module=module,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=ip_address,
        details_json=details_str,
        status=status
    )
    return log_entry
