import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.delivery_point import DeliveryPoint
from app.models.client import Client

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia geodésica ortodrómica en metros entre dos coordenadas geográficas
    utilizando la fórmula de Haversine de alta precisión.
    """
    R = 6371000.0 # Radio de la Tierra en metros

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 2)

def find_nearby_delivery_points(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 50.0,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Busca puntos de entrega existentes dentro del radio especificado (por defecto 50 metros)
    alrededor de una coordenada GPS dada.
    """
    # Filtro preliminar por bounding box (~0.01 deg aprox 1.1 km) para eficiencia
    lat_delta = (radius_meters + 100) / 111320.0
    lng_delta = (radius_meters + 100) / (111320.0 * math.cos(math.radians(latitude)) or 1.0)

    candidate_points = db.query(DeliveryPoint).filter(
        DeliveryPoint.latitude.between(latitude - lat_delta, latitude + lat_delta),
        DeliveryPoint.longitude.between(longitude - lng_delta, longitude + lng_delta),
        DeliveryPoint.status == "ACTIVO"
    ).all()

    results = []
    for point in candidate_points:
        dist = haversine_distance_meters(latitude, longitude, point.latitude, point.longitude)
        if dist <= radius_meters:
            client_name = point.client.name if point.client else "Cliente sin registrar"
            client_doc = point.client.document_id if point.client else None
            client_phone = point.client.phone if point.client else None
            
            results.append({
                "point_id": point.id,
                "name": point.name,
                "address": point.address,
                "neighborhood": point.neighborhood,
                "city": point.city,
                "reference_point": point.reference_point,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "distance_meters": dist,
                "photo_url": point.photo_url,
                "client_id": point.client_id,
                "client_name": client_name,
                "client_document": client_doc,
                "client_phone": client_phone,
                "updated_at": (point.updated_at or point.created_at).isoformat() if (point.updated_at or point.created_at) else None
            })


    # Ordenar de más cercano a más lejano
    results.sort(key=lambda x: x["distance_meters"])
    return results[:limit]
