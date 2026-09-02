import random
from datetime import timedelta
from typing import Dict, Any, List
from django.utils import timezone
from core.models import Driver, Delivery, Route, RouteStop, Client, DeliveryPoint

DEFAULT_DRIVERS_DATA = [
    {
        "name": "José P. Martínez",
        "phone": "300 452 8910",
        "vehicle_type": "MOTO",
        "vehicle_plate": "GTR-98E",
        "capacity_kg": 35.0,
        "current_lat": 10.4220,
        "current_lng": -75.5490,
        "status": "EN_RUTA"
    },
    {
        "name": "Sergio A. Salgado",
        "phone": "312 889 1234",
        "vehicle_type": "FURGON",
        "vehicle_plate": "UTL-452",
        "capacity_kg": 600.0,
        "current_lat": 10.4040,
        "current_lng": -75.5550,
        "status": "EN_RUTA"
    },
    {
        "name": "Juan S. Espinosa",
        "phone": "318 765 4321",
        "vehicle_type": "MOTO",
        "vehicle_plate": "BHY-11F",
        "capacity_kg": 40.0,
        "current_lat": 10.4150,
        "current_lng": -75.5340,
        "status": "EN_RUTA"
    },
    {
        "name": "Juan D. Amazan",
        "phone": "301 998 7766",
        "vehicle_type": "CAMION",
        "vehicle_plate": "WEN-891",
        "capacity_kg": 1500.0,
        "current_lat": 10.3750,
        "current_lng": -75.5100,
        "status": "EN_RUTA"
    }
]

