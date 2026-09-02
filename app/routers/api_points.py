import os
import uuid
import base64
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.database import get_db
from app.models.delivery_point import DeliveryPoint, DeliveryPointHistory
from app.models.delivery import Delivery
from app.models.client import Client
from app.models.user import User
from app.schemas.point import (
    DeliveryPointCreate,
    DeliveryPointUpdate,
    DeliveryPointOut,
    NearbyPointOut,
    DeliveryPointHistoryOut
)
from app.services.auth import (
    get_current_user,
    require_all_roles,
    get_client_ip
)
from app.services.geo import (
    haversine_distance_meters,
    find_nearby_delivery_points
)
from app.services.audit import log_audit_event

def save_point_photo(photo_data: Optional[str], point_id: Optional[int] = None) -> Optional[str]:
    """Decodifica y almacena una imagen base64 capturada desde la cámara móvil como evidencia del punto GPS."""
    if not photo_data:
        return None
    if photo_data.startswith("data:image"):
        try:
            format_part, imgstr = photo_data.split(";base64,")
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
            points_dir = os.path.join(static_dir, "uploads", "points")
            os.makedirs(points_dir, exist_ok=True)

            prefix = f"point_{point_id}_" if point_id else "point_"
            filename = f"{prefix}{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}.{ext}"
            filepath = os.path.join(points_dir, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(imgstr))

            return f"/static/uploads/points/{filename}"
        except Exception as e:
            print(f"Error decodificando foto de punto GPS: {e}")
            return photo_data[:480]
    elif photo_data.startswith("/static/") or photo_data.startswith("http"):
        return photo_data
    return None

router = APIRouter(prefix="/api/points", tags=["Delivery Points & GPS (Base General)"])

