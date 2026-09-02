import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings

from core.models import (
    User, Driver, Client, DeliveryPoint, DeliveryPointHistory,
    Delivery, Route, RouteStop, AuditLog, SystemSetting
)
from core.services.audit import log_audit_event, get_client_ip

def get_global_stats():
    all_deliveries = list(Delivery.objects.all())
    total_deliveries = len(all_deliveries)
    delivered_count = sum(1 for d in all_deliveries if d.status == 'ENTREGADO')
    in_transit_count = sum(1 for d in all_deliveries if d.status == 'EN_CAMINO')
    pending_count = sum(1 for d in all_deliveries if d.status in ['PENDIENTE', 'ASIGNADO'])
    incident_count = sum(1 for d in all_deliveries if d.status == 'INCIDENCIA')

    drivers = list(Driver.objects.all())
    active_drivers = [d for d in drivers if d.status in ['EN_RUTA', 'DISPONIBLE']]
    inactive_drivers = [d for d in drivers if d.status not in ['EN_RUTA', 'DISPONIBLE']]
    total_points = DeliveryPoint.objects.count()
    total_clients = Client.objects.count()

    return {
        "total_deliveries": total_deliveries,
        "pending_deliveries": pending_count,
        "assigned_deliveries": in_transit_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "incident_count": incident_count,
        "total_drivers": len(drivers),
        "active_drivers": len(active_drivers),
        "inactive_drivers": len(inactive_drivers),
        "total_points": total_points,
        "total_clients": total_clients,
        "drivers_list": drivers
    }

def global_context_processor(request):
    stats = get_global_stats()
    return {
        'sidebar_stats': stats,
        'app_name': 'GTR Logistics',
        'current_user': request.user if request.user.is_authenticated else None
    }

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'REPARTIDOR':
            return redirect('driver_mobile')
        return redirect('dashboard')

    error_message = None
    if request.method == 'POST':
        identifier = (request.POST.get('identifier') or request.POST.get('email_or_user') or request.POST.get('email') or request.POST.get('username') or '').strip()
        password = request.POST.get('password', '').strip()

        # Buscar usuario por email o username
        user_obj = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                if not user.is_active:
                    error_message = "Tu cuenta está desactivada. Contacta al administrador."
                else:
                    login(request, user)
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
                    
                    log_audit_event(
                        user=user,
                        action="LOGIN",
                        module="AUTH",
                        ip_address=get_client_ip(request),
                        details={"role": user.role}
                    )
                    
                    if user.role == 'REPARTIDOR':
                        return redirect('driver_mobile')
                    return redirect('dashboard')
            else:
                error_message = "Contraseña incorrecta."
        else:
            error_message = "No existe una cuenta registrada con este correo o usuario."

    return render(request, 'login.html', {'error': error_message})

def logout_view(request):
    if request.user.is_authenticated:
        log_audit_event(
            user=request.user,
            action="LOGOUT",
            module="AUTH",
            ip_address=get_client_ip(request)
        )
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    stats = get_global_stats()
    efficiency_rate = round((stats["delivered_count"] / (stats["total_deliveries"] or 1)) * 100, 1)

    all_deliveries = list(Delivery.objects.select_related('client', 'delivery_point', 'route_stop__route__driver').order_by('id'))
    drivers = Driver.objects.all()
    active_routes = Route.objects.filter(status__in=['OPTIMIZADA', 'EN_PROGRESO']).select_related('driver')

    total_delivered = sum(1 for d in all_deliveries if d.status == 'ENTREGADO')
    total_in_transit = sum(1 for d in all_deliveries if d.status == 'EN_CAMINO')
    total_pending = sum(1 for d in all_deliveries if d.status in ['PENDIENTE', 'ASIGNADO'])
    total_incidents = sum(1 for d in all_deliveries if d.status == 'INCIDENCIA')

    driver_summaries = []
    for driver in drivers:
        active_route = Route.objects.filter(driver=driver).order_by('-created_at').first()
        stops = []
        if active_route:
            stops = list(RouteStop.objects.filter(route=active_route).select_related('delivery').order_by('sequence_order'))
        
        delivered_c = sum(1 for s in stops if s.status == 'COMPLETADO' or (s.delivery and s.delivery.status == 'ENTREGADO'))
        in_transit_c = sum(1 for s in stops if s.status == 'EN_CAMINO' or (s.delivery and s.delivery.status == 'EN_CAMINO'))
        incident_c = sum(1 for s in stops if s.status == 'INCIDENCIA' or (s.delivery and s.delivery.status == 'INCIDENCIA'))
        pending_c = max(0, len(stops) - delivered_c - in_transit_c - incident_c)
        progress_pct = round((delivered_c / len(stops) * 100)) if stops else 0

        driver_summaries.append({
            "driver": driver,
            "route": active_route,
            "stops": stops,
            "total_packages": len(stops),
            "delivered_count": delivered_c,
            "in_transit_count": in_transit_c,
            "incident_count": incident_c,
            "pending_count": pending_c,
            "progress_pct": progress_pct
        })

    return render(request, 'dashboard.html', {
        "kpis": {
            "total": stats["total_deliveries"],
            "delivered": stats["delivered_count"],
            "in_transit": stats["assigned_deliveries"],
            "incidents": stats["incident_count"],
            "pending": stats["pending_deliveries"],
            "efficiency": efficiency_rate,
            "active_drivers_count": stats["active_drivers"],
            "total_drivers_count": stats["total_drivers"],
            "total_points": stats["total_points"],
            "total_clients": stats["total_clients"]
        },
        "deliveries": all_deliveries,
        "total_delivered": total_delivered,
        "total_in_transit": total_in_transit,
        "total_pending": total_pending,
        "total_incidents": total_incidents,
        "drivers": drivers,
        "driver_summaries": driver_summaries,
        "active_routes": active_routes
    })

