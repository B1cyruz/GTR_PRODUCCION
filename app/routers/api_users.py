from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.delivery_point import DeliveryPoint, DeliveryPointHistory
from app.models.client import Client
from app.models.audit import AuditLog
from app.models.gps_log import GPSLocationLog
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    UserPasswordReset,
    UserToggleStatus
)
from app.services.auth import (
    require_root_user,
    get_password_hash,
    can_manage_target_user,
    get_client_ip
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/users", tags=["Users Management (ROOT)"])

@router.get("", response_model=List[UserOut])
def list_users(
    role: Optional[str] = Query(None, description="Filtrar por rol: ROOT, COORDINADOR, REPARTIDOR"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    search: Optional[str] = Query(None, description="Buscar por nombre o correo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Obtiene la lista de todos los usuarios registrados en el sistema (Solo ROOT)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.upper())
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (User.email.ilike(s)))
        
    return query.order_by(desc(User.created_at)).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Obtiene el detalle de un usuario específico."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Crea un nuevo usuario en el sistema con rol asignado (Solo ROOT)."""
    email_clean = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este correo electrónico")

    role_clean = payload.role.upper().strip()
    if role_clean not in ["ROOT", "COORDINADOR", "REPARTIDOR"]:
        raise HTTPException(status_code=400, detail="Rol inválido. Debe ser ROOT, COORDINADOR o REPARTIDOR")

    driver_id = payload.driver_id if role_clean == "REPARTIDOR" else None

    new_user = User(
        email=email_clean,
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=role_clean,
        phone=payload.phone,
        driver_id=driver_id,
        is_active=payload.is_active,
        provider="LOCAL",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auditoría
    log_audit_event(
        db=db,
        user=current_user,
        action="CREATE_USER",
        module="USERS",
        target_id=str(new_user.id),
        ip_address=get_client_ip(request),
        details={"email": new_user.email, "role": new_user.role, "full_name": new_user.full_name},
        status="SUCCESS"
    )

    return new_user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Actualiza datos, rol o información de un usuario (Solo ROOT)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not can_manage_target_user(current_user, user, payload.role):
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes para modificar este usuario")

    changes = {}
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
        changes["full_name"] = user.full_name
    if payload.email is not None:
        email_clean = payload.email.strip().lower()
        if email_clean != user.email:
            existing = db.query(User).filter(User.email == email_clean).first()
            if existing and existing.id != user.id:
                raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso")
            user.email = email_clean
            changes["email"] = user.email
    if payload.role is not None:
        role_clean = payload.role.upper().strip()
        if role_clean not in ["ROOT", "COORDINADOR", "REPARTIDOR"]:
            raise HTTPException(status_code=400, detail="Rol inválido")
        # Prevenir remover el último ROOT del sistema
        if user.role == "ROOT" and role_clean != "ROOT":
            root_count = db.query(User).filter(User.role == "ROOT", User.is_active == True).count()
            if root_count <= 1:
                raise HTTPException(status_code=400, detail="No se puede cambiar el rol del único administrador ROOT activo")
        user.role = role_clean
        changes["role"] = user.role
        if role_clean != "REPARTIDOR":
            user.driver_id = None

    if payload.phone is not None:
        user.phone = payload.phone.strip() if payload.phone else None
        changes["phone"] = user.phone

    if payload.driver_id is not None:
        if user.role == "REPARTIDOR":
            user.driver_id = payload.driver_id if payload.driver_id > 0 else None
        else:
            user.driver_id = None
        changes["driver_id"] = user.driver_id

    if payload.is_active is not None:
        user.is_active = payload.is_active
        changes["is_active"] = user.is_active

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)
        changes["password_updated"] = True

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_USER",
        module="USERS",
        target_id=str(user.id),
        ip_address=get_client_ip(request),
        details=changes,
        status="SUCCESS"
    )

    return user

@router.post("/{user_id}/toggle-status", response_model=UserOut)
def toggle_user_status(
    user_id: int,
    payload: UserToggleStatus,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Bloquea o desbloquea el acceso de un usuario (Solo ROOT)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta actual")

    if user.role == "ROOT" and not payload.is_active:
        root_count = db.query(User).filter(User.role == "ROOT", User.is_active == True).count()
        if root_count <= 1:
            raise HTTPException(status_code=400, detail="No se puede desactivar el único administrador ROOT activo")

    user.is_active = payload.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    action_label = "ACTIVATE_USER" if payload.is_active else "DEACTIVATE_USER"
    log_audit_event(
        db=db,
        user=current_user,
        action=action_label,
        module="USERS",
        target_id=str(user.id),
        ip_address=get_client_ip(request),
        details={"is_active": user.is_active},
        status="SUCCESS"
    )

    return user

@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Reestablece la contraseña de un usuario (Solo ROOT)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    user.hashed_password = get_password_hash(payload.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    log_audit_event(
        db=db,
        user=current_user,
        action="RESET_PASSWORD",
        module="USERS",
        target_id=str(user.id),
        ip_address=get_client_ip(request),
        details={"user_email": user.email},
        status="SUCCESS"
    )

    return {"success": True, "message": f"Contraseña actualizada para {user.email}"}

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_root_user)
):
    """Elimina permanentemente un usuario desvinculando referencias de forma segura (Solo ROOT)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta en sesión")

    if user.role == "ROOT":
        root_count = db.query(User).filter(User.role == "ROOT").count()
        if root_count <= 1:
            raise HTTPException(status_code=400, detail="No se puede eliminar el único administrador ROOT")

    email_bak = user.email
    name_bak = user.full_name

    try:
        # Desvincular referencias foráneas de manera segura antes de eliminar
        db.query(DeliveryPoint).filter(DeliveryPoint.created_by_user_id == user_id).update({DeliveryPoint.created_by_user_id: None}, synchronize_session=False)
        db.query(DeliveryPoint).filter(DeliveryPoint.updated_by_user_id == user_id).update({DeliveryPoint.updated_by_user_id: None}, synchronize_session=False)
        db.query(DeliveryPointHistory).filter(DeliveryPointHistory.user_id == user_id).update({DeliveryPointHistory.user_id: None}, synchronize_session=False)
        db.query(Client).filter(Client.created_by_user_id == user_id).update({Client.created_by_user_id: None}, synchronize_session=False)
        db.query(GPSLocationLog).filter(GPSLocationLog.user_id == user_id).update({GPSLocationLog.user_id: None}, synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.user_id == user_id).update({AuditLog.user_id: None}, synchronize_session=False)

        db.delete(user)
        db.commit()

        log_audit_event(
            db=db,
            user=current_user,
            action="DELETE_USER",
            module="USERS",
            target_id=str(user_id),
            ip_address=get_client_ip(request),
            details={"deleted_user_email": email_bak, "full_name": name_bak},
            status="SUCCESS"
        )

        return {"success": True, "message": f"Usuario {name_bak} eliminado exitosamente."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")
