from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.point import (
    ClientCreate,
    ClientUpdate,
    ClientOut
)
from app.services.auth import (
    get_current_user,
    get_client_ip
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/clients", tags=["Clients (Base General)"])

@router.get("", response_model=List[ClientOut])
def list_clients(
    search: Optional[str] = Query(None, description="Buscar por documento, nombre o teléfono"),
    is_active: Optional[bool] = Query(None, description="Filtrar por activos/inactivos"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consulta y busca clientes en la BASE GENERAL DEL SISTEMA.
    Accesible para ROOT, COORDINADOR y REPARTIDOR (para reutilización).
    """
    query = db.query(Client)
    if is_active is not None:
        query = query.filter(Client.is_active == is_active)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Client.name.ilike(s),
                Client.document_id.ilike(s),
                Client.phone.ilike(s),
                Client.address.ilike(s)
            )
        )
    return query.order_by(desc(Client.created_at)).limit(limit).all()

@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el detalle de un cliente."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client

@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registra un nuevo cliente en la BASE GENERAL.
    Valida si ya existe por documento o teléfono para evitar duplicados.
    """
    # 1. Validar por documento si se proporcionó
    if payload.document_id:
        doc = payload.document_id.strip()
        existing_doc = db.query(Client).filter(Client.document_id == doc).first()
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente registrado con el documento {doc} ({existing_doc.name})"
            )

    new_client = Client(
        name=payload.name.strip(),
        document_id=payload.document_id.strip() if payload.document_id else None,
        phone=payload.phone.strip(),
        email=payload.email.strip() if payload.email else None,
        address=payload.address.strip() if payload.address else None,
        neighborhood=payload.neighborhood.strip() if payload.neighborhood else None,
        city=payload.city.strip() if payload.city else "Cartagena",
        notes=payload.notes,
        is_active=payload.is_active,
        created_by_user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    log_audit_event(
        db=db,
        user=current_user,
        action="CREATE_CLIENT",
        module="CLIENTS",
        target_id=str(new_client.id),
        ip_address=get_client_ip(request),
        details={"name": new_client.name, "doc": new_client.document_id, "phone": new_client.phone},
        status="SUCCESS"
    )

    return new_client

@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza la información operativa de un cliente en la Base General."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if payload.name is not None:
        client.name = payload.name.strip()
    if payload.document_id is not None:
        client.document_id = payload.document_id.strip()
    if payload.phone is not None:
        client.phone = payload.phone.strip()
    if payload.email is not None:
        client.email = payload.email.strip()
    if payload.address is not None:
        client.address = payload.address.strip()
    if payload.neighborhood is not None:
        client.neighborhood = payload.neighborhood.strip()
    if payload.city is not None:
        client.city = payload.city.strip()
    if payload.notes is not None:
        client.notes = payload.notes
    if payload.is_active is not None:
        client.is_active = payload.is_active

    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)

    log_audit_event(
        db=db,
        user=current_user,
        action="UPDATE_CLIENT",
        module="CLIENTS",
        target_id=str(client.id),
        ip_address=get_client_ip(request),
        details={"client_id": client.id, "name": client.name},
        status="SUCCESS"
    )

    return client
