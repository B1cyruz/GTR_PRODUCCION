import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.driver import Driver
from app.models.delivery import Delivery
from app.models.route import Route, RouteStop

DEFAULT_DRIVERS_DATA = [
    {
        "name": "José P. Martínez",
        "phone": "300 452 8910",
        "email": "jose.martinez@gtrlogistics.com",
        "vehicle_type": "MOTO",
        "vehicle_plate": "GTR-98E",
        "capacity_kg": 35.0,
        "current_lat": 10.4075,
        "current_lng": -75.5342,
        "status": "EN_RUTA",
        "rating": 4.9
    },
    {
        "name": "Sergio A. Salgado",
        "phone": "312 889 1234",
        "email": "sergio.salgado@gtrlogistics.com",
        "vehicle_type": "FURGON",
        "vehicle_plate": "UTL-452",
        "capacity_kg": 600.0,
        "current_lat": 10.3985,
        "current_lng": -75.5562,
        "status": "EN_RUTA",
        "rating": 4.8
    },
    {
        "name": "Juan S. Espinosa",
        "phone": "318 765 4321",
        "email": "juan.espinosa@gtrlogistics.com",
        "vehicle_type": "MOTO",
        "vehicle_plate": "BHY-11F",
        "capacity_kg": 40.0,
        "current_lat": 10.4236,
        "current_lng": -75.5501,
        "status": "EN_RUTA",
        "rating": 5.0
    },
    {
        "name": "Juan D. Amazan",
        "phone": "301 998 7766",
        "email": "juan.amazan@gtrlogistics.com",
        "vehicle_type": "CAMION",
        "vehicle_plate": "WEN-891",
        "capacity_kg": 1500.0,
        "current_lat": 10.3345,
        "current_lng": -75.4985,
        "status": "EN_RUTA",
        "rating": 4.7
    }
]

