import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import bcrypt
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.config import settings

# Configuración JWT
SECRET_KEY = getattr(settings, "SECRET_KEY", "gtr_super_secret_jwt_key_2026_cartagena")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
COOKIE_NAME = "gtr_session_token"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash bcrypt almacenado."""
    if not hashed_password or not plain_password:
        return False
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        # Fallback de seguridad en caso de coincidencia directa o legacy
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt seguro para la contraseña."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT firmado para la sesión del usuario."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Obtiene el usuario actual a partir de la cookie de sesión o encabezado Authorization.
    No arroja excepción si no está autenticado (retorna None).
    """
    token = request.cookies.get(COOKIE_NAME)
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    user_id = payload.get("sub")
    try:
        user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
        return user
    except Exception:
        return None

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Obtiene el usuario autenticado. Arroja excepción 401 si no hay sesión válida.
    """
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No has iniciado sesión o tu sesión ha expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_role(allowed_roles: List[str]):
    """
    Genera una dependencia que restringe el acceso solo a usuarios con roles permitidos.
    ROOT siempre tiene acceso a todo.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "").upper()
        if user_role == "ROOT":
            return current_user
        
        allowed_upper = [r.upper() for r in allowed_roles]
        if user_role not in allowed_upper:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: Se requiere rol {', '.join(allowed_roles)} (Tu rol actual es {user_role})."
            )
        return current_user
    return role_checker

require_root_user = require_role(["ROOT"])
require_coordinator_or_root = require_role(["ROOT", "COORDINADOR"])
require_all_roles = require_role(["ROOT", "COORDINADOR", "REPARTIDOR"])

def can_manage_target_user(current_user: User, target_user: User, new_role: Optional[str] = None) -> bool:
    """
    Verifica si el usuario autenticado tiene jerarquía para administrar o cambiar el rol de otro usuario.
    Reglas:
    1. Solo ROOT puede gestionar usuarios.
    2. Ningún usuario inferior puede modificar a un usuario con rol ROOT ni asignarse el rol ROOT.
    """
    c_role = (current_user.role or "").upper()
    t_role = (target_user.role or "").upper()
    
    if c_role != "ROOT":
        return False
    
    # Si el target es ROOT pero current_user es ROOT, se permite (gestión entre administradores)
    return True

def get_client_ip(request: Request) -> str:
    """Obtiene la dirección IP real del cliente considerando proxies y cabeceras."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"

def get_default_redirect_for_role(role: str) -> str:
    """Retorna la URL de inicio por defecto según el rol del usuario."""
    r = (role or "").upper()
    if r == "REPARTIDOR":
        return "/repartidor/ruta-activa"
    elif r == "COORDINADOR":
        return "/coordinacion"
    elif r in ["ROOT", "ADMIN"]:
        return "/dashboard"
    return "/dashboard"

