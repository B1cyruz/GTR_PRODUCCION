from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Driver, Client, DeliveryPoint, DeliveryPointHistory,
    Delivery, Route, RouteStop, AuditLog, SystemSetting
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'driver', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Datos GTR', {'fields': ('full_name', 'role', 'provider', 'phone', 'avatar_url', 'driver')}),
    )

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'vehicle_plate', 'vehicle_type', 'status', 'max_capacity_kg')
    list_filter = ('status', 'vehicle_type')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'document_id', 'phone', 'city', 'is_active')
    search_fields = ('name', 'document_id', 'phone')

@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'neighborhood', 'city', 'latitude', 'longitude', 'status', 'created_by_user')
    list_filter = ('status', 'city')
    search_fields = ('name', 'address')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'recipient_name', 'address', 'priority', 'status', 'package_type')
    list_filter = ('status', 'priority', 'package_type')
    search_fields = ('tracking_code', 'recipient_name', 'address')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'driver', 'status', 'total_stops', 'completed_stops', 'created_at')
    list_filter = ('status', 'created_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'module', 'user', 'ip_address', 'status', 'created_at')
    list_filter = ('module', 'status')
