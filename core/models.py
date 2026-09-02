from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json

class Driver(models.Model):
    STATUS_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('EN_RUTA', 'En Ruta'),
        ('INACTIVO', 'Inactivo'),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=255, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, default='MOTO')
    vehicle_plate = models.CharField(max_length=50)
    capacity_kg = models.FloatField(default=50.0)
    current_lat = models.FloatField(default=10.4075, null=True, blank=True)
    current_lng = models.FloatField(default=-75.5342, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DISPONIBLE')
    avatar_url = models.CharField(max_length=500, blank=True, null=True)
    rating = models.FloatField(default=5.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drivers'
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.vehicle_plate})"

    @property
    def max_capacity_kg(self):
        return self.capacity_kg

    @property
    def current_latitude(self):
        return self.current_lat

    @property
    def current_longitude(self):
        return self.current_lng


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ROOT', 'Super Admin (ROOT)'),
        ('COORDINADOR', 'Coordinador de Transporte'),
        ('REPARTIDOR', 'Repartidor / Conductor'),
    ]
    PROVIDER_CHOICES = [
        ('LOCAL', 'Local'),
        ('CORPORATIVO', 'Corporativo'),
    ]

    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='COORDINADOR')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='LOCAL')
    phone = models.CharField(max_length=50, blank=True, null=True)
    avatar_url = models.CharField(max_length=500, blank=True, null=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='app_users')
    
    class Meta:
        db_table = 'users'
        ordering = ['id']

    def __str__(self):
        return f"{self.email or self.username} ({self.role})"

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip() or self.username
        if not self.username and self.email:
            self.username = self.email
        super().save(*args, **kwargs)


class Client(models.Model):
    name = models.CharField(max_length=255)
    document_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, default='Cartagena')
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.city})"


class DeliveryPoint(models.Model):
    STATUS_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('VERIFICADO', 'Verificado'),
    ]

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='points')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, default='Cartagena')
    reference_point = models.CharField(max_length=255, blank=True, null=True)
    
    latitude = models.FloatField(db_index=True)
    longitude = models.FloatField(db_index=True)
    gps_accuracy = models.FloatField(null=True, blank=True)
    location_source = models.CharField(max_length=50, default='GPS_DEVICE')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='ACTIVO')
    notes = models.TextField(blank=True, null=True)
    photo_url = models.CharField(max_length=500, blank=True, null=True)
    
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_points')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_points')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_points'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.address}"

    @property
    def created_by_user_name(self) -> str:
        return self.created_by_user.full_name if self.created_by_user else "Sistema"

    @property
    def created_by_user_role(self) -> str:
        return self.created_by_user.role if self.created_by_user else "SISTEMA"


class DeliveryPointHistory(models.Model):
    delivery_point = models.ForeignKey(DeliveryPoint, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    action = models.CharField(max_length=50, default='CREACION')
    previous_latitude = models.FloatField(null=True, blank=True)
    previous_longitude = models.FloatField(null=True, blank=True)
    new_latitude = models.FloatField()
    new_longitude = models.FloatField()
    gps_accuracy = models.FloatField(null=True, blank=True)
    photo_url = models.CharField(max_length=500, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'delivery_point_history'
        ordering = ['-created_at']

    @property
    def user_name(self) -> str:
        return self.user.full_name if self.user else "Sistema"


class Delivery(models.Model):
    PRIORITY_CHOICES = [
        ('ALTA', 'Alta'),
        ('MEDIA', 'Media'),
        ('BAJA', 'Baja'),
    ]
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ASIGNADO', 'Asignado'),
        ('EN_CAMINO', 'En Camino'),
        ('ENTREGADO', 'Entregado'),
        ('INCIDENCIA', 'Incidencia'),
        ('CANCELADO', 'Cancelado'),
    ]

    tracking_code = models.CharField(max_length=50, unique=True, db_index=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    delivery_point = models.ForeignKey(DeliveryPoint, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')

    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_phone = models.CharField(max_length=50, blank=True, null=True)
    sender_document = models.CharField(max_length=50, blank=True, null=True)

    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=50)
    recipient_email = models.EmailField(blank=True, null=True)
    
    address = models.CharField(max_length=500)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, default='Cartagena')
    latitude = models.FloatField()
    longitude = models.FloatField()
    reference_point = models.CharField(max_length=255, blank=True, null=True)
    
    package_type = models.CharField(max_length=100, default='PAQUETE_MEDIANO')
    weight_kg = models.FloatField(default=1.0)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='MEDIA')
    time_window_start = models.CharField(max_length=10, default='08:00')
    time_window_end = models.CharField(max_length=10, default='18:00')
    notes = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDIENTE')
    delivered_at = models.DateTimeField(null=True, blank=True)
    recipient_id_card = models.CharField(max_length=50, blank=True, null=True)
    signature_svg = models.TextField(blank=True, null=True)
    proof_photo_url = models.CharField(max_length=500, blank=True, null=True)
    incident_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'deliveries'
        ordering = ['id']

    def __str__(self):
        return f"{self.tracking_code} - {self.recipient_name}"

    @property
    def place_name(self) -> str:
        if self.delivery_point and self.delivery_point.name:
            return self.delivery_point.name
        if self.client and self.client.name:
            return self.client.name
        return self.recipient_name

    @property
    def place_phone(self) -> str:
        if self.delivery_point and self.delivery_point.client and self.delivery_point.client.phone:
            return self.delivery_point.client.phone
        if self.client and self.client.phone:
            return self.client.phone
        return self.recipient_phone


