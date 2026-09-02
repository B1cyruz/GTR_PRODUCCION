from app.routers.api_deliveries import router as deliveries_router
from app.routers.api_drivers import router as drivers_router
from app.routers.api_routes import router as routes_router
from app.routers.api_users import router as users_router
from app.routers.api_points import router as points_router
from app.routers.api_clients import router as clients_router
from app.routers.api_audit import router as audit_router
from app.routers.api_system import router as system_router
from app.routers.auth import router as auth_router
from app.routers.web import router as web_router

__all__ = [
    "deliveries_router",
    "drivers_router",
    "routes_router",
    "users_router",
    "points_router",
    "clients_router",
    "audit_router",
    "system_router",
    "auth_router",
    "web_router"
]
