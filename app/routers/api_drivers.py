from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.driver import Driver
from app.models.user import User
from app.schemas.driver import DriverCreate, DriverOut
from app.services.auth import (
    get_current_user,
    require_coordinator_or_root,
    get_client_ip
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])

@router.get("", response_model=List[DriverOut])
def list_drivers(
    status: Optional[str] = Query(None, description="Filtrar por estado: DISPONIBLE, EN_RUTA, PAUSA"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Driver)
    if status:
        query = query.filter(Driver.status == status)
    return query.all()

@router.get("/{driver_id}", response_model=DriverOut)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado")
    return driver

@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator_or_root)
):
    driver = Driver(**payload.dict())
    db.add(driver)
    db.commit()
    db.refresh(driver)

    log_audit_event(
        db=db,
        user=current_user,
        action="CREATE_DRIVER",
        module="DRIVERS",
        target_id=str(driver.id),
        ip_address=get_client_ip(request),
        details={"name": driver.name, "vehicle": driver.vehicle_type},
        status="SUCCESS"
    )

    return driver

@router.patch("/{driver_id}/location", response_model=DriverOut)
def update_driver_location(
    driver_id: int,
    lat: float,
    lng: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado")
    driver.current_lat = lat
    driver.current_lng = lng
    db.commit()
    db.refresh(driver)
    return driver
