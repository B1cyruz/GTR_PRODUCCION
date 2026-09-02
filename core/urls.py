from django.urls import path
from core import views, api_views

urlpatterns = [
    # --- VISTAS WEB ---
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('coordinacion/', views.coordinator_view, name='coordinator'),
    path('despacho/', views.coordinator_view, name='dispatch'),
    
    # Nuevos Módulos del Coordinador
    path('cargas/', views.data_import_view, name='data_import'),
    path('entregas/importar/', views.data_import_view, name='deliveries_import'),
    path('repartidores/monitoreo/', views.driver_monitoring_view, name='driver_monitoring'),
    path('repartidores/', views.driver_monitoring_view, name='drivers_fleet'),

    path('repartidor/ruta-activa/', views.driver_mobile_view, name='driver_mobile'),
    path('repartidor/ruta-activa/<int:route_id>/', views.driver_mobile_view, name='driver_mobile_route'),
    path('driver-app/', views.driver_mobile_view, name='driver_app'),
    path('rutas/optimizar/', views.route_optimizer_view, name='route_optimizer'),
    path('entregas/nueva/', views.new_delivery_view, name='new_delivery'),
    path('puntos/', views.points_view, name='points'),
    path('clientes/', views.points_view, name='clients'),
    path('usuarios/', views.users_view, name='users'),
    path('audit/', views.audit_view, name='audit'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- ENDPOINTS API JSON ---
    path('api/auth/login', api_views.api_auth_login, name='api_auth_login'),
    path('api/auth/login/', api_views.api_auth_login),
    path('api/auth/provider-login', api_views.api_auth_provider_login, name='api_auth_provider_login'),
    path('api/auth/provider-login/', api_views.api_auth_provider_login),
    
    path('api/points', api_views.api_points_list_create, name='api_points'),
    path('api/points/', api_views.api_points_list_create),
    path('api/points/nearby', api_views.api_points_nearby, name='api_points_nearby'),
    path('api/points/nearby/', api_views.api_points_nearby),
    path('api/points/<int:point_id>', api_views.api_point_detail_update, name='api_point_detail'),
    path('api/points/<int:point_id>/', api_views.api_point_detail_update),
    path('api/points/<int:point_id>/history', api_views.api_point_history, name='api_point_history'),
    path('api/points/<int:point_id>/history/', api_views.api_point_history),
    
    path('api/routes/stops/<int:stop_id>/status', api_views.api_update_stop_status, name='api_update_stop_status'),
    path('api/routes/stops/<int:stop_id>/status/', api_views.api_update_stop_status),
    path('api/routes/distribute-random', api_views.api_distribute_random_routes, name='api_distribute_routes'),
    path('api/routes/distribute-random/', api_views.api_distribute_random_routes),
    
    # API Carga Masiva y Escáner QR / Barras
    path('api/deliveries/import-batch', api_views.api_bulk_import_deliveries, name='api_bulk_import_deliveries'),
    path('api/deliveries/import-batch/', api_views.api_bulk_import_deliveries),
    path('api/deliveries/download-template', api_views.api_download_template, name='api_download_template'),
    path('api/deliveries/download-template/', api_views.api_download_template),
    path('api/deliveries/scan-barcode-qr', api_views.api_scan_barcode_qr, name='api_scan_barcode_qr'),
    path('api/deliveries/scan-barcode-qr/', api_views.api_scan_barcode_qr),

    # API Novedades y Monitoreo en Vivo de Flota
    path('api/drivers/novelties', api_views.api_driver_novelties_list_create, name='api_driver_novelties'),
    path('api/drivers/novelties/', api_views.api_driver_novelties_list_create),
    path('api/drivers/novelties/<int:novelty_id>/resolve', api_views.api_resolve_driver_novelty, name='api_resolve_driver_novelty'),
    path('api/drivers/novelties/<int:novelty_id>/resolve/', api_views.api_resolve_driver_novelty),
    path('api/drivers/live-status', api_views.api_driver_live_status, name='api_driver_live_status'),
    path('api/drivers/live-status/', api_views.api_driver_live_status),

    path('api/users', api_views.api_users_list_create, name='api_users'),
    path('api/users/', api_views.api_users_list_create),
    path('api/audit', api_views.api_audit_list, name='api_audit'),
    path('api/audit/', api_views.api_audit_list),
]

