from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import os

from app.database import get_db
from app.models.delivery import Delivery
from app.models.delivery_point import DeliveryPoint, DeliveryPointHistory
from app.models.client import Client
from app.models.route import Route, RouteStop
from app.models.driver import Driver
from app.models.user import User
from app.models.audit import AuditLog
from app.models.system_setting import SystemSetting
from app.services.auth import get_current_user_optional, get_default_redirect_for_role
from app.config import settings

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(include_in_schema=False)

def get_global_stats(db: Session):
    total_deliveries = db.query(Delivery).count()
    pending_deliveries = db.query(Delivery).filter(Delivery.status == "PENDIENTE").count()
    assigned_deliveries = db.query(Delivery).filter(Delivery.status.in_(["ASIGNADO", "EN_CAMINO"])).count()
    delivered_count = db.query(Delivery).filter(Delivery.status == "ENTREGADO").count()
    incident_count = db.query(Delivery).filter(Delivery.status == "INCIDENCIA").count()
    drivers = db.query(Driver).all()
    active_drivers = [d for d in drivers if d.status == "EN_RUTA"]
    total_points = db.query(DeliveryPoint).count()
    total_clients = db.query(Client).count()
    return {
        "total_deliveries": total_deliveries,
        "pending_deliveries": pending_deliveries,
        "assigned_deliveries": assigned_deliveries,
        "delivered_count": delivered_count,
        "incident_count": incident_count,
        "total_drivers": len(drivers),
        "active_drivers": len(active_drivers),
        "total_points": total_points,
        "total_clients": total_clients,
        "drivers_list": drivers
    }


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user.role == "REPARTIDOR":
        return RedirectResponse(url="/repartidor/ruta-activa", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    efficiency_rate = round((stats["delivered_count"] / (stats["total_deliveries"] or 1)) * 100, 1)

    recent_deliveries = db.query(Delivery).order_by(Delivery.id).all()
    drivers = db.query(Driver).order_by(Driver.id).all()
    active_routes = db.query(Route).filter(Route.status.in_(["OPTIMIZADA", "EN_PROGRESO"])).all()

    driver_summaries = []
    for driver in drivers:
        active_route = db.query(Route).filter(Route.driver_id == driver.id).order_by(desc(Route.created_at)).first()
        stops = []
        if active_route:
            stops = db.query(RouteStop).filter(RouteStop.route_id == active_route.id).order_by(RouteStop.sequence_order).all()
        
        delivered_c = sum(1 for s in stops if s.status == "COMPLETADO" or (s.delivery and s.delivery.status == "ENTREGADO"))
        in_transit_c = sum(1 for s in stops if s.status == "EN_CAMINO" or (s.delivery and s.delivery.status == "EN_CAMINO"))
        incident_c = sum(1 for s in stops if s.status == "INCIDENCIA" or (s.delivery and s.delivery.status == "INCIDENCIA"))
        pending_c = max(0, len(stops) - delivered_c - in_transit_c - incident_c)
        progress_pct = round((delivered_c / len(stops) * 100)) if stops else 0

        driver_summaries.append({
            "driver": driver,
            "route": active_route,
            "stops": stops,
            "total_packages": len(stops),
            "delivered_count": delivered_c,
            "in_transit_count": in_transit_c,
            "incident_count": incident_c,
            "pending_count": pending_c,
            "progress_pct": progress_pct
        })

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "kpis": {
                "total": stats["total_deliveries"],
                "delivered": stats["delivered_count"],
                "in_transit": stats["assigned_deliveries"],
                "incidents": stats["incident_count"],
                "pending": stats["pending_deliveries"],
                "efficiency": efficiency_rate,
                "active_drivers_count": stats["active_drivers"],
                "total_drivers_count": stats["total_drivers"],
                "total_points": stats["total_points"],
                "total_clients": stats["total_clients"]
            },
            "deliveries": recent_deliveries,
            "drivers": drivers,
            "driver_summaries": driver_summaries,
            "active_routes": active_routes
        }
    )

@router.get("/coordinacion", response_class=HTMLResponse)
@router.get("/despacho", response_class=HTMLResponse)
@router.get("/coordinador", response_class=HTMLResponse)
def coordinator_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user.role == "REPARTIDOR":
        return RedirectResponse(url="/repartidor/ruta-activa", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    all_deliveries = db.query(Delivery).order_by(desc(Delivery.created_at)).all()
    drivers = db.query(Driver).all()
    active_routes = db.query(Route).filter(Route.status.in_(["OPTIMIZADA", "EN_PROGRESO"])).all()

    return templates.TemplateResponse(
        request=request,
        name="coordinator.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "deliveries": all_deliveries,
            "drivers": drivers,
            "active_routes": active_routes
        }
    )