# 40 Envíos en total: 10 entregas para cada repartidor
# Para cada repartidor: 4 comercios/sitios turísticos con GPS verificado + 6 residenciales sin GPS en base general
REAL_CARTAGENA_LOCATIONS = [
    # =========================================================================
    # GRUPO 1: REPARTIDOR 1 (José P. Martínez - Moto GTR-98E)
    # Zona: Centro Histórico, Getsemaní, San Diego, Manga, El Cabrero, Torices (10 envíos)
    # =========================================================================
    {
        "tracking_code": "GTR-1001-CDM",
        "place_name": "Restaurante Café del Mar (Baluarte Santo Domingo)",
        "client_name": "Inversiones Gastronómicas del Mar S.A.S.",
        "recipient_name": "Chef Álvaro Martínez",
        "recipient_phone": "300 452 8901",
        "recipient_email": "alvaro.martinez@cafedelmarcartagena.com.co",
        "address": "Calle Santo Domingo # 2-10, Baluarte de Santo Domingo",
        "neighborhood": "Centro Histórico",
        "city": "Cartagena",
        "reference_point": "Sobre la Muralla con vista al Mar Caribe, acceso por Plaza Santo Domingo",
        "latitude": 10.4233,
        "longitude": -75.5539,
        "package_type": "REFRIGERADO",
        "weight_kg": 4.5,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80",
        "notes": "Entrega directa en cocina principal. Requiere cadena de frío.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1002-TDR",
        "place_name": "Torre del Reloj & Portal de los Dulces",
        "client_name": "Asociación Turística y Comercial Centro Histórico",
        "recipient_name": "Dra. Carmen Cecilia Valiente",
        "recipient_phone": "315 789 4432",
        "recipient_email": "carmen.valiente@turismocartagena.gov.co",
        "address": "Plaza de los Coches # 34-12, Puerta del Reloj",
        "neighborhood": "Centro Histórico",
        "city": "Cartagena",
        "reference_point": "Bajo los arcos del Portal de los Dulces frente a la Plaza de la Paz",
        "latitude": 10.4228,
        "longitude": -75.5488,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.8,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?auto=format&fit=crop&w=600&q=80",
        "notes": "Oficina de Información y Atención Turística Puerta del Reloj.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1003-CSF",
        "place_name": "Monumento Castillo de San Felipe de Barajas",
        "client_name": "Escuela Taller Cartagena de Indias (ETCAR)",
        "recipient_name": "Ing. Gabriel Riascos (Coordinador)",
        "recipient_phone": "301 223 9988",
        "recipient_email": "administracion@castillosanfelipe.org",
        "address": "Avenida Antonio Arévalo # 17-80, Cerro San Lázaro",
        "neighborhood": "Pie del Cerro",
        "city": "Cartagena",
        "reference_point": "Taquilla y Acceso Principal Fuerte San Felipe",
        "latitude": 10.4224,
        "longitude": -75.5398,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 5.2,
        "priority": "MEDIA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1583997052103-b4a1cb974ce3?auto=format&fit=crop&w=600&q=80",
        "notes": "Entregar en centro de visitantes y guardia de acceso.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1004-CEV",
        "place_name": "Restaurante La Cevichería (Plaza San Diego)",
        "client_name": "Comercializadora del Caribe Gourmet S.A.S.",
        "recipient_name": "Chef Carmelo Barrios",
        "recipient_phone": "318 667 5544",
        "recipient_email": "pedidos@lacevicheriacartagena.com",
        "address": "Calle Stuart # 7-14, Plaza de San Diego",
        "neighborhood": "San Diego",
        "city": "Cartagena",
        "reference_point": "Diagonal a la Plaza San Diego y Hotel Sofitel Legend Santa Clara",
        "latitude": 10.4265,
        "longitude": -75.5470,
        "package_type": "REFRIGERADO",
        "weight_kg": 6.0,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80",
        "notes": "Recibe personal de recepción de mariscos.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1005-CEM",
        "place_name": "Residencia Mendoza (Sin GPS Previo)",
        "client_name": "Carlos Eduardo Mendoza",
        "recipient_name": "Carlos Eduardo Mendoza",
        "recipient_phone": "312 456 7890",
        "recipient_email": "carlos.mendoza@gmail.com",
        "address": "Calle 26 # 22-45 Edificio Bahía Azul Apto 402",
        "neighborhood": "Manga",
        "city": "Cartagena",
        "reference_point": "Tercera Avenida de Manga diagonal al Puente Román",
        "latitude": 10.4112,
        "longitude": -75.5348,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 1.8,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Entrega residencial. El repartidor debe registrar ubicación GPS exacta.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1006-MFG",
        "place_name": "Casa Colonial Gómez (Sin GPS Previo)",
        "client_name": "María Fernanda Gómez",
        "recipient_name": "María Fernanda Gómez",
        "recipient_phone": "301 789 1234",
        "recipient_email": "mafe.gomez@outlook.com",
        "address": "Calle de la Sierpe # 29-18 Casa Colonial",
        "neighborhood": "Getsemaní",
        "city": "Cartagena",
        "reference_point": "Calle de los grafitis frente a la Plazoleta de la Trinidad",
        "latitude": 10.4201,
        "longitude": -75.5452,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 2.3,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Tocar timbre portón de madera colonial.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1007-JLH",
        "place_name": "Familia Herrera (Sin GPS Previo)",
        "client_name": "Jorge Luis Herrera",
        "recipient_name": "Jorge Luis Herrera",
        "recipient_phone": "317 234 5678",
        "recipient_email": "jorge.herrera@hotmail.com",
        "address": "Carrera 14 # 42-50 Paseo de Bolívar",
        "neighborhood": "Torices",
        "city": "Cartagena",
        "reference_point": "Frente a la Cancha Múltiple de Torices",
        "latitude": 10.4310,
        "longitude": -75.5360,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 4.1,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Casa esquinera reja blanca.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1008-LMC",
        "place_name": "Residencia Castro (Sin GPS Previo)",
        "client_name": "Luz Marina Castro",
        "recipient_name": "Luz Marina Castro",
        "recipient_phone": "310 987 6543",
        "recipient_email": "luz.castro@yahoo.com",
        "address": "Calle del Curato # 38-20 Casa Balcón Colonial",
        "neighborhood": "San Diego",
        "city": "Cartagena",
        "reference_point": "A media cuadra de la Plaza del Tejadillo",
        "latitude": 10.4278,
        "longitude": -75.5485,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.4,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Sobre de correspondencia bancaria prioritaria.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1009-ADP",
        "place_name": "Edificio Mar de Leva (Sin GPS Previo)",
        "client_name": "Andrés David Pineda",
        "recipient_name": "Andrés David Pineda",
        "recipient_phone": "300 112 2334",
        "recipient_email": "andres.pineda@live.com",
        "address": "Calle Real # 41-15 Edificio Mar de Leva Apto 601",
        "neighborhood": "El Cabrero",
        "city": "Cartagena",
        "reference_point": "Frente a la Casa Museo Rafael Núñez y Parque Apolo",
        "latitude": 10.4345,
        "longitude": -75.5420,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 3.7,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Dejar en portería con el vigilante de turno.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1010-PEM",
        "place_name": "Comercio La Carbonera (Sin GPS Previo)",
        "client_name": "Patricia Elena Morales",
        "recipient_name": "Patricia Elena Morales",
        "recipient_phone": "314 334 4556",
        "recipient_email": "patricia.morales@gmail.com",
        "address": "Sector La Carbonera Manzana B Lote 4",
        "neighborhood": "Chambacú",
        "city": "Cartagena",
        "reference_point": "Entrando por la estación Transcaribe Chambacú",
        "latitude": 10.4240,
        "longitude": -75.5410,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 2.0,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Tienda esquinera de abarrotes.",
        "driver_idx": 0
    },

    # =========================================================================
    # GRUPO 2: REPARTIDOR 2 (Sergio A. Salgado - Furgón UTL-452)
    # Zona: Península Bocagrande, Castillogrande, El Laguito (10 envíos)
    # =========================================================================
    {
        "tracking_code": "GTR-1011-HYT",
        "place_name": "Hotel Hyatt Regency & CC Plaza Bocagrande",
        "client_name": "Inversiones Plaza Bocagrande P.H.",
        "recipient_name": "Ing. Natalia Silva",
        "recipient_phone": "310 445 6677",
        "recipient_email": "natalia.silva@hyattcartagena.com",
        "address": "Carrera 1 # 12-118, Avenida del Malecón",
        "neighborhood": "Bocagrande",
        "city": "Cartagena",
        "reference_point": "Entrada principal Centro Comercial Plaza Bocagrande",
        "latitude": 10.4082,
        "longitude": -75.5540,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 12.5,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=600&q=80",
        "notes": "Bahía de carga subterránea nivel S1.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1012-LRB",
        "place_name": "Droguería La Rebaja San Martín",
        "client_name": "Copservir Droguerías La Rebaja",
        "recipient_name": "Dra. Diana Patricia Roa",
        "recipient_phone": "300 998 1234",
        "recipient_email": "diana.roa@larebaja.com.co",
        "address": "Avenida San Martín Carrera 2 # 7-45",
        "neighborhood": "Bocagrande",
        "city": "Cartagena",
        "reference_point": "Frente al Hotel Decameron Bocagrande",
        "latitude": 10.4015,
        "longitude": -75.5562,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 2.1,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1586015555751-63c25b3901bc?auto=format&fit=crop&w=600&q=80",
        "notes": "Medicamentos con precinto de seguridad térmico.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1013-CNV",
        "place_name": "Club Naval de Oficiales Castillogrande",
        "client_name": "Club Naval Armada Nacional de Colombia",
        "recipient_name": "Capitán Fernando Morales",
        "recipient_phone": "312 334 5566",
        "recipient_email": "fernando.morales@clubnaval.mil.co",
        "address": "Calle 5A # 10-80 Paseo Bahía",
        "neighborhood": "Castillogrande",
        "city": "Cartagena",
        "reference_point": "Final del Malecón de Castillogrande sobre la bahía",
        "latitude": 10.3920,
        "longitude": -75.5495,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.5,
        "priority": "MEDIA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80",
        "notes": "Ingreso por guardia principal con carnet o identificación.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1014-DNC",
        "place_name": "Hotel Dann Carlton El Laguito",
        "client_name": "Cadena Hotelera Dann Carlton",
        "recipient_name": "Germán Dussán",
        "recipient_phone": "317 889 0011",
        "recipient_email": "almacen@danncarltoncartagena.com",
        "address": "Calle 1A # 3-15 Avenida Almirante Brión",
        "neighborhood": "El Laguito",
        "city": "Cartagena",
        "reference_point": "Sector El Laguito frente al lago y playas de Hilton",
        "latitude": 10.3965,
        "longitude": -75.5610,
        "package_type": "VOLUMINOSO",
        "weight_kg": 28.0,
        "priority": "MEDIA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=600&q=80",
        "notes": "Entregar en muelle logístico trasero.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1015-VMC",
        "place_name": "Edificio Infinito Bocagrande (Sin GPS Previo)",
        "client_name": "Valentina Mejía Cueto",
        "recipient_name": "Valentina Mejía Cueto",
        "recipient_phone": "301 556 7788",
        "recipient_email": "valen.mejia@gmail.com",
        "address": "Carrera 3 # 6-80 Edificio Infinito Apto 802",
        "neighborhood": "Bocagrande",
        "city": "Cartagena",
        "reference_point": "Avenida San Martín entre Calles 6 y 7",
        "latitude": 10.4005,
        "longitude": -75.5570,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 3.0,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Recepción torre A.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1016-ROB",
        "place_name": "Edificio Puerto Velero (Sin GPS Previo)",
        "client_name": "Rodrigo Osorio Barrios",
        "recipient_name": "Rodrigo Osorio Barrios",
        "recipient_phone": "318 443 2211",
        "recipient_email": "rodrigo.osorio@yahoo.es",
        "address": "Calle 6 # 12-40 Edificio Puerto Velero Apto 1201",
        "neighborhood": "Castillogrande",
        "city": "Cartagena",
        "reference_point": "Paseo Peatonal de Castillogrande",
        "latitude": 10.3930,
        "longitude": -75.5510,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 5.5,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Anunciar en recepción con el celador.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1017-GLS",
        "place_name": "Edificio Mirador del Laguito (Sin GPS Previo)",
        "client_name": "Gloria Lucía Suárez",
        "recipient_name": "Gloria Lucía Suárez",
        "recipient_phone": "315 889 9001",
        "recipient_email": "gloria.suarez@outlook.com",
        "address": "Avenida Almirante Brión Edificio Mirador del Laguito Apto 504",
        "neighborhood": "El Laguito",
        "city": "Cartagena",
        "reference_point": "Diagonal a la entrada del Hotel Hilton",
        "latitude": 10.3955,
        "longitude": -75.5625,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 1.2,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Entregar en lobby principal.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1018-DAP",
        "place_name": "Edificio Torre del Mar (Sin GPS Previo)",
        "client_name": "Daniel Alfonso Pardo",
        "recipient_name": "Daniel Alfonso Pardo",
        "recipient_phone": "320 667 8899",
        "recipient_email": "daniel.pardo@gmail.com",
        "address": "Carrera 2 # 11-25 Edificio Torre del Mar Apto 1403",
        "neighborhood": "Bocagrande",
        "city": "Cartagena",
        "reference_point": "Frente a las playas de Bocagrande sector Hollywood",
        "latitude": 10.4060,
        "longitude": -75.5548,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 6.8,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Paquete frágil con equipos electrónicos.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1019-EVS",
        "place_name": "Edificio Bahía Grande (Sin GPS Previo)",
        "client_name": "Esperanza Vega Salcedo",
        "recipient_name": "Esperanza Vega Salcedo",
        "recipient_phone": "311 223 9988",
        "recipient_email": "esperanza.vega@hotmail.com",
        "address": "Calle 5 # 8-30 Edificio Bahía Grande Apto 901",
        "neighborhood": "Castillogrande",
        "city": "Cartagena",
        "reference_point": "Calle 5 frente a la bahía interior",
        "latitude": 10.3912,
        "longitude": -75.5480,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 4.9,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Entregar directamente a la señora Esperanza.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1020-MAR",
        "place_name": "Conjunto Nuevo Conquistador (Sin GPS Previo)",
        "client_name": "Mauricio Antonio Rivas",
        "recipient_name": "Mauricio Antonio Rivas",
        "recipient_phone": "300 887 6655",
        "recipient_email": "mauricio.rivas@gmail.com",
        "address": "Calle 1 # 4-50 Conjunto Nuevo Conquistador Torre 2 Apto 310",
        "neighborhood": "El Laguito",
        "city": "Cartagena",
        "reference_point": "Frente al lago El Laguito",
        "latitude": 10.3980,
        "longitude": -75.5600,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.6,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Dejar en casillero de correspondencia.",
        "driver_idx": 1
    },

    # =========================================================================
    # GRUPO 3: REPARTIDOR 3 (Juan S. Espinosa - Moto BHY-11F)
    # Zona: Corredor Manga, Pie de la Popa, Mallplaza & La Popa (10 envíos)
    # =========================================================================
    {
        "tracking_code": "GTR-1021-CPT",
        "place_name": "Club de Pesca Cartagena (Fuerte Pastelillo)",
        "client_name": "Club de Pesca de Cartagena S.A.",
        "recipient_name": "Ricardo Herrera",
        "recipient_phone": "320 556 7788",
        "recipient_email": "administracion@clubdepescacartagena.com",
        "address": "Calle 24 # 18-02 Fuerte de San Sebastián del Pastelillo",
        "neighborhood": "Manga",
        "city": "Cartagena",
        "reference_point": "Fuerte San Sebastián del Pastelillo, entrada marina",
        "latitude": 10.4178,
        "longitude": -75.5385,
        "package_type": "REFRIGERADO",
        "weight_kg": 5.5,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
        "notes": "Insumos gourmet para marina y restaurante del fuerte.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1022-CAR",
        "place_name": "Supermercado Carulla Manga",
        "client_name": "Grupo Éxito - Carulla",
        "recipient_name": "Sandra Milena Torres",
        "recipient_phone": "311 223 4455",
        "recipient_email": "sandra.torres@grupo-exito.com",
        "address": "Calle 25 # 24-30 Cuarta Avenida",
        "neighborhood": "Manga",
        "city": "Cartagena",
        "reference_point": "Cuarta Avenida de Manga esquina Calle 25",
        "latitude": 10.4105,
        "longitude": -75.5330,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 8.4,
        "priority": "MEDIA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1578916171728-46686eac8d58?auto=format&fit=crop&w=600&q=80",
        "notes": "Recepción de mercancía por bahía de proveedores.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1023-MLP",
        "place_name": "Éxito Wow Mallplaza El Castillo",
        "client_name": "Mallplaza Colombia S.A.S.",
        "recipient_name": "Claudia Mendoza",
        "recipient_phone": "302 998 3344",
        "recipient_email": "claudia.mendoza@mallplaza.com",
        "address": "Av. Pedro de Heredia # 13-110, Chambacú",
        "neighborhood": "Chambacú / Pie del Cerro",
        "city": "Cartagena",
        "reference_point": "A un costado del Castillo San Felipe de Barajas",
        "latitude": 10.4225,
        "longitude": -75.5392,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 6.2,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1567449303078-57ad995bd301?auto=format&fit=crop&w=600&q=80",
        "notes": "Local Éxito Wow sótano comercial.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1024-FLB",
        "place_name": "Falabella CC Caribe Plaza",
        "client_name": "Falabella de Colombia S.A.",
        "recipient_name": "Andrés Felipe Gómez",
        "recipient_phone": "314 667 8899",
        "recipient_email": "afgomez@falabella.com.co",
        "address": "Calle 29D # 22-108 CC Caribe Plaza Local 101",
        "neighborhood": "Pie de la Popa / El Espinal",
        "city": "Cartagena",
        "reference_point": "Muelle de carga principal CC Caribe Plaza sobre Calle 30",
        "latitude": 10.4125,
        "longitude": -75.5240,
        "package_type": "VOLUMINOSO",
        "weight_kg": 16.0,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1519642918688-7e43b19245d8?auto=format&fit=crop&w=600&q=80",
        "notes": "Entrega en bodega general almacén ancla Falabella.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1025-CJS",
        "place_name": "Casa Patrimonial Manga (Sin GPS Previo)",
        "client_name": "Camilo José Silgado",
        "recipient_name": "Camilo José Silgado",
        "recipient_phone": "310 334 5566",
        "recipient_email": "camilo.silgado@gmail.com",
        "address": "1ra Avenida de Manga # 20-35 Casa Republicana",
        "neighborhood": "Manga",
        "city": "Cartagena",
        "reference_point": "Frente al paseo peatonal de la Bahía de Manga",
        "latitude": 10.4160,
        "longitude": -75.5390,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 2.5,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Registrar punto GPS frente a la fachada de la casona.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1026-NPR",
        "place_name": "Residencia Ramos (Sin GPS Previo)",
        "client_name": "Nubia Patricia Ramos",
        "recipient_name": "Nubia Patricia Ramos",
        "recipient_phone": "316 778 9900",
        "recipient_email": "nubia.ramos@hotmail.com",
        "address": "Calle 29B # 21-40 Sector Callejón Angosto",
        "neighborhood": "Pie de la Popa",
        "city": "Cartagena",
        "reference_point": "Atrás del Colegio Biffi",
        "latitude": 10.4140,
        "longitude": -75.5260,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.5,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Casa de dos pisos color crema.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1027-HGB",
        "place_name": "Finca Subida a la Popa (Sin GPS Previo)",
        "client_name": "Hernán Guillermo Berrío",
        "recipient_name": "Hernán Guillermo Berrío",
        "recipient_phone": "301 223 4455",
        "recipient_email": "hernan.berrio@gmail.com",
        "address": "Vía al Convento de la Popa Kilómetro 1",
        "neighborhood": "La Popa",
        "city": "Cartagena",
        "reference_point": "Curva 3 subiendo al Cerro de la Popa",
        "latitude": 10.4190,
        "longitude": -75.5220,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 7.0,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Portón metálico negro con aviso Finca La Cabaña.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1028-YMC",
        "place_name": "Edificio San Lázaro (Sin GPS Previo)",
        "client_name": "Yolanda Mercedes Cuesta",
        "recipient_name": "Yolanda Mercedes Cuesta",
        "recipient_phone": "318 990 1122",
        "recipient_email": "yolanda.cuesta@yahoo.com",
        "address": "Carrera 18 # 27-15 Edificio San Lázaro Apto 204",
        "neighborhood": "El Espinal",
        "city": "Cartagena",
        "reference_point": "Frente al Monumento a la India Catalina",
        "latitude": 10.4205,
        "longitude": -75.5370,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 1.9,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Entregar en conserjería del edificio.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1029-FJQ",
        "place_name": "Taller Quintana (Sin GPS Previo)",
        "client_name": "Fabián Jesús Quintana",
        "recipient_name": "Fabián Jesús Quintana",
        "recipient_phone": "312 887 6655",
        "recipient_email": "fabian.quintana@gmail.com",
        "address": "Callejón Franco # 23-18",
        "neighborhood": "Lo Amador",
        "city": "Cartagena",
        "reference_point": "A dos cuadras del Puente de Chambacú",
        "latitude": 10.4230,
        "longitude": -75.5320,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 5.0,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Taller mecánico automotriz.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1030-BME",
        "place_name": "Edificio Plaza de Toros (Sin GPS Previo)",
        "client_name": "Beatriz Molinares Echeverría",
        "recipient_name": "Beatriz Molinares Echeverría",
        "recipient_phone": "315 443 2211",
        "recipient_email": "beatriz.molinares@outlook.com",
        "address": "Calle 30 # 25-50 Edificio Plaza de Toros Apto 802",
        "neighborhood": "Pie de la Popa",
        "city": "Cartagena",
        "reference_point": "Frente a la antigua Plaza de Toros Cartagena",
        "latitude": 10.4170,
        "longitude": -75.5280,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.3,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Dejar con recepción.",
        "driver_idx": 2
    },

    # =========================================================================
    # GRUPO 4: REPARTIDOR 4 (Juan D. Amazan - Camión WEN-891)
    # Zona: Corredor Norte Crespo, Alpes, El Bosque & Industrial Mamonal (10 envíos)
    # =========================================================================
    {
        "tracking_code": "GTR-1031-SNT",
        "place_name": "Hotel Sonesta & GHL Complejo Turístico",
        "client_name": "GHL Hoteles del Caribe S.A.S.",
        "recipient_name": "Juliana Vergara",
        "recipient_phone": "300 776 1122",
        "recipient_email": "juliana.vergara@sonestacartagena.com",
        "address": "Carrera 9 # 35-104 Anillo Vial Malecón Crespo",
        "neighborhood": "Crespo",
        "city": "Cartagena",
        "reference_point": "Anillo Vial Costero cerca al Túnel de Crespo",
        "latitude": 10.4510,
        "longitude": -75.5120,
        "package_type": "VOLUMINOSO",
        "weight_kg": 45.0,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=600&q=80",
        "notes": "Ingreso por muelle de proveedores norte.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1032-CMB",
        "place_name": "Clínica Madre Bernarda",
        "client_name": "Organización Clínica Madre Bernarda",
        "recipient_name": "Dr. Jorge Posada",
        "recipient_phone": "318 445 2233",
        "recipient_email": "jorge.posada@clinicamadrebernarda.com.co",
        "address": "Av. Pedro de Heredia # 69-75",
        "neighborhood": "Los Alpes",
        "city": "Cartagena",
        "reference_point": "Sobre la Avenida Pedro de Heredia sector Los Alpes",
        "latitude": 10.3950,
        "longitude": -75.4920,
        "package_type": "REFRIGERADO",
        "weight_kg": 10.0,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=600&q=80",
        "notes": "Farmacia intrahospitalaria piso 1. Mantener refrigeración estricta.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1033-FEB",
        "place_name": "Ferretería El Bosque Industrial",
        "client_name": "Distribuciones El Bosque Ferretero S.A.S.",
        "recipient_name": "Manuel Quintana",
        "recipient_phone": "301 554 9988",
        "recipient_email": "manuel.quintana@ferreteriaelbosque.com",
        "address": "Diagonal 21 # 53-12",
        "neighborhood": "El Bosque",
        "city": "Cartagena",
        "reference_point": "Diagonal 21 Corredor de Carga frente al sector Ceballos",
        "latitude": 10.3870,
        "longitude": -75.5190,
        "package_type": "VOLUMINOSO",
        "weight_kg": 48.0,
        "priority": "MEDIA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=600&q=80",
        "notes": "Descargue con montacargas en patio de materiales.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1034-RFC",
        "place_name": "Refinería de Cartagena (Reficar - Ecopetrol)",
        "client_name": "Refinería de Cartagena S.A.S.",
        "recipient_name": "Ing. Hernando Cárdenas",
        "recipient_phone": "315 678 9012",
        "recipient_email": "hernando.cardenas@ecopetrol.com.co",
        "address": "Km 13 Vía Mamonal Sector Puerta 2",
        "neighborhood": "Mamonal",
        "city": "Cartagena",
        "reference_point": "Garita principal de acceso logístico Puerta 2 Mamonal",
        "latitude": 10.3340,
        "longitude": -75.5015,
        "package_type": "VOLUMINOSO",
        "weight_kg": 85.0,
        "priority": "ALTA",
        "has_gps_point": True,
        "photo_url": "https://images.unsplash.com/photo-1581092335397-9583fe92d232?auto=format&fit=crop&w=600&q=80",
        "notes": "Requiere EPP completos y autorización de ingreso en garita.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1035-RAH",
        "place_name": "Familia Henao (Sin GPS Previo)",
        "client_name": "Raúl Alberto Henao",
        "recipient_name": "Raúl Alberto Henao",
        "recipient_phone": "310 889 7766",
        "recipient_email": "raul.henao@gmail.com",
        "address": "Manzana 25 Lote 12 Etapa 2",
        "neighborhood": "Blas de Lezo",
        "city": "Cartagena",
        "reference_point": "Cerca al Parque de la Virgen de Blas de Lezo",
        "latitude": 10.3880,
        "longitude": -75.4890,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 8.0,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Casa de rejas negras.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1036-KJC",
        "place_name": "Edificio Los Caracoles (Sin GPS Previo)",
        "client_name": "Kelly Johana Caraballo",
        "recipient_name": "Kelly Johana Caraballo",
        "recipient_phone": "301 445 6677",
        "recipient_email": "kelly.caraballo@yahoo.com",
        "address": "Transversal 54 # 31-80 Edificio Los Caracoles Apto 302",
        "neighborhood": "Los Caracoles",
        "city": "Cartagena",
        "reference_point": "Sobre la Transversal 54 diagonal a Bomberos",
        "latitude": 10.3820,
        "longitude": -75.4950,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 3.4,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Dejar en portería.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1037-EJP",
        "place_name": "Residencia Pacheco (Sin GPS Previo)",
        "client_name": "Eduardo José Pacheco",
        "recipient_name": "Eduardo José Pacheco",
        "recipient_phone": "318 223 9900",
        "recipient_email": "eduardo.pacheco@outlook.com",
        "address": "Carrera 71 # 31-20",
        "neighborhood": "Santa Mónica",
        "city": "Cartagena",
        "reference_point": "A dos cuadras del Centro Comercial Santa Lucía",
        "latitude": 10.3910,
        "longitude": -75.4820,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.8,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Entrega residencial personal.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1038-SMR",
        "place_name": "Conjunto Mar Adentro (Sin GPS Previo)",
        "client_name": "Sara Marcela Restrepo",
        "recipient_name": "Sara Marcela Restrepo",
        "recipient_phone": "315 990 8877",
        "recipient_email": "sara.restrepo@gmail.com",
        "address": "Calle 68 # 4-30 Conjunto Residencial Mar Adentro Torre 1 Apto 405",
        "neighborhood": "Crespo",
        "city": "Cartagena",
        "reference_point": "A una cuadra de las playas de Crespo",
        "latitude": 10.4480,
        "longitude": -75.5150,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 6.5,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Entregar en portería del conjunto.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1039-GAL",
        "place_name": "Distribuciones Londoño (Sin GPS Previo)",
        "client_name": "Gustavo Adolfo Londoño",
        "recipient_name": "Gustavo Adolfo Londoño",
        "recipient_phone": "320 554 3322",
        "recipient_email": "gustavo.londono@hotmail.com",
        "address": "Diagonal 22 # 48-15 Corredor Logístico",
        "neighborhood": "El Bosque",
        "city": "Cartagena",
        "reference_point": "Frente a la estación de servicio del Bosque",
        "latitude": 10.3850,
        "longitude": -75.5140,
        "package_type": "VOLUMINOSO",
        "weight_kg": 35.0,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Descargue en bodega local 2.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1040-MTZ",
        "place_name": "Familia Zambrano (Sin GPS Previo)",
        "client_name": "Marta Teresa Zambrano",
        "recipient_name": "Marta Teresa Zambrano",
        "recipient_phone": "300 778 8990",
        "recipient_email": "marta.zambrano@gmail.com",
        "address": "Manzana 14 Lote 8",
        "neighborhood": "San Fernando",
        "city": "Cartagena",
        "reference_point": "Detrás del Polideportivo de San Fernando",
        "latitude": 10.3830,
        "longitude": -75.4850,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 2.2,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "Casa de rejas rojas con jardín.",
        "driver_idx": 3
    },

    # =========================================================================
    # 5 ENVÍOS ADICIONALES SIN UBICACIÓN GPS (Pendientes de georreferenciar en campo)
    # Distribuidos aleatoriamente entre los 4 repartidores
    # =========================================================================
    {
        "tracking_code": "GTR-1041-POZ",
        "place_name": "Residencia Paternina (Sin Ubicación GPS)",
        "client_name": "Marta Elena Paternina",
        "recipient_name": "Marta Elena Paternina",
        "recipient_phone": "318 456 1234",
        "recipient_email": "marta.paternina@gmail.com",
        "address": "Manzana 45 Lote 12 Sector Primero de Mayo",
        "neighborhood": "El Pozón",
        "city": "Cartagena",
        "reference_point": "Frente al billar La Terraza (Sin GPS registrado)",
        "latitude": 0.0,
        "longitude": 0.0,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 3.2,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "📍 Sin ubicación GPS previa. El repartidor debe capturar y registrar las coordenadas GPS al entregar.",
        "driver_idx": 0
    },
    {
        "tracking_code": "GTR-1042-NEL",
        "place_name": "Comercial Caicedo (Sin Ubicación GPS)",
        "client_name": "Jorge Luis Caicedo",
        "recipient_name": "Jorge Luis Caicedo",
        "recipient_phone": "300 789 6543",
        "recipient_email": "jorge.caicedo@outlook.com",
        "address": "Sector Las Vegas Manzana F Casa 18",
        "neighborhood": "Nelson Mandela",
        "city": "Cartagena",
        "reference_point": "Diagonal a la tienda comunitaria La Bendición",
        "latitude": 0.0,
        "longitude": 0.0,
        "package_type": "DOCUMENTO",
        "weight_kg": 0.6,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "📍 Sin ubicación GPS previa. Requiere confirmación de punto al llegar a la zona.",
        "driver_idx": 1
    },
    {
        "tracking_code": "GTR-1043-OLA",
        "place_name": "Depósito Marrugo (Sin Ubicación GPS)",
        "client_name": "Luz Dary Marrugo",
        "recipient_name": "Luz Dary Marrugo",
        "recipient_phone": "312 345 6789",
        "recipient_email": "luzdary.marrugo@gmail.com",
        "address": "Sector La Puntilla Carrera 50 # 32-15",
        "neighborhood": "Olaya Herrera",
        "city": "Cartagena",
        "reference_point": "Callejón peatonal al lado del caño",
        "latitude": 0.0,
        "longitude": 0.0,
        "package_type": "PAQUETE_PEQUEÑO",
        "weight_kg": 1.8,
        "priority": "MEDIA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "📍 Sin ubicación GPS previa. Acceso por pasaje peatonal.",
        "driver_idx": 2
    },
    {
        "tracking_code": "GTR-1044-PAS",
        "place_name": "Almacén Marítimo Quintana (Sin Ubicación GPS)",
        "client_name": "Guillermo León Quintana",
        "recipient_name": "Guillermo León Quintana",
        "recipient_phone": "315 678 9012",
        "recipient_email": "guillermo.quintana@gmail.com",
        "address": "Calle del Puerto # 12-40 Frente al Muelle",
        "neighborhood": "Pasacaballos",
        "city": "Cartagena",
        "reference_point": "A 50 metros del embarcadero principal",
        "latitude": 0.0,
        "longitude": 0.0,
        "package_type": "VOLUMINOSO",
        "weight_kg": 14.5,
        "priority": "ALTA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "📍 Sin ubicación GPS previa. Paquete voluminoso para bodega portuaria.",
        "driver_idx": 3
    },
    {
        "tracking_code": "GTR-1045-SFE",
        "place_name": "Residencia Cuadrado (Sin Ubicación GPS)",
        "client_name": "Diana Marcela Cuadrado",
        "recipient_name": "Diana Marcela Cuadrado",
        "recipient_phone": "301 987 5432",
        "recipient_email": "diana.cuadrado@yahoo.es",
        "address": "Calle Santander Manzana 14 Lote 8",
        "neighborhood": "San Fernando",
        "city": "Cartagena",
        "reference_point": "Cerca a la cancha de fútbol La Victoria",
        "latitude": 0.0,
        "longitude": 0.0,
        "package_type": "PAQUETE_MEDIANO",
        "weight_kg": 4.0,
        "priority": "BAJA",
        "has_gps_point": False,
        "photo_url": None,
        "notes": "📍 Sin ubicación GPS previa. Casa esquinera de un piso.",
        "driver_idx": 0
    }
]