@router.get("", response_model=List[DeliveryPointOut])
def list_delivery_points(
    search: Optional[str] = Query(None, description="Buscar por nombre, dirección o cliente"),
    neighborhood: Optional[str] = Query(None, description="Filtrar por barrio"),
    client_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    status_filter: Optional[str] = Query("ACTIVO", description="Estado del punto"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los puntos de entrega de la BASE GENERAL compartida del sistema.
    Accesible para ROOT, COORDINADOR y REPARTIDOR.
    """
    query = db.query(DeliveryPoint)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(DeliveryPoint.status == status_filter.upper())
    if client_id:
        query = query.filter(DeliveryPoint.client_id == client_id)
    if neighborhood:
        query = query.filter(DeliveryPoint.neighborhood.ilike(f"%{neighborhood.strip()}%"))
    if search:
        s = f"%{search.strip()}%"
        query = query.join(Client, DeliveryPoint.client_id == Client.id, isouter=True).filter(
            or_(
                DeliveryPoint.name.ilike(s),
                DeliveryPoint.address.ilike(s),
                DeliveryPoint.reference_point.ilike(s),
                Client.name.ilike(s),
                Client.document_id.ilike(s)
            )
        )
    return query.order_by(desc(DeliveryPoint.created_at)).limit(limit).all()

@router.get("/nearby", response_model=List[NearbyPointOut])
def check_nearby_points(
    latitude: float = Query(..., description="Latitud GPS actual"),
    longitude: float = Query(..., description="Longitud GPS actual"),
    radius: float = Query(50.0, description="Radio de proximidad en metros (por defecto 50m)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detecta puntos existentes en la Base General dentro del radio especificado (50 metros)
    para alertar sobre posibles duplicados antes de guardar un nuevo punto.
    """
    nearby = find_nearby_delivery_points(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius,
        limit=5
    )
    return nearby

@router.get("/{point_id}", response_model=DeliveryPointOut)
def get_delivery_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el detalle de un punto de entrega."""
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Punto de entrega no encontrado")
    return point

@router.get("/{point_id}/history", response_model=List[DeliveryPointHistoryOut])
def get_point_history(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el historial de modificaciones y trazabilidad GPS de un punto."""
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Punto no encontrado")

    history_entries = db.query(DeliveryPointHistory).filter(
        DeliveryPointHistory.delivery_point_id == point_id
    ).order_by(desc(DeliveryPointHistory.created_at)).all()

    results = []
    for h in history_entries:
        user_name = h.user.full_name if h.user else "Sistema"
        results.append(DeliveryPointHistoryOut(
            id=h.id,
            delivery_point_id=h.delivery_point_id,
            user_id=h.user_id,
            user_name=user_name,
            action=h.action,
            previous_latitude=h.previous_latitude,
            previous_longitude=h.previous_longitude,
            new_latitude=h.new_latitude,
            new_longitude=h.new_longitude,
            gps_accuracy=h.gps_accuracy,
            photo_url=h.photo_url,
            notes=h.notes,
            created_at=h.created_at
        ))
    return results

@router.post("", response_model=DeliveryPointOut, status_code=status.HTTP_201_CREATED)
def create_delivery_point(
    payload: DeliveryPointCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registra un punto GPS de entrega en la BASE GENERAL DEL SISTEMA.
    Flujo:
    1. Si no viene client_id, busca o crea el cliente evitando duplicados.
    2. Valida duplicados cercanos si no se fuerza la creación.
    3. Guarda el punto asociándolo al usuario actual con foto de la dirección real y coordenadas GPS.
    4. Crea registro de trazabilidad en el historial y auditoría.
    """
    target_client_id = payload.client_id

    # Si no se pasó client_id pero sí información de cliente, buscar o crear
    if not target_client_id and (payload.client_name or payload.client_document or payload.client_phone):
        # 1. Buscar por documento
        client = None
        if payload.client_document:
            client = db.query(Client).filter(Client.document_id == payload.client_document.strip()).first()
        
        # 2. Buscar por teléfono o nombre
        if not client and payload.client_phone:
            client = db.query(Client).filter(Client.phone == payload.client_phone.strip()).first()

        if not client and payload.client_name:
            client = db.query(Client).filter(Client.name.ilike(payload.client_name.strip())).first()

        # Si no existe, crear cliente nuevo en la base general
        if not client:
            client = Client(
                name=payload.client_name.strip() if payload.client_name else "Cliente General",
                document_id=payload.client_document.strip() if payload.client_document else None,
                phone=payload.client_phone.strip() if payload.client_phone else "3000000000",
                address=payload.address.strip(),
                neighborhood=payload.neighborhood or "Cartagena",
                city=payload.city or "Cartagena",
                notes=payload.notes,
                created_by_user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.add(client)
            db.flush()
        
        target_client_id = client.id

    # Validación de duplicados por proximidad GPS y dirección si no se ha forzado
    if not payload.force_create_duplicate:
        nearby = find_nearby_delivery_points(db, payload.latitude, payload.longitude, radius_meters=50.0)
        
        # Comprobar también duplicados existentes por coincidencia de dirección exacta
        if payload.address:
            match_addr = db.query(DeliveryPoint).filter(
                DeliveryPoint.address.ilike(payload.address.strip()),
                DeliveryPoint.status != "INACTIVO"
            ).all()
            for m in match_addr:
                if not any(n.get("point_id") == m.id for n in nearby):
                    dist = haversine_distance_meters(payload.latitude, payload.longitude, m.latitude, m.longitude)
                    nearby.append({
                        "point_id": m.id,
                        "name": m.name,
                        "address": m.address,
                        "neighborhood": m.neighborhood,
                        "city": m.city,
                        "reference_point": m.reference_point,
                        "latitude": m.latitude,
                        "longitude": m.longitude,
                        "distance_meters": round(dist, 1),
                        "photo_url": m.photo_url,
                        "client_id": m.client_id,
                        "client_name": m.client.name if m.client else None,
                        "client_document": m.client.document_id if m.client else None,
                        "client_phone": m.client.phone if m.client else None,
                        "updated_at": (m.updated_at or m.created_at).isoformat() if (m.updated_at or m.created_at) else None
                    })

        if nearby:
            # Si hay un punto a menos de 50 metros o coincidencia de dirección, advertir
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Se encontró un punto registrado cerca de esta ubicación (menos de 50m) o con la misma dirección.",
                    "duplicate_warning": True,
                    "nearby_points": nearby
                }
            )

    # Procesar y guardar fotografía del sitio/fachada si fue capturada por la cámara
    saved_photo_url = save_point_photo(payload.photo_data) or payload.photo_url

    new_point = DeliveryPoint(
        client_id=target_client_id,
        name=payload.name.strip(),
        address=payload.address.strip(),
        neighborhood=payload.neighborhood or "Cartagena",
        city=payload.city or "Cartagena",
        reference_point=payload.reference_point,
        latitude=payload.latitude,
        longitude=payload.longitude,
        gps_accuracy=payload.gps_accuracy,
        location_source=payload.location_source or "GPS_DEVICE",
        status=payload.status or "ACTIVO",
        notes=payload.notes,
        photo_url=saved_photo_url,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_point)
    db.flush()

    # Si viene delivery_id, asociar el punto a la entrega
    if payload.delivery_id:
        delivery_obj = db.query(Delivery).filter(Delivery.id == payload.delivery_id).first()
        if delivery_obj:
            delivery_obj.delivery_point_id = new_point.id

    # Registro de Trazabilidad en el Historial del Punto
    history_entry = DeliveryPointHistory(
        delivery_point_id=new_point.id,
        user_id=current_user.id,
        action="CREACION",
        previous_latitude=None,
        previous_longitude=None,
        new_latitude=new_point.latitude,
        new_longitude=new_point.longitude,
        gps_accuracy=new_point.gps_accuracy,
        photo_url=saved_photo_url,
        notes=f"Punto registrado por {current_user.full_name} ({current_user.role}). Fuente: {new_point.location_source}",
        created_at=datetime.utcnow()
    )
    db.add(history_entry)
    db.commit()
    db.refresh(new_point)

    # Registro de Auditoría General
    log_audit_event(
        db=db,
        user=current_user,
        action="CREATE_GPS_POINT",
        module="POINTS",
        target_id=str(new_point.id),
        ip_address=get_client_ip(request),
        details={
            "point_id": new_point.id,
            "name": new_point.name,
            "lat": new_point.latitude,
            "lng": new_point.longitude,
            "accuracy": new_point.gps_accuracy,
            "client_id": new_point.client_id,
            "photo_url": new_point.photo_url,
            "driver_name": current_user.full_name
        },
        status="SUCCESS"
    )

    return new_point

@router.put("/{point_id}", response_model=DeliveryPointOut)
def update_delivery_point(
    point_id: int,
    payload: DeliveryPointUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la información operativa, fotografía del sitio o corrige las coordenadas GPS de un punto existente.
    Guarda automáticamente la trazabilidad del cambio de coordenadas en el historial.
    """
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Punto de entrega no encontrado")

    old_lat = point.latitude
    old_lng = point.longitude
    gps_changed = False

    if payload.name is not None:
        point.name = payload.name.strip()
    if payload.address is not None:
        point.address = payload.address.strip()
    if payload.neighborhood is not None:
        point.neighborhood = payload.neighborhood.strip()
    if payload.city is not None:
        point.city = payload.city.strip()
    if payload.reference_point is not None:
        point.reference_point = payload.reference_point
    if payload.client_id is not None:
        point.client_id = payload.client_id
    if payload.status is not None:
        point.status = payload.status
    if payload.notes is not None:
        point.notes = payload.notes

    # Si se envía una nueva fotografía desde la cámara o URL
    if payload.photo_data is not None:
        saved_photo = save_point_photo(payload.photo_data, point_id=point.id)
        if saved_photo:
            point.photo_url = saved_photo
    elif payload.photo_url is not None:
        point.photo_url = payload.photo_url

    if payload.latitude is not None and payload.longitude is not None:
        if old_lat != payload.latitude or old_lng != payload.longitude:
            gps_changed = True
            point.latitude = payload.latitude
            point.longitude = payload.longitude
            if payload.gps_accuracy is not None:
                point.gps_accuracy = payload.gps_accuracy
            if payload.location_source is not None:
                point.location_source = payload.location_source

    point.updated_by_user_id = current_user.id
    point.updated_at = datetime.utcnow()

    # Si cambiaron las coordenadas GPS o datos clave, registrar en historial
    history_entry = DeliveryPointHistory(
        delivery_point_id=point.id,
        user_id=current_user.id,
        action="ACTUALIZACION_GPS" if gps_changed else "EDICION_DATOS",
        previous_latitude=old_lat,
        previous_longitude=old_lng,
        new_latitude=point.latitude,
        new_longitude=point.longitude,
        gps_accuracy=point.gps_accuracy,
        photo_url=point.photo_url,
        notes=f"Actualizado por {current_user.full_name} ({current_user.role}). Notas: {payload.notes or 'Actualización de datos y coordenadas'}",
        created_at=datetime.utcnow()
    )
    # Si viene delivery_id, asociar el punto a la entrega
    if payload.delivery_id:
        delivery_obj = db.query(Delivery).filter(Delivery.id == payload.delivery_id).first()
        if delivery_obj:
            delivery_obj.delivery_point_id = point.id

    db.add(history_entry)
    db.commit()
    db.refresh(point)

    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_GPS_POINT",
        module="POINTS",
        target_id=str(point.id),
        ip_address=get_client_ip(request),
        details={
            "point_id": point.id,
            "old_lat": old_lat,
            "old_lng": old_lng,
            "new_lat": point.latitude,
            "new_lng": point.longitude,
            "photo_url": point.photo_url,
            "gps_changed": gps_changed,
            "driver_name": current_user.full_name
        },
        status="SUCCESS"
    )

    return point