DEFAULT_DELIVERIES_DATA = [
    {
        "tracking_code": "GTR-1001-CT",
        "recipient_name": "Dra. Mariana Restrepo",
        "recipient_phone": "300 234 5678",
        "recipient_email": "mariana.restrepo@clinicacartagena.com",
        "address": "Cra. 3 # 6-10 Edificio Infinito Apto 802",
        "neighborhood": "Bocagrande",
        "city": "Cartagena",
        "latitude": 10.4012,
        "longitude": -75.5548,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 2.4,
        "priority": "ALTA"
    },
    {
        "tracking_code": "GTR-1002-CL",
        "recipient_name": "Carlos Eduardo Vélez",
        "recipient_phone": "314 556 7890",
        "recipient_email": "carlos.velez@gmail.com",
        "address": "Calle 6 # 14-45 Edificio Castillogrande Bay",
        "neighborhood": "Castillogrande",
        "city": "Cartagena",
        "latitude": 10.3915,
        "longitude": -75.5523,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.5,
        "priority": "MEDIA"
    },
    {
        "tracking_code": "GTR-1003-CH",
        "recipient_name": "Restaurante La Cevicheria",
        "recipient_phone": "301 445 6789",
        "recipient_email": "pedidos@lacevicheriacartagena.com",
        "address": "Calle Stuart # 7-14 Plaza San Diego",
        "neighborhood": "Centro Histórico",
        "city": "Cartagena",
        "latitude": 10.4262,
        "longitude": -75.5471,
        "package_type": "REFRIGERADO",
        "weight_kg": 8.0,
        "priority": "ALTA"
    },
    {
        "tracking_code": "GTR-1004-MG",
        "recipient_name": "Ing. Roberto Alarcón",
        "recipient_phone": "320 887 6543",
        "recipient_email": "roberto.alarcon@puertomanga.com",
        "address": "Calle 26 # 21-80 Edificio Puerto Manga",
        "neighborhood": "Manga",
        "city": "Cartagena",
        "latitude": 10.4110,
        "longitude": -75.5315,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 3.2,
        "priority": "MEDIA"
    },
    {
        "tracking_code": "GTR-1005-PP",
        "recipient_name": "Farmacia La Popa Central",
        "recipient_phone": "317 223 9900",
        "recipient_email": "farmacia.lapopa@redsalud.com",
        "address": "Av. Pedro de Heredia Calle 31 # 21-12",
        "neighborhood": "Pie de la Popa",
        "city": "Cartagena",
        "latitude": 10.4190,
        "longitude": -75.5280,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 4.1,
        "priority": "ALTA"
    },
    {
        "tracking_code": "GTR-1006-CR",
        "recipient_name": "Hotel Sonesta Cartagena",
        "recipient_phone": "300 998 1122",
        "recipient_email": "recepcion@sonestacartagena.com",
        "address": "Carrera 9 # 35-104 Anillo Vial",
        "neighborhood": "Crespo",
        "city": "Cartagena",
        "latitude": 10.4510,
        "longitude": -75.5120,
        "package_type": "VOLUMINOSO",
        "weight_kg": 18.5,
        "priority": "MEDIA"
    },
    {
        "tracking_code": "GTR-1007-CB",
        "recipient_name": "Sofía Gómez Del Castillo",
        "recipient_phone": "311 345 6712",
        "recipient_email": "sofia.gomez@hotmail.com",
        "address": "Calle Real del Cabrero # 41-20",
        "neighborhood": "El Cabrero",
        "city": "Cartagena",
        "latitude": 10.4350,
        "longitude": -75.5380,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 1.1,
        "priority": "BAJA"
    },
    {
        "tracking_code": "GTR-1008-MM",
        "recipient_name": "Consorcio Industrial Mamonal",
        "recipient_phone": "315 678 9012",
        "recipient_email": "logistica@mamonalindustrias.co",
        "address": "Km 5 Vía Mamonal Zona Industrial",
        "neighborhood": "Mamonal",
        "city": "Cartagena",
        "latitude": 10.3380,
        "longitude": -75.5010,
        "package_type": "VOLUMINOSO",
        "weight_kg": 45.0,
        "priority": "MEDIA"
    },
    {
        "tracking_code": "GTR-1009-AM",
        "recipient_name": "Clínica Madre Bernarda",
        "recipient_phone": "300 112 3344",
        "recipient_email": "suministros@madrebernarda.com",
        "address": "Av. Pedro de Heredia # 69-75",
        "neighborhood": "Los Alpes",
        "city": "Cartagena",
        "latitude": 10.3950,
        "longitude": -75.4920,
        "package_type": "REFRIGERADO",
        "weight_kg": 5.5,
        "priority": "ALTA"
    },
    {
        "tracking_code": "GTR-1010-CS",
        "recipient_name": "Supermercado Euro Consulado",
        "recipient_phone": "318 443 2211",
        "recipient_email": "compras@euroconsulado.com",
        "address": "Transversal 54 # 30-80",
        "neighborhood": "El Consulado",
        "city": "Cartagena",
        "latitude": 10.3980,
        "longitude": -75.5080,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 12.0,
        "priority": "MEDIA"
    },
    {
        "tracking_code": "GTR-1011-BO",
        "recipient_name": "Ferretería El Bosque",
        "recipient_phone": "301 554 9988",
        "recipient_email": "ventas@ferreteriaelbosque.com",
        "address": "Diag. 21 # 53-12",
        "neighborhood": "El Bosque",
        "city": "Cartagena",
        "latitude": 10.3870,
        "longitude": -75.5190,
        "package_type": "VOLUMINOSO",
        "weight_kg": 28.0,
        "priority": "BAJA"
    },
    {
        "tracking_code": "GTR-1012-SL",
        "recipient_name": "Almacén San Fernando",
        "recipient_phone": "310 998 7711",
        "recipient_email": "contacto@sanfernandostore.co",
        "address": "Calle 15 # 58-24",
        "neighborhood": "San Fernando",
        "city": "Cartagena",
        "latitude": 10.3810,
        "longitude": -75.4950,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 1.8,
        "priority": "MEDIA"
    },
    {
        "tracking_code": "GTR-1013-SE",
        "recipient_name": "Centro Comercial Caribe Plaza",
        "recipient_phone": "302 776 5432",
        "recipient_email": "administracion@caribeplaza.com",
        "address": "Calle 29D # 22-108",
        "neighborhood": "La Esperanza",
        "city": "Cartagena",
        "latitude": 10.4125,
        "longitude": -75.5240,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.3,
        "priority": "ALTA"
    },
    {
        "tracking_code": "GTR-1014-PI",
        "recipient_name": "Hotel Las Américas",
        "recipient_phone": "315 221 4433",
        "recipient_email": "concierge@hotelamericas.com",
        "address": "Sector Cielo Mar Calle 15 # 1-05",
        "neighborhood": "La Boquilla",
        "city": "Cartagena",
        "latitude": 10.4690,
        "longitude": -75.5030,
        "package_type": "REFRIGERADO",
        "weight_kg": 6.4,
        "priority": "ALTA"
    },
    {
        "tracking_code": "GTR-1015-MZ",
        "recipient_name": "Laboratorio Bioquímico Manzanillo",
        "recipient_phone": "300 887 2211",
        "recipient_email": "laboratorio@bioquimicactg.com",
        "address": "Zona Franca Parque Central",
        "neighborhood": "Albornoz",
        "city": "Cartagena",
        "latitude": 10.3620,
        "longitude": -75.5050,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.8,
        "priority": "MEDIA"
    }
]

