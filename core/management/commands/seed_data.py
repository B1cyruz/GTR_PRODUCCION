from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Driver, DeliveryPoint, SystemSetting
from core.services.distribution import distribute_random_deliveries, DEFAULT_DRIVERS_DATA

User = get_user_model()

DEFAULT_USERS_DATA = [
    {
        "username": "admin",
        "email": "admin@gtrlogistics.com",
        "full_name": "Super Admin (ROOT)",
        "password": "Admin123*",
        "role": "ROOT",
        "provider": "CORPORATIVO",
        "phone": "300 111 0000",
        "is_staff": True,
        "is_superuser": True
    },
    {
        "username": "root",
        "email": "root@gtrlogistics.com",
        "full_name": "Administrador Principal",
        "password": "Admin123*",
        "role": "ROOT",
        "provider": "CORPORATIVO",
        "phone": "300 111 0001",
        "is_staff": True,
        "is_superuser": True
    },
    {
        "username": "coordinador",
        "email": "coordinacion@gtrlogistics.com",
        "full_name": "Carlos D. Despacho (Coordinador)",
        "password": "Coord123*",
        "role": "COORDINADOR",
        "provider": "CORPORATIVO",
        "phone": "312 456 7890",
        "is_staff": False
    },
    {
        "username": "repartidor1",
        "email": "jose.martinez@gtrlogistics.com",
        "full_name": "José P. Martínez",
        "password": "Driver123*",
        "role": "REPARTIDOR",
        "provider": "CORPORATIVO",
        "driver_name": "José P. Martínez",
        "phone": "300 452 8910",
        "is_staff": False
    },
    {
        "username": "repartidor2",
        "email": "sergio.salgado@gtrlogistics.com",
        "full_name": "Sergio A. Salgado",
        "password": "Driver123*",
        "role": "REPARTIDOR",
        "provider": "CORPORATIVO",
        "driver_name": "Sergio A. Salgado",
        "phone": "312 889 1234",
        "is_staff": False
    },
    {
        "username": "repartidor3",
        "email": "juan.espinosa@gtrlogistics.com",
        "full_name": "Juan S. Espinosa",
        "password": "Driver123*",
        "role": "REPARTIDOR",
        "provider": "CORPORATIVO",
        "driver_name": "Juan S. Espinosa",
        "phone": "318 765 4321",
        "is_staff": False
    },
    {
        "username": "repartidor4",
        "email": "juan.amazan@gtrlogistics.com",
        "full_name": "Juan D. Amazan",
        "password": "Driver123*",
        "role": "REPARTIDOR",
        "provider": "CORPORATIVO",
        "driver_name": "Juan D. Amazan",
        "phone": "301 998 7766",
        "is_staff": False
    }
]

class Command(BaseCommand):
    help = "Puebla la base de datos de GTR con conductores, rutas, clientes, puntos GPS y usuarios demo"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Iniciando sembrado de datos en GTR (Django 5.2) ==="))

        # 1. Distribuir rutas y entregas
        self.stdout.write(" [1/3] Creando conductores y distribuyendo rutas optimizadas en Cartagena...")
        dist_res = distribute_random_deliveries(seed_if_needed=True)
        self.stdout.write(self.style.SUCCESS(f"  [OK] {dist_res['message']}"))

        # 2. Crear Usuarios para los 3 Roles
        self.stdout.write(" [2/3] Registrando usuarios de demostracion (ROOT, COORDINADOR, REPARTIDOR)...")
        drivers_map = {d.name: d for d in Driver.objects.all()}

        from django.db.models import Q

        for u_data in DEFAULT_USERS_DATA:
            email = u_data["email"]
            driver_name = u_data.get("driver_name")
            driver_obj = drivers_map.get(driver_name) if driver_name else None

            user = User.objects.filter(Q(username=u_data["username"]) | Q(email=email)).first()
            if not user:
                user = User(
                    username=u_data["username"],
                    email=email,
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    provider=u_data["provider"],
                    phone=u_data["phone"],
                    driver=driver_obj,
                    is_staff=u_data.get("is_staff", False),
                    is_superuser=u_data.get("is_superuser", False),
                    is_active=True
                )
                user.set_password(u_data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  [OK] Creado: {user.username} ({user.role}) - {email}"))
            else:
                user.username = u_data["username"]
                user.email = email
                user.full_name = u_data["full_name"]
                user.role = u_data["role"]
                user.provider = u_data["provider"]
                user.phone = u_data["phone"]
                user.driver = driver_obj
                user.is_staff = u_data.get("is_staff", False)
                user.is_superuser = u_data.get("is_superuser", False)
                user.is_active = True
                user.set_password(u_data["password"])
                user.save()
                self.stdout.write(f"  * Actualizado: {user.username} ({user.role})")

        # 3. Configuraciones del sistema
        self.stdout.write(" [3/3] Inicializando configuraciones operativas del sistema...")
        default_settings = [
            ("DEPOT_NAME", "Centro de Distribucion GTR - Manga", "Nombre del centro logistico"),
            ("DEPOT_LATITUDE", "10.4075", "Latitud del almacen central"),
            ("DEPOT_LONGITUDE", "-75.5342", "Longitud del almacen central"),
            ("DUPLICATE_GPS_THRESHOLD_METERS", "50.0", "Radio de deteccion de duplicados en metros"),
            ("MAX_STOPS_PER_ROUTE", "25", "Maximo de paradas por ruta diaria")
        ]
        for key, val, desc in default_settings:
            SystemSetting.objects.get_or_create(key=key, defaults={"value": val, "description": desc})

        self.stdout.write(self.style.SUCCESS("=== Base de datos poblada exitosamente con todos los datos operativos ==="))
