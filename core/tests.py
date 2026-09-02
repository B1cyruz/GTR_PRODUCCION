import json
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Driver, Client as GTRClient, DeliveryPoint, Delivery, Route, RouteStop
from core.services.geo import haversine_distance_meters, find_nearby_delivery_points, save_base64_image

class GTRDjangoTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Crear conductor
        self.driver = Driver.objects.create(
            name="Conductor Prueba",
            phone="3001234567",
            vehicle_type="MOTO",
            vehicle_plate="TST-123",
            capacity_kg=40.0,
            current_lat=10.4075,
            current_lng=-75.5342,
            status="DISPONIBLE"
        )
        
        # 2. Crear Usuarios (ROOT, COORDINADOR, REPARTIDOR)
        self.root_user = User.objects.create_user(
            username="root@gtr.com",
            email="root@gtr.com",
            password="password123",
            full_name="Super Root",
            role="ROOT"
        )
        self.coord_user = User.objects.create_user(
            username="coord@gtr.com",
            email="coord@gtr.com",
            password="password123",
            full_name="Carlos Coord",
            role="COORDINADOR"
        )
        self.driver_user = User.objects.create_user(
            username="driver@gtr.com",
            email="driver@gtr.com",
            password="password123",
            full_name="Conductor Prueba",
            role="REPARTIDOR",
            driver=self.driver
        )

        # 3. Punto GPS inicial en Bocagrande (Cartagena)
        self.point = DeliveryPoint.objects.create(
            name="Farmacia Bocagrande",
            address="Cra 3 # 6-10",
            neighborhood="Bocagrande",
            city="Cartagena",
            latitude=10.4012,
            longitude=-75.5548,
            created_by_user=self.root_user
        )

        # 4. Entrega de prueba
        self.delivery = Delivery.objects.create(
            tracking_code="GTR-TEST-001",
            recipient_name="Juan Perez",
            recipient_phone="3009998877",
            address="Cra 3 # 6-10",
            neighborhood="Bocagrande",
            city="Cartagena",
            latitude=10.4012,
            longitude=-75.5548,
            package_type="PAQUETE_MEDIANO",
            weight_kg=2.5,
            priority="MEDIA",
            status="PENDIENTE"
        )

    def test_haversine_distance(self):
        # Distancia entre dos puntos idénticos debe ser 0
        dist = haversine_distance_meters(10.4012, -75.5548, 10.4012, -75.5548)
        self.assertEqual(dist, 0.0)

        # Distancia ~20 metros
        dist_near = haversine_distance_meters(10.4012, -75.5548, 10.4013, -75.5549)
        self.assertTrue(0 < dist_near < 50)

    def test_find_nearby_delivery_points(self):
        # Buscar punto a 10 metros
        nearby = find_nearby_delivery_points(10.40121, -75.55481, radius_meters=50.0)
        self.assertEqual(len(nearby), 1)
        self.assertEqual(nearby[0]["id"], self.point.id)

    def test_login_flow(self):
        response = self.client.post('/api/auth/login/', data=json.dumps({
            "email": "root@gtr.com",
            "password": "password123"
        }), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("role"), "ROOT")

    def test_api_create_point_with_duplicate_detection(self):
        self.client.force_login(self.driver_user)
        
        # Intentar crear un punto a menos de 50 metros sin force_create_duplicate=True -> debe advertir duplicado (HTTP 409)
        payload = {
            "name": "Drogueria Bocagrande 2",
            "address": "Cra 3 # 6-12",
            "latitude": 10.40122,
            "longitude": -75.55482,
            "force_create_duplicate": False
        }
        res = self.client.post('/api/points/', data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 409)
        data = res.json()
        self.assertTrue(data.get("duplicate_warning"))
        self.assertTrue(len(data.get("nearby_points")) > 0)

        # Forzar creación de punto con foto simulada
        payload["force_create_duplicate"] = True
        payload["photo_data"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        res2 = self.client.post('/api/points/', data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res2.status_code, 201)
        data2 = res2.json()
        self.assertTrue(data2.get("id") is not None)
        self.assertIsNotNone(data2.get("photo_url"))

    def test_update_existing_point_without_duplicate(self):
        self.client.force_login(self.driver_user)
        
        # Repartidor actualiza coordenadas de un punto existente
        payload = {
            "latitude": 10.40130,
            "longitude": -75.55490,
            "gps_accuracy": 4.5,
            "notes": "Coordenadas corregidas en campo"
        }
        res = self.client.put(f'/api/points/{self.point.id}/', data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.point.refresh_from_db()
        self.assertAlmostEqual(self.point.latitude, 10.40130, places=4)
        self.assertEqual(self.point.updated_by_user, self.driver_user)

    def test_driver_mobile_view(self):
        self.client.force_login(self.driver_user)
        res = self.client.get('/repartidor/ruta-activa/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "GTR Móvil")

    def test_dashboard_view(self):
        self.client.force_login(self.root_user)
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Panel de Control de Distribución")
