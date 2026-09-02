import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "GTR - Gestión Logística y Rutas")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "gtr_secret_super_secure_key_adso_2026")
    
    # PostgreSQL configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "gtr_db")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'gtr_db')}"
    )
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

    # Coordenadas por defecto (Cartagena, Colombia)
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Cartagena")
    DEFAULT_LAT: float = float(os.getenv("DEFAULT_LAT", "10.3997"))
    DEFAULT_LNG: float = float(os.getenv("DEFAULT_LNG", "-75.5144"))
    DEFAULT_ZOOM: int = int(os.getenv("DEFAULT_ZOOM", "13"))

    class Config:
        case_sensitive = True

settings = Settings()