@router.get("/rutas/optimizar", response_class=HTMLResponse)
@router.get("/optimizer", response_class=HTMLResponse)
def route_optimizer_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user.role == "REPARTIDOR":
        return RedirectResponse(url="/repartidor/ruta-activa", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    pending_deliveries = db.query(Delivery).filter(Delivery.status == "PENDIENTE").all()
    drivers = db.query(Driver).filter(Driver.status.in_(["DISPONIBLE", "EN_RUTA"])).all()
    existing_routes = db.query(Route).order_by(desc(Route.created_at)).limit(5).all()

    return templates.TemplateResponse(
        request=request,
        name="route_optimizer.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "pending_deliveries": pending_deliveries,
            "drivers": drivers,
            "existing_routes": existing_routes
        }
    )

@router.get("/entregas/nueva", response_class=HTMLResponse)
@router.get("/deliveries/new", response_class=HTMLResponse)
def new_delivery_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user.role == "REPARTIDOR":
        return RedirectResponse(url="/repartidor/ruta-activa", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    recent_deliveries = db.query(Delivery).order_by(desc(Delivery.created_at)).limit(6).all()
    return templates.TemplateResponse(
        request=request,
        name="new_delivery.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "recent_deliveries": recent_deliveries
        }
    )

# --- VISTA: GESTIÓN DE USUARIOS (ROOT ONLY) ---
@router.get("/usuarios", response_class=HTMLResponse)
@router.get("/users", response_class=HTMLResponse)
def users_management_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Protección estricta: Solo ROOT puede acceder
    if current_user.role != "ROOT":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    all_users = db.query(User).order_by(desc(User.created_at)).all()
    drivers = db.query(Driver).all()

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "users": all_users,
            "drivers": drivers
        }
    )

# --- VISTA: AUDITORÍA DEL SISTEMA (ROOT ONLY) ---
@router.get("/auditoria", response_class=HTMLResponse)
@router.get("/audit", response_class=HTMLResponse)
def audit_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Protección estricta: Solo ROOT puede acceder
    if current_user.role != "ROOT":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    recent_logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(150).all()

    return templates.TemplateResponse(
        request=request,
        name="audit.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "logs": recent_logs
        }
    )

# --- VISTA: BASE GENERAL DE PUNTOS Y CLIENTES ---
@router.get("/puntos", response_class=HTMLResponse)
@router.get("/clientes", response_class=HTMLResponse)
def delivery_points_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user.role == "REPARTIDOR":
        return RedirectResponse(url="/repartidor/ruta-activa", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    points = db.query(DeliveryPoint).order_by(desc(DeliveryPoint.created_at)).all()
    clients = db.query(Client).order_by(desc(Client.created_at)).all()

    return templates.TemplateResponse(
        request=request,
        name="points.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "points": points,
            "clients": clients
        }
    )

@router.get("/repartidor/ruta-activa", response_class=HTMLResponse)
@router.get("/driver-app", response_class=HTMLResponse)
def driver_mobile_view(request: Request, route_id: int = None, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    stats = get_global_stats(db)
    
    route = None
    if route_id:
        route = db.query(Route).filter(Route.id == route_id).first()
    elif current_user.driver_id:
        # Buscar la ruta del conductor asignado a este usuario repartidor
        route = db.query(Route).filter(
            Route.driver_id == current_user.driver_id,
            Route.status.in_(["EN_PROGRESO", "OPTIMIZADA"])
        ).order_by(desc(Route.created_at)).first()
        
        if not route:
            # Si no hay ruta en progreso, buscar la última ruta del conductor
            route = db.query(Route).filter(Route.driver_id == current_user.driver_id).order_by(desc(Route.created_at)).first()
    
    # Si aún no hay ruta o es usuario ROOT/COORDINADOR inspeccionando la app móvil
    if not route:
        route = db.query(Route).filter(Route.status.in_(["EN_PROGRESO", "OPTIMIZADA"])).order_by(desc(Route.created_at)).first()
        if not route:
            route = db.query(Route).order_by(desc(Route.created_at)).first()

    stops = []
    driver = None
    if route:
        stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).order_by(RouteStop.sequence_order).all()
        driver = route.driver
    elif current_user.driver_id:
        driver = db.query(Driver).filter(Driver.id == current_user.driver_id).first()

    # Obtener clientes para sugerencias en el modal de registro de punto GPS
    clients_list = db.query(Client).filter(Client.is_active == True).order_by(Client.name).limit(50).all()

    return templates.TemplateResponse(
        request=request,
        name="driver_mobile.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "sidebar_stats": stats,
            "route": route,
            "stops": stops,
            "driver": driver,
            "clients": clients_list
        }
    )
