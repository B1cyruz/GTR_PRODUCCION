"""
Script de Semillas (Seed Data) para GTR Logistics
Puebla la base de datos PostgreSQL con:
1. Usuarios de los 3 roles: ROOT / Administrador, Coordinador de Transporte y Repartidor.
2. Repartidores de la flota y envíos en Cartagena distribuidos aleatoriamente con rutas optimizadas.
3. Base general de clientes y puntos GPS georreferenciados con historial de trazabilidad.
4. Configuraciones y parámetros del sistema.
"""
from datetime import datetime
from app.database import engine, SessionLocal, Base, ensure_schema_updates
from app.models.user import User
from app.models.driver import Driver
from app.models.client import Client
from app.models.delivery_point import DeliveryPoint, DeliveryPointHistory
from app.models.system_setting import SystemSetting
from app.services.auth import get_password_hash
from app.services.distribution import distribute_random_deliveries
from app.routers.api_system import seed_system_settings_if_empty

def seed_database():
    print(" [1/4] Verificando esquemas y tablas en PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    db = SessionLocal()

    try:
        # 1. Distribuir envíos y rutas
        print(" [2/4] Distribuyendo y asignando envíos aleatoriamente a todos los repartidores...")
        result = distribute_random_deliveries(db, seed_if_needed=True)
        print(f" {result['message']}")
        for r in result.get("routes", []):
            print(f"  • {r['driver_name']} -> {r['route_code']} ({r['route_name']}): {r['total_packages']} paquetes ({r['delivered']} entregados).")

        # 2. Crear Usuarios para los 3 Roles (ROOT, COORDINADOR, REPARTIDOR)
        print(" [3/4] Registrando usuarios de demostración para los 3 roles (ROOT, COORDINADOR, REPARTIDOR)...")
        
        drivers_in_db = {d.name: d for d in db.query(Driver).all()}

        default_users = [
            {
                "email": "root@gtrlogistics.com",
                "full_name": "Super Admin (ROOT)",
                "hashed_password": get_password_hash("GTRAdmin2026!"),
                "role": "ROOT",
                "provider": "CORPORATIVO",
                "phone": "300 111 0000",
                "is_active": True
            },
            {
                "email": "admin@gtrlogistics.com",
                "full_name": "Administrador Principal",
                "hashed_password": get_password_hash("GTRAdmin2026!"),
                "role": "ROOT",
                "provider": "CORPORATIVO",
                "phone": "300 111 0001",
                "is_active": True
            },
            {
                "email": "coordinador@gtrlogistics.com",
                "full_name": "Carlos D. Despacho (Coordinador)",
                "hashed_password": get_password_hash("GTRCoord2026!"),
                "role": "COORDINADOR",
                "provider": "CORPORATIVO",
                "phone": "312 456 7890",
                "is_active": True
            },
            {
                "email": "jose.martinez@gtrlogistics.com",
                "full_name": "José P. Martínez",
                "hashed_password": get_password_hash("GTRDriver2026!"),
                "role": "REPARTIDOR",
                "provider": "CORPORATIVO",
                "driver_id": drivers_in_db.get("José P. Martínez").id if drivers_in_db.get("José P. Martínez") else None,
                "phone": "300 452 8910",
                "is_active": True
            },
            {
                "email": "sergio.salgado@gtrlogistics.com",
                "full_name": "Sergio A. Salgado",
                "hashed_password": get_password_hash("GTRDriver2026!"),
                "role": "REPARTIDOR",
                "provider": "CORPORATIVO",
                "driver_id": drivers_in_db.get("Sergio A. Salgado").id if drivers_in_db.get("Sergio A. Salgado") else None,
                "phone": "312 889 1234",
                "is_active": True
            },
            {
                "email": "juan.espinosa@gtrlogistics.com",
                "full_name": "Juan S. Espinosa",
                "hashed_password": get_password_hash("GTRDriver2026!"),
                "role": "REPARTIDOR",
                "provider": "CORPORATIVO",
                "driver_id": drivers_in_db.get("Juan S. Espinosa").id if drivers_in_db.get("Juan S. Espinosa") else None,
                "phone": "318 765 4321",
                "is_active": True
            },
            {
                "email": "juan.amazan@gtrlogistics.com",
                "full_name": "Juan D. Amazan",
                "hashed_password": get_password_hash("GTRDriver2026!"),
                "role": "REPARTIDOR",
                "provider": "CORPORATIVO",
                "driver_id": drivers_in_db.get("Juan D. Amazan").id if drivers_in_db.get("Juan D. Amazan") else None,
                "phone": "301 998 7766",
                "is_active": True
            }
        ]

        user_map = {}
        for u_data in default_users:
            existing_user = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing_user:
                new_u = User(**u_data)
                db.add(new_u)
                db.flush()
                user_map[u_data["full_name"]] = new_u
                print(f"  [OK] Usuario creado: {u_data['email']} [{u_data['role']}]")
            else:
                existing_user.role = u_data["role"]
                existing_user.full_name = u_data["full_name"]
                existing_user.hashed_password = u_data["hashed_password"]
                existing_user.provider = u_data["provider"]
                existing_user.driver_id = u_data.get("driver_id")
                db.flush()
                user_map[u_data["full_name"]] = existing_user
                print(f"  [OK] Usuario actualizado: {u_data['email']} [{u_data['role']}]")

        db.commit()

        # 3. Poblar Base General de Clientes y Puntos GPS Compartidos
        print(" [4/4] Sembrando Base General de Clientes y Puntos GPS compartidos...")
        root_user = user_map.get("Super Admin (ROOT)") or db.query(User).filter(User.role == "ROOT").first()
        coord_user = user_map.get("Carlos D. Despacho (Coordinador)")
        u_jose = user_map.get("José P. Martínez")
        u_sergio = user_map.get("Sergio A. Salgado")
        u_espinosa = user_map.get("Juan S. Espinosa")
        u_amazan = user_map.get("Juan D. Amazan")

        sample_clients_and_points = [
            {
                "name": "Ferretería El Carmen Manga",
                "document_id": "900123456-1",
                "phone": "300 987 6543",
                "address": "Calle Real de Manga #24-50",
                "neighborhood": "Manga",
                "city": "Cartagena",
                "lat": 10.4092,
                "lng": -75.5310,
                "ref": "Frente al parque de Manga",
                "accuracy": 3.8,
                "author": u_jose
            },
            {
                "name": "Droguería Bocagrande Express",
                "document_id": "800987654-2",
                "phone": "315 456 7890",
                "address": "Cra 3 # 6-45",
                "neighborhood": "Bocagrande",
                "city": "Cartagena",
                "lat": 10.4010,
                "lng": -75.5560,
                "ref": "Diagonal al Hotel Caribe",
                "accuracy": 4.2,
                "author": u_sergio
            },
            {
                "name": "Supermercado Pie de la Popa",
                "document_id": "901234567-3",
                "phone": "320 654 3210",
                "address": "Calle 30 # 21-80",
                "neighborhood": "Pie de la Popa",
                "city": "Cartagena",
                "lat": 10.4185,
                "lng": -75.5280,
                "ref": "A 100m de la subida a la Popa",
                "accuracy": 5.0,
                "author": u_espinosa
            },
            {
                "name": "Distribuidora Industrial Mamonal",
                "document_id": "900778899-4",
                "phone": "301 333 4455",
                "address": "Km 7 Vía Mamonal Sector Puerta de Hierro",
                "neighborhood": "Mamonal",
                "city": "Cartagena",
                "lat": 10.3340,
                "lng": -75.4980,
                "ref": "Entrada principal frente a Reficar",
                "accuracy": 4.5,
                "author": u_amazan
            },
            {
                "name": "Restaurante Portal de San Diego",
                "document_id": "901887766-5",
                "phone": "300 444 8899",
                "address": "Calle Stuart # 7-14 Plaza San Diego",
                "neighborhood": "Centro Histórico",
                "city": "Cartagena",
                "lat": 10.4262,
                "lng": -75.5471,
                "ref": "Frente a la Escuela de Bellas Artes",
                "accuracy": 3.2,
                "author": u_espinosa
            },
            {
                "name": "Clínica MediCentro Castillogrande",
                "document_id": "890554433-6",
                "phone": "314 556 7890",
                "address": "Calle 6 # 14-45 Edificio Castillogrande Bay",
                "neighborhood": "Castillogrande",
                "city": "Cartagena",
                "lat": 10.3915,
                "lng": -75.5523,
                "ref": "Esquina con vista a la bahía",
                "accuracy": 4.0,
                "author": u_sergio
            },
            {
                "name": "Depósito y Abarrotes Getsemaní",
                "document_id": "900665544-7",
                "phone": "300 222 1100",
                "address": "Calle de la Sierpe # 29-15",
                "neighborhood": "Getsemaní",
                "city": "Cartagena",
                "lat": 10.4201,
                "lng": -75.5448,
                "ref": "A media cuadra de Plaza de la Trinidad",
                "accuracy": 3.5,
                "author": u_jose
            },
            {
                "name": "Hotel Boutique San Agustín",
                "document_id": "900332211-8",
                "phone": "310 998 1234",
                "address": "Calle de la Universidad # 36-44",
                "neighborhood": "Centro Histórico",
                "city": "Cartagena",
                "lat": 10.4240,
                "lng": -75.5510,
                "ref": "Al lado de la sede San Agustín Universidad de Cartagena",
                "accuracy": 3.0,
                "author": coord_user or root_user
            }
        ]

        for c_data in sample_clients_and_points:
            author_user = c_data["author"] or root_user
            client = db.query(Client).filter(Client.name == c_data["name"]).first()
            if not client:
                client = Client(
                    name=c_data["name"],
                    document_id=c_data["document_id"],
                    phone=c_data["phone"],
                    address=c_data["address"],
                    neighborhood=c_data["neighborhood"],
                    city=c_data["city"],
                    created_by_user_id=author_user.id if author_user else None,
                    created_at=datetime.utcnow()
                )
                db.add(client)
                db.flush()

            point = db.query(DeliveryPoint).filter(DeliveryPoint.name == c_data["name"]).first()
            if not point:
                point = DeliveryPoint(
                    client_id=client.id,
                    name=c_data["name"],
                    address=c_data["address"],
                    neighborhood=c_data["neighborhood"],
                    city=c_data["city"],
                    reference_point=c_data["ref"],
                    latitude=c_data["lat"],
                    longitude=c_data["lng"],
                    gps_accuracy=c_data["accuracy"],
                    location_source="GPS_DEVICE",
                    status="ACTIVO",
                    created_by_user_id=author_user.id if author_user else None,
                    updated_by_user_id=author_user.id if author_user else None,
                    created_at=datetime.utcnow()
                )
                db.add(point)
                db.flush()

                history = DeliveryPointHistory(
                    delivery_point_id=point.id,
                    user_id=point.created_by_user_id,
                    action="CREACION",
                    new_latitude=point.latitude,
                    new_longitude=point.longitude,
                    gps_accuracy=point.gps_accuracy,
                    notes=f"Punto registrado por {author_user.full_name if author_user else 'Sistema'} ({author_user.role if author_user else 'ROOT'}). Validado con GPS móvil.",
                    created_at=datetime.utcnow()
                )
                db.add(history)
                print(f"  [OK] Punto GPS registrado: {point.name} por {author_user.full_name if author_user else 'Sistema'}")
            else:
                point.created_by_user_id = author_user.id if author_user else point.created_by_user_id
                point.reference_point = c_data["ref"]
                point.gps_accuracy = c_data["accuracy"]
                db.flush()
                print(f"  [OK] Punto GPS actualizado: {point.name} con autor {author_user.full_name if author_user else 'Sistema'}")

        seed_system_settings_if_empty(db)
        db.commit()
        print("\n [EXITO TOTAL] Base de datos, esquemas RBAC, Base General de Puntos y Envíos sincronizados.")
    except Exception as e:
        db.rollback()
        print(f" [Error] Falló la siembra de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