@login_required
def coordinator_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    all_deliveries = list(Delivery.objects.select_related('client', 'delivery_point', 'route_stop__route__driver').order_by('id'))
    drivers = list(Driver.objects.all().order_by('id'))
    active_routes = list(Route.objects.filter(status__in=['OPTIMIZADA', 'EN_PROGRESO']).select_related('driver'))

    total_delivered = sum(1 for d in all_deliveries if d.status == 'ENTREGADO')
    total_in_transit = sum(1 for d in all_deliveries if d.status == 'EN_CAMINO')
    total_pending = sum(1 for d in all_deliveries if d.status in ['PENDIENTE', 'ASIGNADO'])
    total_incidents = sum(1 for d in all_deliveries if d.status == 'INCIDENCIA')

    active_drivers = [d for d in drivers if d.status in ['EN_RUTA', 'DISPONIBLE']]
    inactive_drivers = [d for d in drivers if d.status not in ['EN_RUTA', 'DISPONIBLE']]
    active_drivers_count = len(active_drivers)
    inactive_drivers_count = len(inactive_drivers)
    total_drivers_count = len(drivers)

    return render(request, 'coordinator.html', {
        "deliveries": all_deliveries,
        "total_delivered": total_delivered,
        "total_in_transit": total_in_transit,
        "total_pending": total_pending,
        "total_incidents": total_incidents,
        "drivers": drivers,
        "active_drivers_count": active_drivers_count,
        "inactive_drivers_count": inactive_drivers_count,
        "total_drivers_count": total_drivers_count,
        "active_routes": active_routes
    })

@login_required
def driver_mobile_view(request, route_id=None):
    current_user = request.user
    route = None
    if route_id:
        route = Route.objects.filter(id=route_id).select_related('driver').first()
    elif current_user.driver:
        route = Route.objects.filter(
            driver=current_user.driver,
            status__in=['EN_PROGRESO', 'OPTIMIZADA']
        ).order_by('-created_at').first()
        
        if not route:
            route = Route.objects.filter(driver=current_user.driver).order_by('-created_at').first()

    if not route:
        route = Route.objects.filter(status__in=['EN_PROGRESO', 'OPTIMIZADA']).order_by('-created_at').first()
        if not route:
            route = Route.objects.order_by('-created_at').first()

    stops = []
    driver = None
    if route:
        stops = RouteStop.objects.filter(route=route).select_related(
            'delivery',
            'delivery__client',
            'delivery__delivery_point',
            'delivery__delivery_point__client'
        ).order_by('sequence_order')
        driver = route.driver
    elif current_user.driver:
        driver = current_user.driver

    clients_list = Client.objects.filter(is_active=True).order_by('name')[:50]

    return render(request, 'driver_mobile.html', {
        "route": route,
        "stops": stops,
        "driver": driver,
        "clients": clients_list
    })

@login_required
def route_optimizer_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    pending_deliveries = Delivery.objects.filter(status='PENDIENTE')
    drivers = Driver.objects.filter(status__in=['DISPONIBLE', 'EN_RUTA'])
    existing_routes = Route.objects.order_by('-created_at')[:5]

    return render(request, 'route_optimizer.html', {
        "pending_deliveries": pending_deliveries,
        "drivers": drivers,
        "existing_routes": existing_routes
    })

@login_required
def new_delivery_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    recent_deliveries = Delivery.objects.order_by('-created_at')[:6]
    return render(request, 'new_delivery.html', {
        "recent_deliveries": recent_deliveries
    })

