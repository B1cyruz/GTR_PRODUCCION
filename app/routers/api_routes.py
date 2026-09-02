import random
import string
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.route import Route, RouteStop
from app.models.delivery import Delivery
from app.models.driver import Driver
from app.models.user import User
from app.schemas.route import (
    RouteOptimizeRequest,
    RouteOut,
    RouteStopOut,
    StopStatusUpdate
)
from app.services.optimizer import (
    optimize_stops_tsp,
    calculate_route_metrics
)
from app.services.distribution import distribute_random_deliveries
from app.services.auth import (
    require_coordinator_or_root,
    get_current_user,
    get_client_ip
)
import os
import uuid
import base64
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/routes", tags=["Routes"])

@router.post("/distribute-random")
def distribute_random(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator_or_root)
):
    """
    Distribuye y asigna de manera aleatoria y equitativa todos los paquetes entre todos los repartidores.
    (Permitido solo para ROOT y COORDINADOR).
    """
    try:
        result = distribute_random_deliveries(db, seed_if_needed=True)
        log_audit_event(
            db=db,
            user=current_user,
            action="DISTRIBUTE_RANDOM_ROUTES",
            module="ROUTES",
            ip_address=get_client_ip(request),
            details={"routes_created": len(result.get("routes", []))},
            status="SUCCESS"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_route_code() -> str:
    now_year = datetime.utcnow().year
    num = ''.join(random.choices(string.digits, k=3))
    return f"RUT-{now_year}-{num}"

@router.get("", response_model=List[RouteOut])
def list_routes(
    status: Optional[str] = Query(None, description="Filtrar por estado: BORRADOR, OPTIMIZADA, EN_PROGRESO, FINALIZADA"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Route)
    # Si es repartidor, solo ve su ruta asignada
    if current_user.role == "REPARTIDOR" and current_user.driver_id:
        query = query.filter(Route.driver_id == current_user.driver_id)
    if status:
        query = query.filter(Route.status == status)
    return query.order_by(desc(Route.created_at)).all()

@router.get("/{route_id}", response_model=RouteOut)
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    # Validar que si es repartidor, sea su ruta
    if current_user.role == "REPARTIDOR" and current_user.driver_id and route.driver_id != current_user.driver_id:
        raise HTTPException(status_code=403, detail="No tienes autorización para consultar la ruta de otro conductor")

    return route

@router.post("/optimize")
def preview_optimized_route(
    payload: RouteOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator_or_root)
):
    """Previsualiza el ordenamiento TSP óptimo de las paradas (ROOT y COORDINADOR)."""
    if not payload.delivery_ids:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos una entrega para optimizar")

    deliveries = db.query(Delivery).filter(Delivery.id.in_(payload.delivery_ids)).all()
    if not deliveries:
        raise HTTPException(status_code=404, detail="No se encontraron las entregas especificadas")

    depot = {
        "name": payload.depot_name or "Centro Logístico GTR - Manga",
        "latitude": payload.depot_lat or 10.4075,
        "longitude": payload.depot_lng or -75.5342
    }

    deliveries_dict = [
        {
            "id": d.id,
            "tracking_code": d.tracking_code,
            "recipient_name": d.recipient_name,
            "recipient_phone": d.recipient_phone,
            "address": d.address,
            "neighborhood": d.neighborhood,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "priority": d.priority,
            "weight_kg": d.weight_kg,
            "time_window_start": d.time_window_start,
            "time_window_end": d.time_window_end,
            "package_type": d.package_type,
            "status": d.status
        }
        for d in deliveries
    ]

    # Ejecución de optimización TSP
    ordered = optimize_stops_tsp(depot, deliveries_dict)
    metrics = calculate_route_metrics(depot, ordered)

    return {
        "depot": depot,
        "metrics": {
            "total_stops": metrics["total_stops"],
            "total_distance_km": metrics["total_distance_km"],
            "estimated_duration_min": metrics["estimated_duration_min"]
        },
        "geometry": metrics["geometry"],
        "stops": metrics["stops"]
    }

@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_and_save_route(
    payload: RouteOptimizeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator_or_root)
):
    """Crea y guarda una ruta despachada (ROOT y COORDINADOR)."""
    if not payload.delivery_ids:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un punto de entrega")

    deliveries = db.query(Delivery).filter(Delivery.id.in_(payload.delivery_ids)).all()
    if not deliveries:
        raise HTTPException(status_code=404, detail="No se encontraron entregas")

    depot = {
        "name": payload.depot_name or "Centro Logístico GTR - Manga",
        "latitude": payload.depot_lat or 10.4075,
        "longitude": payload.depot_lng or -75.5342
    }

    deliveries_dict = [
        {
            "id": d.id,
            "tracking_code": d.tracking_code,
            "recipient_name": d.recipient_name,
            "recipient_phone": d.recipient_phone,
            "address": d.address,
            "neighborhood": d.neighborhood,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "priority": d.priority,
            "weight_kg": d.weight_kg,
            "time_window_start": d.time_window_start,
            "time_window_end": d.time_window_end,
            "package_type": d.package_type,
            "status": d.status
        }
        for d in deliveries
    ]

    ordered = optimize_stops_tsp(depot, deliveries_dict)
    metrics = calculate_route_metrics(depot, ordered)

    route_code = generate_route_code()
    while db.query(Route).filter(Route.code == route_code).first():
        route_code = generate_route_code()

    new_route = Route(
        code=route_code,
        name=payload.name,
        driver_id=payload.driver_id,
        total_stops=metrics["total_stops"],
        completed_stops=0,
        total_distance_km=metrics["total_distance_km"],
        estimated_duration_min=metrics["estimated_duration_min"],
        depot_name=depot["name"],
        depot_lat=depot["latitude"],
        depot_lng=depot["longitude"],
        status="OPTIMIZADA",
        route_geometry=metrics["geometry"]
    )
    db.add(new_route)
    db.flush()

    for item in metrics["stops"]:
        stop = RouteStop(
            route_id=new_route.id,
            delivery_id=item["delivery_id"],
            sequence_order=item["sequence_order"],
            estimated_arrival=item["estimated_arrival"],
            distance_from_prev_km=item["distance_from_prev_km"],
            travel_time_min=item["travel_time_min"],
            status="PENDIENTE"
        )
        db.add(stop)
        
        # Actualizar estado del paquete
        d_obj = db.query(Delivery).filter(Delivery.id == item["delivery_id"]).first()
        if d_obj:
            d_obj.status = "ASIGNADO"

    # Si hay repartidor asignado, marcarlo en ruta
    if payload.driver_id:
        driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
        if driver:
            driver.status = "EN_RUTA"

    db.commit()
    db.refresh(new_route)

    log_audit_event(
        db=db,
        user=current_user,
        action="CREATE_ROUTE",
        module="ROUTES",
        target_id=new_route.code,
        ip_address=get_client_ip(request),
        details={"route_code": new_route.code, "stops": new_route.total_stops, "driver_id": new_route.driver_id},
        status="SUCCESS"
    )

    return new_route

