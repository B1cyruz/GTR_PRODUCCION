import math
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia ortodrómica en kilómetros entre dos coordenadas GPS."""
    R = 6371.0 # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def optimize_stops_tsp(depot: Dict[str, Any], deliveries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Algoritmo heurístico Nearest Neighbor con refinamiento 2-Opt para el problema del agente viajero (TSP).
    Inicia en el depósito y ordena las entregas minimizando la distancia total recorrida.
    """
    if not deliveries:
        return []

    unvisited = list(deliveries)
    ordered = []
    
    current_lat = depot["latitude"]
    current_lng = depot["longitude"]
    
    while unvisited:
        # Encontrar la entrega más cercana al punto actual
        best_idx = 0
        min_dist = float('inf')
        
        for i, item in enumerate(unvisited):
            dist = haversine_distance(current_lat, current_lng, item["latitude"], item["longitude"])
            # Bonificación de prioridad (ALTA tiene preferencia a menor distancia)
            if item.get("priority") == "ALTA":
                dist *= 0.85
            
            if dist < min_dist:
                min_dist = dist
                best_idx = i
                
        nearest = unvisited.pop(best_idx)
        ordered.append(nearest)
        current_lat = nearest["latitude"]
        current_lng = nearest["longitude"]

    # Refinamiento 2-Opt básico si hay más de 3 paradas
    if len(ordered) > 3:
        improved = True
        while improved:
            improved = False
            for i in range(len(ordered) - 1):
                for j in range(i + 1, len(ordered)):
                    prev_i = depot if i == 0 else ordered[i - 1]
                    curr_i = ordered[i]
                    curr_j = ordered[j]
                    next_j = ordered[j + 1] if j + 1 < len(ordered) else None

                    # Distancia actual
                    d1 = haversine_distance(prev_i["latitude"], prev_i["longitude"], curr_i["latitude"], curr_i["longitude"])
                    d2 = haversine_distance(curr_j["latitude"], curr_j["longitude"], next_j["latitude"], next_j["longitude"]) if next_j else 0
                    
                    # Distancia con intercambio invertido
                    d3 = haversine_distance(prev_i["latitude"], prev_i["longitude"], curr_j["latitude"], curr_j["longitude"])
                    d4 = haversine_distance(curr_i["latitude"], curr_i["longitude"], next_j["latitude"], next_j["longitude"]) if next_j else 0
                    
                    if (d3 + d4) < (d1 + d2) - 0.05:
                        ordered[i:j + 1] = reversed(ordered[i:j + 1])
                        improved = True
                        break
                if improved:
                    break

    return ordered

def fetch_osrm_geometry(coordinates: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Consulta el servicio de ruteo OSRM para obtener la geometría vial real de las calles.
    coordinates: lista de tuplas (lat, lng)
    Retorna un diccionario con polilínea/GeoJSON y distancias reales, o fallback geométrico.
    """
    if len(coordinates) < 2:
        return {"type": "LineString", "coordinates": [[c[1], c[0]] for c in coordinates]}

    # OSRM espera lng,lat;lng,lat
    coord_str = ";".join([f"{c[1]},{c[0]}" for c in coordinates])
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"

    try:
        resp = requests.get(url, timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and len(data.get("routes", [])) > 0:
                route = data["routes"][0]
                return {
                    "geometry": route.get("geometry"),
                    "distance_km": round(route.get("distance", 0) / 1000.0, 2),
                    "duration_min": round(route.get("duration", 0) / 60.0)
                }
    except Exception:
        pass

    # Fallback si no hay conexión externa: cálculo ortodrómico estimado con factor de vía urbana (1.35x)
    total_km = 0.0
    for i in range(len(coordinates) - 1):
        total_km += haversine_distance(
            coordinates[i][0], coordinates[i][1],
            coordinates[i+1][0], coordinates[i+1][1]
        ) * 1.35

    est_duration = int((total_km / 22.0) * 60) # 22 km/h promedio en ciudad
    return {
        "geometry": {
            "type": "LineString",
            "coordinates": [[c[1], c[0]] for c in coordinates]
        },
        "distance_km": round(total_km, 2),
        "duration_min": est_duration
    }

def calculate_route_metrics(depot: Dict[str, Any], ordered_deliveries: List[Dict[str, Any]], start_time_str: str = "08:00") -> Dict[str, Any]:
    """
    Calcula distancias parada a parada, horas estimadas de llegada (ETA) y resumen total de la ruta.
    """
    all_points = [(depot["latitude"], depot["longitude"])] + [
        (d["latitude"], d["longitude"]) for d in ordered_deliveries
    ]

    osrm_data = fetch_osrm_geometry(all_points)

    stops_detail = []
    accumulated_km = 0.0
    
    # Hora de inicio
    try:
        base_time = datetime.strptime(start_time_str, "%H:%M")
    except Exception:
        base_time = datetime.strptime("08:00", "%H:%M")

    current_time = base_time
    prev_point = (depot["latitude"], depot["longitude"])

    for i, delivery in enumerate(ordered_deliveries, start=1):
        dist_km = round(haversine_distance(prev_point[0], prev_point[1], delivery["latitude"], delivery["longitude"]) * 1.3, 2)
        travel_min = max(3, int((dist_km / 20.0) * 60)) # tiempo de viaje
        handling_min = 6 # 6 minutos por entrega de paquete

        current_time += timedelta(minutes=travel_min)
        eta_str = current_time.strftime("%H:%M")
        current_time += timedelta(minutes=handling_min)

        accumulated_km += dist_km
        stops_detail.append({
            "sequence_order": i,
            "delivery_id": delivery["id"],
            "estimated_arrival": eta_str,
            "distance_from_prev_km": dist_km,
            "travel_time_min": travel_min,
            "delivery": delivery
        })
        prev_point = (delivery["latitude"], delivery["longitude"])

    total_duration_min = int((current_time - base_time).total_seconds() / 60)

    return {
        "total_stops": len(ordered_deliveries),
        "total_distance_km": round(accumulated_km, 2),
        "estimated_duration_min": total_duration_min,
        "geometry": osrm_data.get("geometry"),
        "stops": stops_detail
    }