class Route(models.Model):
    STATUS_CHOICES = [
        ('PLANIFICADA', 'Planificada'),
        ('OPTIMIZADA', 'Optimizada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    
    total_stops = models.IntegerField(default=0)
    completed_stops = models.IntegerField(default=0)
    total_distance_km = models.FloatField(default=0.0)
    estimated_duration_min = models.IntegerField(default=0)
    
    depot_name = models.CharField(max_length=255, default="Centro Logístico GTR - Manga")
    depot_lat = models.FloatField(default=10.4075)
    depot_lng = models.FloatField(default=-75.5342)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='OPTIMIZADA')
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'routes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RouteStop(models.Model):
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_CAMINO', 'En Camino'),
        ('COMPLETADO', 'Completado'),
        ('INCIDENCIA', 'Incidencia'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='route_stop')
    sequence_order = models.IntegerField()
    estimated_arrival = models.CharField(max_length=10, blank=True, null=True)
    distance_from_prev_km = models.FloatField(default=0.0)
    travel_time_min = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDIENTE')
    arrival_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'route_stops'
        ordering = ['sequence_order']

    def __str__(self):
        return f"Parada #{self.sequence_order} en {self.route.code}"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.CharField(max_length=100, blank=True, null=True)
    details_json = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='SUCCESS')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    @property
    def user_name(self) -> str:
        return self.user.full_name if self.user else "Sistema"

    @property
    def details_dict(self):
        if not self.details_json:
            return {}
        try:
            return json.loads(self.details_json)
        except Exception:
            return {}


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'

    def __str__(self):
        return self.key


class DriverNovelty(models.Model):
    NOVELTY_TYPE_CHOICES = [
        ('INCIDENCIA_ENTREGA', 'Incidencia en Entrega'),
        ('CLIENTE_AUSENTE', 'Cliente Ausente'),
        ('DIRECCION_ERRONEA', 'Dirección no Encontrada / Cambio Nomenclatura'),
        ('TRAFICO_CLIMA', 'Tráfico Pesado / Clima / Lluvia'),
        ('VEHICULO_MECANICA', 'Vehículo / Falla Mecánica'),
        ('PAUSA_DESCANSO', 'Pausa Activa / Almuerzo'),
        ('OTRO', 'Otra Novedad Operativa'),
    ]
    SEVERITY_CHOICES = [
        ('BAJA', 'Baja / Informativa'),
        ('MEDIA', 'Media / Precaución'),
        ('ALTA', 'Alta / Urgente'),
    ]

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='novelties')
    delivery = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True, related_name='novelties')
    novelty_type = models.CharField(max_length=50, choices=NOVELTY_TYPE_CHOICES, default='INCIDENCIA_ENTREGA')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIA')
    title = models.CharField(max_length=255)
    description = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    photo_url = models.CharField(max_length=500, blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_novelties')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'driver_novelties'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.driver.name} - {self.title}"