@router.patch("/{route_id}/status", response_model=RouteOut)
def update_route_status(
    route_id: int,
    status_str: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    if current_user.role == "REPARTIDOR" and current_user.driver_id and route.driver_id != current_user.driver_id:
        raise HTTPException(status_code=403, detail="No puedes modificar una ruta asignada a otro conductor")

    route.status = status_str
    if status_str == "EN_PROGRESO":
        route.started_at = datetime.utcnow()
    elif status_str == "FINALIZADA":
        route.finished_at = datetime.utcnow()
        if route.driver:
            route.driver.status = "DISPONIBLE"

    db.commit()
    db.refresh(route)

    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_ROUTE_STATUS",
        module="ROUTES",
        target_id=route.code,
        ip_address=get_client_ip(request),
        details={"status": status_str},
        status="SUCCESS"
    )

    return route

@router.patch("/stops/{stop_id}/status")
def update_stop_status(
    stop_id: int,
    status_str: Optional[str] = None,
    notes: Optional[str] = None,
    payload: Optional[StopStatusUpdate] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stop = db.query(RouteStop).filter(RouteStop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Parada no encontrada")

    if current_user.role == "REPARTIDOR" and current_user.driver_id and stop.route.driver_id != current_user.driver_id:
        raise HTTPException(status_code=403, detail="No puedes modificar entregas pertenecientes a la ruta de otro conductor")

    # Obtener valores ya sea del body JSON o de query params
    target_status = payload.status_str if (payload and payload.status_str) else (status_str or "COMPLETADO")
    target_notes = payload.notes if (payload and payload.notes is not None) else notes
    target_id_card = payload.recipient_id_card if (payload and payload.recipient_id_card) else None
    target_recipient_name = payload.recipient_name if (payload and payload.recipient_name) else None
    target_photo = payload.proof_photo_data if (payload and payload.proof_photo_data) else None

    stop.status = target_status
    if target_notes:
        stop.notes = target_notes

    if target_status == "COMPLETADO":
        stop.completion_time = datetime.utcnow()
        stop.delivery.status = "ENTREGADO"
        stop.delivery.delivered_at = datetime.utcnow()
        if target_id_card:
            stop.delivery.recipient_id_card = target_id_card.strip()
        if target_recipient_name:
            stop.delivery.recipient_name = target_recipient_name.strip()

        if target_photo:
            if target_photo.startswith("data:image"):
                try:
                    format_part, imgstr = target_photo.split(";base64,")
                    ext = format_part.split("/")[-1].lower()
                    if ext in ["jpeg", "jpg"]:
                        ext = "jpg"
                    elif ext == "png":
                        ext = "png"
                    elif ext == "webp":
                        ext = "webp"
                    else:
                        ext = "jpg"

                    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
                    proofs_dir = os.path.join(static_dir, "uploads", "proofs")
                    os.makedirs(proofs_dir, exist_ok=True)
                    
                    filename = f"proof_delivery_{stop.delivery_id}_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}.{ext}"
                    filepath = os.path.join(proofs_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(imgstr))
                    
                    stop.delivery.proof_photo_url = f"/static/uploads/proofs/{filename}"
                except Exception as e:
                    print(f"Error decodificando foto de entrega: {e}")
                    stop.delivery.proof_photo_url = target_photo[:480]
            else:
                stop.delivery.proof_photo_url = target_photo[:480]

    elif target_status == "EN_CAMINO":
        stop.delivery.status = "EN_CAMINO"
    elif target_status == "INCIDENCIA":
        stop.delivery.status = "INCIDENCIA"
        if target_notes:
            stop.delivery.incident_reason = target_notes

    # Recalcular conteo de paradas completadas en la ruta
    completed_count = db.query(RouteStop).filter(
        RouteStop.route_id == stop.route_id,
        RouteStop.status == "COMPLETADO"
    ).count()
    stop.route.completed_stops = completed_count

    if completed_count == stop.route.total_stops:
        stop.route.status = "FINALIZADA"
        stop.route.finished_at = datetime.utcnow()
        if stop.route.driver:
            stop.route.driver.status = "DISPONIBLE"

    db.commit()

    ip_str = get_client_ip(request) if request else "127.0.0.1"
    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_DELIVERY_STOP_STATUS",
        module="DELIVERIES",
        target_id=str(stop.delivery_id),
        ip_address=ip_str,
        details={"stop_id": stop.id, "status": target_status, "notes": target_notes, "photo_uploaded": bool(stop.delivery.proof_photo_url)},
        status="SUCCESS"
    )

    return {
        "message": "Estado de parada actualizado",
        "stop_id": stop.id,
        "status": stop.status,
        "proof_photo_url": stop.delivery.proof_photo_url
    }
