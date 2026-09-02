from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models.user import User
from app.models.driver import Driver
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user_optional,
    get_current_user,
    get_default_redirect_for_role,
    COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_DAYS
)
from app.config import settings

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(tags=["Authentication"])

class LoginRequest(BaseModel):
    email_or_user: str
    password: str
    remember: bool = True

class ProviderLoginRequest(BaseModel):
    provider: str # google, outlook, corporate, demo_root, demo_coord, demo_driver
    email: Optional[str] = None
    role: Optional[str] = None

@router.get("/login", response_class=HTMLResponse)
def login_view(request: Request, db: Session = Depends(get_db)):
    """Renderiza la vista de inicio de sesión. Si el usuario ya está autenticado, lo redirige."""
    current_user = get_current_user_optional(request, db)
    if current_user:
        redirect_url = get_default_redirect_for_role(current_user.role)
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "settings": settings,
            "error": None
        }
    )

@router.post("/api/auth/login")
def api_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Autenticación tradicional mediante correo/usuario y contraseña."""
    identifier = payload.email_or_user.strip().lower()
    
    # Buscar usuario por email o prefijo
    user = db.query(User).filter(
        (User.email.ilike(identifier)) | (User.email.ilike(f"{identifier}@gtrlogistics.com"))
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifica tu correo y contraseña."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta se encuentra inactiva. Contacta al Administrador Principal."
        )

    # Actualizar último acceso
    user.last_login = datetime.utcnow()
    db.commit()

    # Generar token JWT
    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    redirect_url = get_default_redirect_for_role(user.role)

    # Configurar cookie de sesión
    max_age = ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600 if payload.remember else 24 * 3600
    
    res = JSONResponse(content={
        "success": True,
        "message": f"¡Bienvenido de nuevo, {user.full_name}!",
        "redirect_url": redirect_url,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    })
    res.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False # True en producción con HTTPS
    )
    return res

@router.post("/api/auth/provider-login")
def api_provider_login(payload: ProviderLoginRequest, db: Session = Depends(get_db)):
    """
    Inicio de sesión rápido mediante proveedores de correo (Gmail, Outlook, Corporativo) 
    o selección directa de los 3 perfiles de demostración (ROOT, Coordinador, Repartidor).
    """
    provider_name = payload.provider.lower().strip()
    target_role = "ROOT"
    user_email = ""
    full_name = ""
    driver_id = None

    if provider_name in ["demo_root", "root"]:
        user_email = "root@gtrlogistics.com"
        full_name = "Super Admin (ROOT)"
        target_role = "ROOT"
        auth_provider = "CORPORATIVO"
    elif provider_name in ["demo_coord", "coordinador", "coord"]:
        user_email = "coordinador@gtrlogistics.com"
        full_name = "Coordinador de Despacho"
        target_role = "COORDINADOR"
        auth_provider = "CORPORATIVO"
    elif provider_name in ["demo_driver", "repartidor", "driver"]:
        user_email = "jose.martinez@gtrlogistics.com"
        full_name = "José P. Martínez"
        target_role = "REPARTIDOR"
        auth_provider = "CORPORATIVO"
        first_driver = db.query(Driver).order_by(Driver.id).first()
        if first_driver:
            driver_id = first_driver.id
    elif provider_name == "google" or provider_name == "gmail":
        user_email = payload.email or "usuario.gmail@gmail.com"
        full_name = "Usuario Google (Gmail)"
        target_role = payload.role or "COORDINADOR"
        auth_provider = "GMAIL"
    elif provider_name == "outlook" or provider_name == "microsoft":
        user_email = payload.email or "usuario.outlook@outlook.com"
        full_name = "Usuario Microsoft (Outlook)"
        target_role = payload.role or "COORDINADOR"
        auth_provider = "OUTLOOK"
    elif provider_name == "corporate" or provider_name == "corporativo":
        user_email = payload.email or "operaciones@gtrlogistics.com"
        full_name = "Personal Corporativo GTR"
        target_role = payload.role or "ROOT"
        auth_provider = "CORPORATIVO"
    else:
        user_email = "root@gtrlogistics.com"
        full_name = "Administrador ROOT"
        target_role = "ROOT"
        auth_provider = "LOCAL"

    # Buscar usuario existente o crear uno nuevo para el proveedor
    user = db.query(User).filter(User.email.ilike(user_email)).first()
    if not user:
        # Asignar conductor si es repartidor
        if target_role == "REPARTIDOR" and not driver_id:
            first_driver = db.query(Driver).order_by(Driver.id).first()
            if first_driver:
                driver_id = first_driver.id

        user = User(
            email=user_email,
            full_name=full_name,
            hashed_password=get_password_hash("GTRSecurePass2026!"),
            role=target_role,
            provider=auth_provider,
            driver_id=driver_id,
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_login = datetime.utcnow()
        db.commit()

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    redirect_url = get_default_redirect_for_role(user.role)

    res = JSONResponse(content={
        "success": True,
        "message": f"Inicio de sesión exitoso como {user.role} ({user.full_name})",
        "redirect_url": redirect_url,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "provider": user.provider
        }
    })
    res.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return res

@router.get("/logout")
def logout_view():
    """Cierra la sesión del usuario y redirige a la página de login."""
    res = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie(COOKIE_NAME)
    return res

@router.post("/api/auth/logout")
def api_logout():
    """Endpoint API para cerrar sesión."""
    res = JSONResponse(content={"success": True, "message": "Sesión cerrada correctamente", "redirect_url": "/login"})
    res.delete_cookie(COOKIE_NAME)
    return res

@router.get("/api/auth/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retorna los datos del usuario actualmente autenticado."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "provider": current_user.provider,
        "driver_id": current_user.driver_id,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at
    }
