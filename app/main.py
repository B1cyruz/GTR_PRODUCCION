import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, ensure_schema_updates
import app.models # ensure all models are registered
from app.routers import (
    deliveries_router,
    drivers_router,
    routes_router,
    users_router,
    points_router,
    clients_router,
    audit_router,
    system_router,
    auth_router,
    web_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización de tablas y columnas en base de datos PostgreSQL
    try:
        Base.metadata.create_all(bind=engine)
        ensure_schema_updates()
        print(" [PostgreSQL] Tablas y columnas de GTR verificadas y sincronizadas exitosamente.")
    except Exception as e:
        print(f" [Aviso BD] No se pudo conectar inmediatamente a PostgreSQL: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Plataforma Integral de Gestión Logística, Despacho, RBAC y Base General de Puntos GPS (GTR)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montaje de archivos estáticos
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Inclusión de Enrutadores
app.include_router(auth_router)
app.include_router(web_router)
app.include_router(users_router)
app.include_router(points_router)
app.include_router(clients_router)
app.include_router(audit_router)
app.include_router(system_router)
app.include_router(deliveries_router)
app.include_router(drivers_router)
app.include_router(routes_router)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": "PostgreSQL",
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
