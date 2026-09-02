import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User

class TestAuthSystem(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, follow_redirects=False)

    def test_01_unauthenticated_redirect(self):
        """Verifica que rutas protegidas redirijan a /login si no hay sesión."""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers.get("location"), "/login")

        response = self.client.get("/coordinacion")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers.get("location"), "/login")

    def test_02_login_view(self):
        """Verifica que la página de login cargue con código 200."""
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("GTR", response.text)
        self.assertIn("Iniciar Sesión", response.text)
        self.assertIn("Google", response.text)
        self.assertIn("Outlook", response.text)
        self.assertIn("Corporativo", response.text)

    def test_03_invalid_login(self):
        """Verifica que credenciales incorrectas sean rechazadas con 401."""
        response = self.client.post(
            "/api/auth/login",
            json={"email_or_user": "root@gtrlogistics.com", "password": "wrong_password"}
        )
        self.assertEqual(response.status_code, 401)

    def test_04_root_login_success(self):
        """Verifica inicio de sesión exitoso como ROOT y asignación de cookie."""
        response = self.client.post(
            "/api/auth/login",
            json={"email_or_user": "root@gtrlogistics.com", "password": "GTRAdmin2026!"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["role"], "ROOT")
        self.assertEqual(data["redirect_url"], "/dashboard")
        self.assertIn("gtr_session_token", response.cookies)

        # Probar acceso a /dashboard con la cookie
        cookie_val = response.cookies["gtr_session_token"]
        dash_resp = self.client.get("/dashboard", cookies={"gtr_session_token": cookie_val})
        self.assertEqual(dash_resp.status_code, 200)
        self.assertIn("ROOT", dash_resp.text)

    def test_05_coordinator_login_success(self):
        """Verifica inicio de sesión como COORDINADOR y redirección."""
        response = self.client.post(
            "/api/auth/login",
            json={"email_or_user": "coordinador@gtrlogistics.com", "password": "GTRCoord2026!"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["role"], "COORDINADOR")
        self.assertEqual(data["redirect_url"], "/coordinacion")

    def test_06_driver_login_success(self):
        """Verifica inicio de sesión como REPARTIDOR y redirección a ruta activa."""
        response = self.client.post(
            "/api/auth/login",
            json={"email_or_user": "jose.martinez@gtrlogistics.com", "password": "GTRDriver2026!"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["role"], "REPARTIDOR")
        self.assertEqual(data["redirect_url"], "/repartidor/ruta-activa")

        # Verificar que si el repartidor intenta entrar a /dashboard, se redirige a su app móvil
        cookie_val = response.cookies["gtr_session_token"]
        dash_resp = self.client.get("/dashboard", cookies={"gtr_session_token": cookie_val})
        self.assertEqual(dash_resp.status_code, 303)
        self.assertEqual(dash_resp.headers.get("location"), "/repartidor/ruta-activa")

    def test_07_provider_login_sso(self):
        """Verifica inicio de sesión con proveedores SSO (Google, Outlook, Corporativo)."""
        # Google SSO
        resp_google = self.client.post(
            "/api/auth/provider-login",
            json={"provider": "google", "email": "operador.google@gmail.com"}
        )
        self.assertEqual(resp_google.status_code, 200)
        self.assertEqual(resp_google.json()["user"]["provider"], "GMAIL")

        # Outlook SSO
        resp_outlook = self.client.post(
            "/api/auth/provider-login",
            json={"provider": "outlook", "email": "operador.outlook@outlook.com"}
        )
        self.assertEqual(resp_outlook.status_code, 200)
        self.assertEqual(resp_outlook.json()["user"]["provider"], "OUTLOOK")

        # Corporate SSO
        resp_corp = self.client.post(
            "/api/auth/provider-login",
            json={"provider": "corporate", "email": "root@gtrlogistics.com"}
        )
        self.assertEqual(resp_corp.status_code, 200)
        self.assertEqual(resp_corp.json()["user"]["role"], "ROOT")

    def test_08_me_endpoint_and_logout(self):
        """Verifica /api/auth/me y el proceso de logout."""
        # Login como ROOT
        login_resp = self.client.post(
            "/api/auth/login",
            json={"email_or_user": "root@gtrlogistics.com", "password": "GTRAdmin2026!"}
        )
        cookie_val = login_resp.cookies["gtr_session_token"]

        # Consultar /api/auth/me
        me_resp = self.client.get("/api/auth/me", cookies={"gtr_session_token": cookie_val})
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["email"], "root@gtrlogistics.com")
        self.assertEqual(me_resp.json()["role"], "ROOT")

        # Cerrar sesión
        logout_resp = self.client.get("/logout")
        self.assertEqual(logout_resp.status_code, 303)
        self.assertEqual(logout_resp.headers.get("location"), "/login")

if __name__ == "__main__":
    unittest.main()
