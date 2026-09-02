import random
import string
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.delivery import Delivery
from app.models.user import User
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryUpdate,
    DeliveryStatusUpdate,
    DeliveryOut
)
from app.services.auth import (
    get_current_user,
    require_coordinator_or_root,
    get_client_ip
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/deliveries", tags=["Deliveries"])

def generate_tracking_code() -> str:
    digits = ''.join(random.choices(string.digits, k=4))
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"GTR-{digits}-{letters}"

@router.get("", response_model=List[DeliveryOut])
def list_deliveries(
    status: Optional[str] = Query(None, description="Filtrar por estado: PENDIENTE, ASIGNADO, EN_CAMINO, ENTREGADO, INCIDENCIA"),
    priority: Optional[str] = Query(None, description="Filtrar por prioridad: ALTA, MEDIA, BAJA"),
    neighborhood: Optional[str] = Query(None, description="Filtrar por barrio"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Delivery)
    if status:
        query = query.filter(Delivery.status == status)
    if priority:
        query = query.filter(Delivery.priority == priority)
    if neighborhood:
        query = query.filter(Delivery.neighborhood.ilike(f"%{neighborhood}%"))
        
    return query.order_by(desc(Delivery.created_at)).all()

@router.get("/{delivery_id}", response_model=DeliveryOut)
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return delivery

@router.post("", response_model=DeliveryOut, status_code=status.HTTP_201_CREATED)
def create_delivery(
    payload: DeliveryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator_or_root)
):
    """Registra una nueva encomienda/envío (ROOT y COORDINADOR)."""
    tracking = generate_tracking_code()
    while db.query(Delivery).filter(Delivery.tracking_code == tracking).first():
        tracking = generate_tracking_code()

    delivery = Delivery(
        tracking_code=tracking,
        recipient_name=payload.recipient_name,
        recipient_phone=payload.recipient_phone,
        recipient_email=payload.recipient_email,
        address=payload.address,
        neighborhood=payload.neighborhood or "Cartagena",
        city=payload.city or "Cartagena",
        latitude=payload.latitude,
        longitude=payload.longitude,
        reference_point=payload.reference_point,
        package_type=payload.package_type,
        weight_kg=payload.weight_kg,
        priority=payload.priority,
        time_window_start=payload.time_window_start,
        time_window_end=payload.time_window_end,
        notes=payload.notes,
        status="PENDIENTE"
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    log_audit_event(
        db=db,
        user=current_user,
        action="CREATE_DELIVERY",
        module="DELIVERIES",
        target_id=delivery.tracking_code,
        ip_address=get_client_ip(request),
        details={"tracking": delivery.tracking_code, "recipient": delivery.recipient_name},
        status="SUCCESS"
    )

    return delivery

@router.patch("/{delivery_id}/status", response_model=DeliveryOut)
def update_delivery_status(
    delivery_id: int,
    payload: DeliveryStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")

    delivery.status = payload.status
    if payload.status == "ENTREGADO":
        delivery.delivered_at = datetime.utcnow()
        if payload.recipient_id_card:
            delivery.recipient_id_card = payload.recipient_id_card
        if payload.signature_svg:
            delivery.signature_svg = payload.signature_svg
        if payload.proof_photo_url:
            delivery.proof_photo_url = payload.proof_photo_url
    elif payload.status == "INCIDENCIA":
        delivery.incident_reason = payload.incident_reason

    db.commit()
    db.refresh(delivery)

    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_DELIVERY_STATUS",
        module="DELIVERIES",
        target_id=delivery.tracking_code,
        ip_address=get_client_ip(request),
        details={"status": delivery.status},
        status="SUCCESS"
    )

    return delivery

@router.delete("/{delivery_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery(
    delivery_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator_or_root)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    trk = delivery.tracking_code
    db.delete(delivery)
    db.commit()

    log_audit_event(
        db=db,
        user=current_user,
        action="DELETE_DELIVERY",
        module="DELIVERIES",
        target_id=trk,
        ip_address=get_client_ip(request),
        details={"deleted_tracking": trk},
        status="SUCCESS"
    )

    return None
