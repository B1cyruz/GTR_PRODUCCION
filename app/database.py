from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Conexión exclusiva a PostgreSQL
# pool_size y max_overflow configurados para alta concurrencia en producción
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_schema_updates():
    """Garantiza que todas las columnas e índices requeridos existan en PostgreSQL mediante ALTER TABLE seguro."""
    alter_statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'COORDINADOR';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider VARCHAR(50) DEFAULT 'LOCAL';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS driver_id INTEGER REFERENCES drivers(id);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        
        # Clientes y Puntos
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER REFERENCES users(id);",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER REFERENCES users(id);",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS updated_by_user_id INTEGER REFERENCES users(id);",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS gps_accuracy FLOAT;",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS location_source VARCHAR(50) DEFAULT 'GPS_DEVICE';",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS reference_point VARCHAR(255);",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100);",
        "ALTER TABLE delivery_points ADD COLUMN IF NOT EXISTS photo_url VARCHAR(500);",
        "ALTER TABLE delivery_point_history ADD COLUMN IF NOT EXISTS photo_url VARCHAR(500);",
        "ALTER TABLE deliveries ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id);",
        "ALTER TABLE deliveries ADD COLUMN IF NOT EXISTS delivery_point_id INTEGER REFERENCES delivery_points(id);"
    ]
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