@login_required
def points_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    points = DeliveryPoint.objects.select_related('client', 'created_by_user').order_by('-created_at')
    clients = Client.objects.order_by('-created_at')

    return render(request, 'points.html', {
        "points": points,
        "clients": clients
    })

@login_required
def users_view(request):
    if request.user.role != 'ROOT':
        return redirect('dashboard')

    users = User.objects.select_related('driver').order_by('id')
    drivers = Driver.objects.all()
    return render(request, 'users.html', {
        "users": users,
        "drivers": drivers
    })

@login_required
def audit_view(request):
    if request.user.role != 'ROOT':
        return redirect('dashboard')

    recent_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:150]
    return render(request, 'audit.html', {
        "logs": recent_logs
    })

@login_required
def data_import_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    recent_deliveries = Delivery.objects.order_by('-created_at')[:15]
    drivers = Driver.objects.all()
    return render(request, 'data_import.html', {
        "recent_deliveries": recent_deliveries,
        "drivers": drivers
    })

@login_required
def driver_monitoring_view(request):
    if request.user.role == 'REPARTIDOR':
        return redirect('driver_mobile')

    from core.models import DriverNovelty
    drivers = Driver.objects.all()
    active_routes = Route.objects.filter(status__in=['OPTIMIZADA', 'EN_PROGRESO']).select_related('driver')
    
    # Asegurar algunas novedades de demostración en tiempo real si está vacía
    if DriverNovelty.objects.count() == 0 and drivers.exists():
        d1 = drivers[0]
        d2 = drivers[1] if len(drivers) > 1 else d1
        d3 = drivers[2] if len(drivers) > 2 else d1
        DriverNovelty.objects.create(
            driver=d1,
            novelty_type='CLIENTE_AUSENTE',
            severity='MEDIA',
            title='Cliente Ausente en Baluarte Santo Domingo',
            description='Se timbró y llamó al destinatario 3 veces (3004528901). Dejó mensaje solicitando reintentar en 30 minutos.',
            latitude=10.4236,
            longitude=-75.5524
        )
        DriverNovelty.objects.create(
            driver=d2,
            novelty_type='TRAFICO_CLIMA',
            severity='BAJA',
            title='Lluvia Intensa y Tráfico Lento en Bocagrande',
            description='Fuerte aguacero en la Av. San Martín. Velocidad reducida a 15 km/h por seguridad de la carga.',
            latitude=10.4012,
            longitude=-75.5543
        )
        DriverNovelty.objects.create(
            driver=d3,
            novelty_type='DIRECCION_ERRONEA',
            severity='ALTA',
            title='Cambio de Nomenclatura en Barrio Manga',
            description='La dirección Calle Real # 24-80 no coincide con la placa física. Se contactó al cliente y confirmó Callejón Dede # 24-82.',
            latitude=10.4132,
            longitude=-75.5367
        )

    novelties_qs = DriverNovelty.objects.select_related('driver', 'delivery', 'resolved_by_user').order_by('-created_at')[:50]
    novelties = list(novelties_qs)
    active_novelties_total = DriverNovelty.objects.filter(is_resolved=False).count()

    # Resumen de repartidores con métricas de paradas
    driver_cards = []
    for drv in drivers:
        route = Route.objects.filter(driver=drv).order_by('-created_at').first()
        stops = list(RouteStop.objects.filter(route=route).select_related('delivery').order_by('sequence_order')) if route else []
        delivered = sum(1 for s in stops if s.status == 'COMPLETADO' or (s.delivery and s.delivery.status == 'ENTREGADO'))
        in_transit = sum(1 for s in stops if s.status == 'EN_CAMINO' or (s.delivery and s.delivery.status == 'EN_CAMINO'))
        incidents = sum(1 for s in stops if s.status == 'INCIDENCIA' or (s.delivery and s.delivery.status == 'INCIDENCIA'))
        pending = max(0, len(stops) - delivered - in_transit - incidents)
        progress = round((delivered / len(stops) * 100)) if stops else 0
        driver_novelties_count = sum(1 for n in novelties if n.driver_id == drv.id and not n.is_resolved)

        driver_cards.append({
            "driver": drv,
            "route": route,
            "stops": stops,
            "total_stops": len(stops),
            "delivered": delivered,
            "in_transit": in_transit,
            "incidents": incidents,
            "pending": pending,
            "progress_pct": progress,
            "active_novelties_count": driver_novelties_count,
            "battery_pct": 82 if drv.id % 2 == 0 else 94,
            "speed_kmh": 28 if drv.status == 'EN_RUTA' else 0
        })

    return render(request, 'driver_monitoring.html', {
        "drivers": drivers,
        "driver_cards": driver_cards,
        "active_routes": active_routes,
        "novelties": novelties,
        "active_novelties_count": active_novelties_total
    })


