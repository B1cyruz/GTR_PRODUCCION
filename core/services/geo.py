import math
import os
import uuid
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from django.conf import settings
from core.models import DeliveryPoint

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
    latitude: float,
    longitude: float,
    radius_meters: float = 50.0,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Busca puntos de entrega existentes dentro del radio especificado (50 metros)
    alrededor de una coordenada GPS dada utilizando Django ORM.
    """
    lat_delta = (radius_meters + 100) / 111320.0
    lng_delta = (radius_meters + 100) / (111320.0 * math.cos(math.radians(latitude)) or 1.0)

    candidate_points = DeliveryPoint.objects.filter(
        latitude__gte=latitude - lat_delta,
        latitude__lte=latitude + lat_delta,
        longitude__gte=longitude - lng_delta,
        longitude__lte=longitude + lng_delta,
        status='ACTIVO'
    ).select_related('client')

    results = []
    for point in candidate_points:
        dist = haversine_distance_meters(latitude, longitude, point.latitude, point.longitude)
        if dist <= radius_meters:
            client_name = point.client.name if point.client else "Cliente sin registrar"
            client_doc = point.client.document_id if point.client else None
            client_phone = point.client.phone if point.client else None
            
            results.append({
                "id": point.id,
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

    results.sort(key=lambda x: x["distance_meters"])
    return results[:limit]

def save_base64_image(photo_data: Optional[str], subfolder: str = "points", prefix: str = "img_") -> Optional[str]:
    """Decodifica y almacena una imagen base64 capturada desde la cámara del móvil en media/uploads."""
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

            target_dir = os.path.join(settings.MEDIA_ROOT, "uploads", subfolder)
            os.makedirs(target_dir, exist_ok=True)

            timestamp_str = int(datetime.now().timestamp())
            filename = f"{prefix}{timestamp_str}_{uuid.uuid4().hex[:6]}.{ext}"
            filepath = os.path.join(target_dir, filename)

            with open(filepath, "wb") as f:
                f.write(base64.b64decode(imgstr))

            return f"/media/uploads/{subfolder}/{filename}"
        except Exception as e:
            print(f"Error guardando imagen base64: {e}")
            return photo_data[:480]
    elif photo_data.startswith("/media/") or photo_data.startswith("/static/") or photo_data.startswith("http"):
        return photo_data
    return None