ROUTE_NAMES_BY_ZONE = [
    "Ruta Costera & Zona Turística",
    "Ruta Centro Histórico & Norte",
    "Ruta Corredor Central & Los Alpes",
    "Ruta Industrial Mamonal & Sur",
    "Ruta Comercial & Caribe Plaza",
    "Ruta Bahía & Bocagrande Express"
]

def distribute_random_deliveries(db: Session, seed_if_needed: bool = True) -> Dict[str, Any]:
    """
    Distribuye y asigna aleatoriamente todos los envíos registrados entre todos los repartidores activos de la flota.
    Crea rutas optimizadas individuales y genera estados de progreso en tiempo real para cada repartidor.
    """
    # 1. Asegurar conductores
    drivers = db.query(Driver).order_by(Driver.id).all()
    if not drivers and seed_if_needed:
        for d_data in DEFAULT_DRIVERS_DATA:
            db.add(Driver(**d_data))
        db.commit()
        drivers = db.query(Driver).order_by(Driver.id).all()

    if not drivers:
        raise ValueError("No hay repartidores registrados en el sistema.")

    # 2. Asegurar entregas
    deliveries = db.query(Delivery).order_by(Delivery.id).all()
    if (not deliveries or len(deliveries) < 15) and seed_if_needed:
        # Re-crear las 15 entregas por defecto si están vacías
        db.query(RouteStop).delete()
        db.query(Route).delete()
        db.query(Delivery).delete()
        db.commit()

        for d_data in DEFAULT_DELIVERIES_DATA:
            db.add(Delivery(**d_data))
        db.commit()
        deliveries = db.query(Delivery).order_by(Delivery.id).all()

    # 3. Limpiar asignaciones previas de rutas y paradas
    db.query(RouteStop).delete()
    db.query(Route).delete()
    db.commit()

    # 4. Barajar entregas aleatoriamente
    shuffled_deliveries = list(deliveries)
    random.shuffle(shuffled_deliveries)

    num_drivers = len(drivers)
    # Dividir las entregas en partes equitativas
    avg_count = len(shuffled_deliveries) // num_drivers
    remainder = len(shuffled_deliveries) % num_drivers

    allocated_chunks = []
    current_idx = 0
    for i in range(num_drivers):
        chunk_size = avg_count + (1 if i < remainder else 0)
        chunk = shuffled_deliveries[current_idx:current_idx + chunk_size]
        allocated_chunks.append(chunk)
        current_idx += chunk_size

    results_summary = []

    # 5. Crear ruta y paradas para cada conductor
    for i, (driver, driver_deliveries) in enumerate(zip(drivers, allocated_chunks)):
        driver.status = "EN_RUTA"
        
        route_code = f"RUT-2026-{i+1:03d}"
        zone_title = ROUTE_NAMES_BY_ZONE[i % len(ROUTE_NAMES_BY_ZONE)]
        route_name = f"Ruta {i+1} - {zone_title}"

        total_stops = len(driver_deliveries)
        
        # Simular distancias y duraciones realistas
        est_distance = round(random.uniform(12.0, 28.0) + (total_stops * 2.2), 1)
        est_duration = int(round(est_distance * 3.2))

        # Crear la entidad Ruta
        route = Route(
            code=route_code,
            name=route_name,
            driver_id=driver.id,
            total_stops=total_stops,
            completed_stops=0,
            total_distance_km=est_distance,
            estimated_duration_min=est_duration,
            depot_name="Centro Logístico GTR - Manga",
            depot_lat=10.4075,
            depot_lng=-75.5342,
            status="EN_PROGRESO",
            started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 2), minutes=random.randint(10, 45))
        )
        db.add(route)
        db.flush()

        completed_count = 0
        
        # Determinar cuántos paquetes ya están entregados (al menos 1 si hay >=2 entregas)
        if total_stops >= 3:
            num_delivered = random.randint(1, total_stops - 2)
            has_in_transit = True
        elif total_stops >= 2:
            num_delivered = 1
            has_in_transit = True
        else:
            num_delivered = 0
            has_in_transit = True

        for seq, deliv in enumerate(driver_deliveries, start=1):
            if seq <= num_delivered:
                # Ya fue entregado
                deliv_status = "ENTREGADO"
                stop_status = "COMPLETADO"
                deliv.delivered_at = datetime.utcnow() - timedelta(minutes=random.randint(15, 60))
                deliv.recipient_id_card = f"CC-{random.randint(10000000, 99999999)}"
                deliv.incident_reason = None
                completed_count += 1
            elif seq == num_delivered + 1 and has_in_transit:
                # Paquete actualmente en tránsito
                deliv_status = "EN_CAMINO"
                stop_status = "EN_CAMINO"
                deliv.delivered_at = None
                deliv.recipient_id_card = None
                deliv.incident_reason = None
            elif seq == total_stops and random.random() < 0.20:
                # Pequeña probabilidad aleatoria de incidencia para enriquecer la simulación
                deliv_status = "INCIDENCIA"
                stop_status = "INCIDENCIA"
                deliv.delivered_at = None
                deliv.recipient_id_card = None
                deliv.incident_reason = "Dirección con acceso restringido o cliente ausente"
            else:
                # Paquete asignado / pendiente por visitar en la ruta
                deliv_status = "ASIGNADO"
                stop_status = "PENDIENTE"
                deliv.delivered_at = None
                deliv.recipient_id_card = None
                deliv.incident_reason = None

            deliv.status = deliv_status

            # Crear Parada de Ruta
            stop = RouteStop(
                route_id=route.id,
                delivery_id=deliv.id,
                sequence_order=seq,
                estimated_arrival=f"{8 + seq:02d}:{random.choice(['15', '30', '45'])}",
                distance_from_prev_km=round(est_distance / (total_stops or 1), 1),
                travel_time_min=round(est_duration / (total_stops or 1)),
                status=stop_status,
                notes=deliv.incident_reason
            )
            db.add(stop)

        route.completed_stops = completed_count
        if completed_count == total_stops and total_stops > 0:
            route.status = "FINALIZADA"
            driver.status = "DISPONIBLE"

        results_summary.append({
            "driver_id": driver.id,
            "driver_name": driver.name,
            "vehicle": f"{driver.vehicle_type} ({driver.vehicle_plate})",
            "route_code": route_code,
            "route_name": route_name,
            "total_packages": total_stops,
            "delivered": completed_count,
            "in_transit": 1 if has_in_transit and (num_delivered + 1 <= total_stops) else 0,
            "status": route.status
        })

    db.commit()
    return {
        "success": True,
        "message": f"Se distribuyeron aleatoriamente {len(deliveries)} paquetes entre {num_drivers} repartidores con éxito.",
        "drivers_allocated": len(drivers),
        "total_deliveries": len(deliveries),
        "routes": results_summary
    }
