import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine, ensure_schema_updates
from app.models.user import User
from app.models.driver import Driver
from app.models.client import Client
from app.models.delivery_point import DeliveryPoint, DeliveryPointHistory
from app.models.audit import AuditLog
from app.services.auth import create_access_token, get_password_hash
from app.services.geo import haversine_distance_meters, find_nearby_delivery_points

class TestRBACAndGPSSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        ensure_schema_updates()
        cls.client = TestClient(app, follow_redirects=False)
        cls.db = SessionLocal()

        # Asegurar usuarios de prueba
        cls.root_user = cls.db.query(User).filter(User.email == "root@gtrlogistics.com").first()
        if not cls.root_user:
            cls.root_user = User(
                email="root@gtrlogistics.com",
                full_name="Super Admin (ROOT)",
                hashed_password=get_password_hash("GTRAdmin2026!"),
                role="ROOT",
                is_active=True
            )
            cls.db.add(cls.root_user)
            cls.db.commit()
            cls.db.refresh(cls.root_user)

        cls.coord_user = cls.db.query(User).filter(User.email == "coordinador@gtrlogistics.com").first()
        if not cls.coord_user:
            cls.coord_user = User(
                email="coordinador@gtrlogistics.com",
                full_name="Carlos Coordinador",
                hashed_password=get_password_hash("GTRCoord2026!"),
                role="COORDINADOR",
                is_active=True
            )
            cls.db.add(cls.coord_user)
            cls.db.commit()
            cls.db.refresh(cls.coord_user)

        # Repartidor 1
        cls.driver_user1 = cls.db.query(User).filter(User.email == "repartidor1@gtrlogistics.com").first()
        if not cls.driver_user1:
            cls.driver_user1 = User(
                email="repartidor1@gtrlogistics.com",
                full_name="Repartidor Uno",
                hashed_password=get_password_hash("GTRDriver2026!"),
                role="REPARTIDOR",
                is_active=True
            )
            cls.db.add(cls.driver_user1)
            cls.db.commit()
            cls.db.refresh(cls.driver_user1)

        # Repartidor 2
        cls.driver_user2 = cls.db.query(User).filter(User.email == "repartidor2@gtrlogistics.com").first()
        if not cls.driver_user2:
            cls.driver_user2 = User(
                email="repartidor2@gtrlogistics.com",
                full_name="Repartidor Dos",
                hashed_password=get_password_hash("GTRDriver2026!"),
                role="REPARTIDOR",
                is_active=True
            )
            cls.db.add(cls.driver_user2)
            cls.db.commit()
            cls.db.refresh(cls.driver_user2)

        # Tokens JWT
        cls.root_token = create_access_token(data={"sub": str(cls.root_user.id), "email": cls.root_user.email, "role": "ROOT"})
        cls.coord_token = create_access_token(data={"sub": str(cls.coord_user.id), "email": cls.coord_user.email, "role": "COORDINADOR"})
        cls.driver1_token = create_access_token(data={"sub": str(cls.driver_user1.id), "email": cls.driver_user1.email, "role": "REPARTIDOR"})
        cls.driver2_token = create_access_token(data={"sub": str(cls.driver_user2.id), "email": cls.driver_user2.email, "role": "REPARTIDOR"})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # --- TEST 1: CONTROL DE ACCESO A USUARIOS (SOLO ROOT) ---
    def test_01_users_endpoint_rbac(self):
        """Verifica que solo ROOT pueda consultar y crear usuarios; Coordinador y Repartidor reciben 403."""
        # ROOT puede listar usuarios
        resp = self.client.get("/api/users", cookies={"gtr_session_token": self.root_token})
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

        # COORDINADOR es rechazado con 403
        resp_coord = self.client.get("/api/users", cookies={"gtr_session_token": self.coord_token})
        self.assertEqual(resp_coord.status_code, 403)

        # REPARTIDOR es rechazado con 403
        resp_driver = self.client.get("/api/users", cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(resp_driver.status_code, 403)

    # --- TEST 2: AUDITORÍA DEL SISTEMA (SOLO ROOT) ---
    def test_02_audit_endpoint_rbac(self):
        """Verifica que el módulo de auditoría solo sea accesible para ROOT."""
        # ROOT consulta auditoría
        resp_root = self.client.get("/api/audit", cookies={"gtr_session_token": self.root_token})
        self.assertEqual(resp_root.status_code, 200)

        # COORDINADOR recibe 403
        resp_coord = self.client.get("/api/audit", cookies={"gtr_session_token": self.coord_token})
        self.assertEqual(resp_coord.status_code, 403)

        # REPARTIDOR recibe 403
        resp_driver = self.client.get("/api/audit", cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(resp_driver.status_code, 403)

    # --- TEST 3: CREACIÓN DE RUTAS Y DISTRIBUCIÓN (ROOT & COORDINADOR) ---
    def test_03_route_creation_rbac(self):
        """Verifica que Repartidor no pueda crear ni distribuir rutas aleatorias (403)."""
        # REPARTIDOR intentando crear/distribuir ruta -> 403
        resp_driver = self.client.post("/api/routes/distribute-random", cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(resp_driver.status_code, 403)

        # COORDINADOR sí puede
        resp_coord = self.client.post("/api/routes/distribute-random", cookies={"gtr_session_token": self.coord_token})
        self.assertIn(resp_coord.status_code, [200, 201])

    # --- TEST 4: REGISTRO GPS EN BASE GENERAL COMPARTIDA ---
    def test_04_driver_registers_gps_point(self):
        """Verifica que un repartidor pueda registrar un punto GPS y quede en la Base General."""
        payload = {
            "name": "Tienda La Esperanza Manga",
            "address": "Calle 25 # 22-10",
            "neighborhood": "Manga",
            "city": "Cartagena",
            "reference_point": "Frente a la bahía",
            "latitude": 10.4120,
            "longitude": -75.5380,
            "gps_accuracy": 3.2,
            "location_source": "GPS_DEVICE",
            "client_name": "Tienda La Esperanza",
            "client_phone": "3015559988",
            "force_create_duplicate": True
        }

        resp = self.client.post("/api/points", json=payload, cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(resp.status_code, 201)
        created_point = resp.json()
        self.assertEqual(created_point["name"], "Tienda La Esperanza Manga")
        self.assertEqual(created_point["created_by_user_id"], self.driver_user1.id)
        self.assertEqual(created_point["created_by_user_name"], self.driver_user1.full_name)
        self.assertEqual(created_point["created_by_user_role"], "REPARTIDOR")

        # Guardar ID para siguientes tests
        TestRBACAndGPSSystem.test_point_id = created_point["id"]
        TestRBACAndGPSSystem.test_point_lat = created_point["latitude"]
        TestRBACAndGPSSystem.test_point_lng = created_point["longitude"]

    # --- TEST 5: COMPARTICIÓN INMEDIATA CON OTROS USUARIOS ---
    def test_05_shared_database_access(self):
        """Verifica que el punto creado por Repartidor 1 esté disponible para Repartidor 2, Coordinador y Root."""
        # Repartidor 2 consulta la Base General de puntos
        resp_driver2 = self.client.get("/api/points", cookies={"gtr_session_token": self.driver2_token})
        self.assertEqual(resp_driver2.status_code, 200)
        points_list = resp_driver2.json()
        found = any(p["id"] == self.test_point_id for p in points_list)
        self.assertTrue(found, "Repartidor 2 debe tener acceso al punto registrado por Repartidor 1")

        # Coordinador consulta la Base General
        resp_coord = self.client.get("/api/points", cookies={"gtr_session_token": self.coord_token})
        self.assertEqual(resp_coord.status_code, 200)
        found_coord = any(p["id"] == self.test_point_id for p in resp_coord.json())
        self.assertTrue(found_coord, "Coordinador debe poder ver los puntos registrados en la Base General")

    # --- TEST 6: DETECCIÓN DE DUPLICADOS GPS A MENOS DE 50 METROS ---
    def test_06_gps_duplicate_detection_50m(self):
        """Verifica que si se intenta registrar un punto a <50m, el sistema retorne 409 con advertencia de duplicado."""
        # Coordenada muy cercana (a ~15 metros de distancia)
        near_lat = self.test_point_lat + 0.0001
        near_lng = self.test_point_lng + 0.0001

        # Verificar distancia matemática primero
        dist = haversine_distance_meters(self.test_point_lat, self.test_point_lng, near_lat, near_lng)
        self.assertLess(dist, 50.0, f"Distancia calculada {dist}m debe ser menor a 50m")

        payload_duplicate = {
            "name": "Local Casi Idéntico",
            "address": "Calle 25 # 22-12",
            "neighborhood": "Manga",
            "city": "Cartagena",
            "latitude": near_lat,
            "longitude": near_lng,
            "gps_accuracy": 2.5,
            "client_name": "Cliente Duplicado",
            "client_phone": "3010001122",
            "force_create_duplicate": False # Sin forzar -> debe advertir
        }

        resp = self.client.post("/api/points", json=payload_duplicate, cookies={"gtr_session_token": self.driver2_token})
        self.assertEqual(resp.status_code, 409)
        data = resp.json()
        self.assertTrue(data["detail"]["duplicate_warning"])
        self.assertGreater(len(data["detail"]["nearby_points"]), 0)

    # --- TEST 7: TRAZABILIDAD E HISTORIAL DEL PUNTO ---
    def test_07_point_history_traceability(self):
        """Verifica que los cambios en coordenadas GPS generen entradas en el historial."""
        # Repartidor 2 actualiza las coordenadas del punto
        update_payload = {
            "latitude": 10.4125,
            "longitude": -75.5385,
            "gps_accuracy": 2.0,
            "notes": "Coordenadas corregidas en puerta principal"
        }
        update_resp = self.client.put(f"/api/points/{self.test_point_id}", json=update_payload, cookies={"gtr_session_token": self.driver2_token})
        self.assertEqual(update_resp.status_code, 200)

        # Consultar historial
        hist_resp = self.client.get(f"/api/points/{self.test_point_id}/history", cookies={"gtr_session_token": self.driver2_token})
        self.assertEqual(hist_resp.status_code, 200)
        history = hist_resp.json()
        self.assertGreaterEqual(len(history), 2, "Debe haber al menos 2 registros: creación y actualización GPS")
        self.assertEqual(history[0]["action"], "ACTUALIZACION_GPS")

    # --- TEST 8: VERIFICACIÓN DE LOGS DE AUDITORÍA ---
    def test_08_audit_logs_recorded(self):
        """Verifica que las operaciones críticas hayan quedado registradas en audit_logs."""
        logs = self.db.query(AuditLog).filter(AuditLog.target_id == str(self.test_point_id)).all()
        self.assertGreater(len(logs), 0, "Debe existir al menos un registro de auditoría para el punto")

    # --- TEST 9: REGISTRO DE PUNTO GPS CON FOTOGRAFÍA DE FACHADA (CÁMARA MÓVIL) ---
    def test_09_gps_point_with_camera_photo(self):
        """Verifica que un repartidor pueda registrar un punto GPS con fotografía de la dirección real capturada con la cámara."""
        # 1x1 pixel base64 jpeg dummy
        sample_b64_photo = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        
        payload = {
            "name": "Supermercado Manga Plaza Real",
            "address": "Av. Miramar # 19-45",
            "neighborhood": "Manga",
            "city": "Cartagena",
            "reference_point": "Frente al puente Román",
            "latitude": 10.4155,
            "longitude": -75.5320,
            "gps_accuracy": 2.1,
            "location_source": "GPS_DEVICE",
            "client_name": "Supermercado Manga Plaza",
            "client_phone": "3007778899",
            "photo_data": sample_b64_photo,
            "force_create_duplicate": True
        }

        resp = self.client.post("/api/points", json=payload, cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIsNotNone(data.get("photo_url"))
        self.assertTrue(data["photo_url"].startswith("/static/uploads/points/"))
        self.assertEqual(data["created_by_user_id"], self.driver_user1.id)
        self.assertEqual(data["created_by_user_name"], self.driver_user1.full_name)

        # Verificar historial con foto
        hist_resp = self.client.get(f"/api/points/{data['id']}/history", cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(hist_resp.status_code, 200)
        history = hist_resp.json()
        self.assertIsNotNone(history[0].get("photo_url"))

    # --- TEST 10: ACTUALIZACIÓN DE PUNTO EXISTENTE SIN DUPLICAR CON NUEVA FOTO ---
    def test_10_update_point_with_photo(self):
        """Verifica que el repartidor pueda actualizar las coordenadas y la foto del punto existente sin duplicarlo."""
        sample_b64_photo = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        
        update_payload = {
            "latitude": 10.4128,
            "longitude": -75.5388,
            "gps_accuracy": 1.8,
            "photo_data": sample_b64_photo,
            "notes": "Fotografía y coordenadas actualizadas en campo por el repartidor"
        }
        resp = self.client.put(f"/api/points/{self.test_point_id}", json=update_payload, cookies={"gtr_session_token": self.driver1_token})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNotNone(data.get("photo_url"))
        self.assertTrue(data["photo_url"].startswith("/static/uploads/points/"))

if __name__ == "__main__":
    unittest.main()