ROUTE_NAMES_BY_ZONE = [
    "Ruta 1 - Centro Histórico, Getsemaní, Manga & Pozón/San Fernando (12 Envíos)",
    "Ruta 2 - Península Bocagrande, Castillogrande & Nelson Mandela (11 Envíos)",
    "Ruta 3 - Corredor Manga, Pie de la Popa & Olaya Herrera (11 Envíos)",
    "Ruta 4 - Corredor Norte Crespo, Mamonal & Pasacaballos (11 Envíos)"
]

def distribute_random_deliveries(seed_if_needed: bool = True) -> Dict[str, Any]:
    """
    Distribuye 40 envíos en 4 rutas continuas y realistas (10 envíos por repartidor),
    creando Clientes, Puntos de Entrega GPS (para comercios verificados) y
    dejando los residenciales sin punto GPS para que el repartidor los registre en campo.
    """
    # 1. Asegurar conductores
    drivers = list(Driver.objects.order_by('id'))
    if (not drivers or len(drivers) < 4) and seed_if_needed:
        for d_data in DEFAULT_DRIVERS_DATA:
            Driver.objects.update_or_create(
                name=d_data["name"],
                defaults=d_data
            )
        drivers = list(Driver.objects.order_by('id'))

    if not drivers:
        raise ValueError("No hay repartidores registrados en el sistema.")

    # 2. Limpiar paradas, rutas y entregas anteriores para reconstruir fielmente
    RouteStop.objects.all().delete()
    Route.objects.all().delete()
    Delivery.objects.all().delete()

    created_deliveries_by_driver: Dict[int, List[Delivery]] = {i: [] for i in range(len(drivers))}

    for loc in REAL_CARTAGENA_LOCATIONS:
        # Crear o actualizar cliente
        client, _ = Client.objects.update_or_create(
            name=loc["client_name"],
            defaults={
                "phone": loc["recipient_phone"],
                "email": loc["recipient_email"],
                "address": loc["address"],
                "neighborhood": loc["neighborhood"],
                "city": loc["city"],
                "is_active": True
            }
        )

        delivery_point = None
        # Solo crear y vincular Punto de Entrega GPS si has_gps_point es True
        if loc.get("has_gps_point", True):
            delivery_point, _ = DeliveryPoint.objects.update_or_create(
                name=loc["place_name"],
                defaults={
                    "client": client,
                    "address": loc["address"],
                    "neighborhood": loc["neighborhood"],
                    "city": loc["city"],
                    "reference_point": loc["reference_point"],
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "photo_url": loc.get("photo_url"),
                    "status": "VERIFICADO",
                    "notes": loc["notes"]
                }
            )

        # Crear el envío asociado
        delivery = Delivery.objects.create(
            tracking_code=loc["tracking_code"],
            client=client,
            delivery_point=delivery_point,
            recipient_name=loc["recipient_name"],
            recipient_phone=loc["recipient_phone"],
            recipient_email=loc["recipient_email"],
            address=loc["address"],
            neighborhood=loc["neighborhood"],
            city=loc["city"],
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            reference_point=loc["reference_point"],
            package_type=loc["package_type"],
            weight_kg=loc["weight_kg"],
            priority=loc["priority"],
            notes=loc["notes"],
            status="PENDIENTE"
        )

        driver_idx = loc.get("driver_idx", 0) % len(drivers)
        created_deliveries_by_driver[driver_idx].append(delivery)

    results_summary = []

    for i, driver in enumerate(drivers):
        driver_deliveries = created_deliveries_by_driver.get(i, [])
        if not driver_deliveries:
            continue

        driver.status = "EN_RUTA"
        # Actualizar ubicación del conductor al inicio de su ruta
        first_loc = driver_deliveries[0]
        driver.current_lat = first_loc.latitude
        driver.current_lng = first_loc.longitude
        driver.save()

        route_code = f"RUT-2026-{i+1:03d}"
        route_name = ROUTE_NAMES_BY_ZONE[i % len(ROUTE_NAMES_BY_ZONE)]
        total_stops = len(driver_deliveries)

        # Distancias realistas calculadas (10 paradas ~18.5 km)
        est_distance = round(7.5 + (total_stops * 1.8), 1)
        est_duration = int(round(est_distance * 3.6))

        route = Route.objects.create(
            code=route_code,
            name=route_name,
            driver=driver,
            total_stops=total_stops,
            completed_stops=1,
            total_distance_km=est_distance,
            estimated_duration_min=est_duration,
            status="EN_PROGRESO",
            started_at=timezone.now() - timedelta(hours=1, minutes=20)
        )

        for seq, deliv in enumerate(driver_deliveries, start=1):
            if seq == 1:
                deliv_status = "ENTREGADO"
                stop_status = "COMPLETADO"
                deliv.delivered_at = timezone.now() - timedelta(minutes=35)
                deliv.recipient_id_card = f"CC-1047{random.randint(1000, 9999)}"
                deliv.incident_reason = None
            elif seq == 2:
                deliv_status = "EN_CAMINO"
                stop_status = "EN_CAMINO"
                deliv.delivered_at = None
                deliv.recipient_id_card = None
                deliv.incident_reason = None
            else:
                deliv_status = "ASIGNADO"
                stop_status = "PENDIENTE"
                deliv.delivered_at = None
                deliv.recipient_id_card = None
                deliv.incident_reason = None

            deliv.status = deliv_status
            deliv.save()

            RouteStop.objects.create(
                route=route,
                delivery=deliv,
                sequence_order=seq,
                status=stop_status,
                estimated_arrival=(timezone.now() + timedelta(minutes=(seq * 15))).strftime("%H:%M"),
                notes=f"Parada #{seq} de la ruta {route.name}"
            )

        results_summary.append({
            "driver_name": driver.name,
            "route_code": route.code,
            "route_name": route.name,
            "total_stops": total_stops,
            "total_distance_km": est_distance
        })

    return {
        "status": "success",
        "message": f"Se organizaron y optimizaron {len(REAL_CARTAGENA_LOCATIONS)} entregas (10 por repartidor) en 4 rutas de Cartagena con éxito.",
        "total_routes": len(results_summary),
        "total_deliveries": len(REAL_CARTAGENA_LOCATIONS),
        "routes": results_summary
    }
