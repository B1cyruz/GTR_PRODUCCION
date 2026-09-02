# GTR: Gestión Logística y Rutas Urbanas 🚚🗺️

Plataforma integral desarrollada en **Python (FastAPI)** con persistencia exclusiva en **PostgreSQL**, diseñada para la optimización de rutas de última milla, control de despachos y seguimiento de entregas en tiempo real.

---

## 🌟 Características Principales

1. **Dashboard Operativo en Vivo**:
   - KPIs de efectividad, entregas completadas, en tránsito e incidencias.
   - Mapa interactivo en tiempo real con geolocalización de repartidores y paquetes en Cartagena.
   - Panel de control de flota de repartidores (motos, furgones, camiones).
2. **Motor de Optimización de Rutas (Algoritmo TSP)**:
   - Algoritmo heurístico *Nearest Neighbor* con refinamiento *2-Opt*.
   - Integración con OSRM / OpenStreetMap para trazado y cálculo de distancias viales reales.
   - Cálculo automático de horas estimadas de llegada (ETA) y kilometraje.
3. **Módulo de Alta y Geocodificación de Envíos**:
   - Registro de paquetes con selector interactivo de coordenadas en mapa.
   - Clasificación por categorías de carga (frío, paquetes estándar, voluminoso).
4. **App Móvil para Repartidores**:
   - Interfaz web móvil responsive para conductores en calle.
   - Checklist interactivo de paradas con estados (*En camino*, *Entregado*, *Incidencia*).
   - Modal de confirmación de entrega con captura de cédula/documento y notas.
5. **Listo para Producción en DigitalOcean**:
   - Configuración lista para PostgreSQL 16.
   - Servidor WSGI/ASGI con Gunicorn y Uvicorn Workers.
   - Proxy reverso con Nginx, gzip y headers de seguridad.
   - Scripts de despliegue automático `deploy.sh` y `docker-compose.yml`.

---

## 🚀 Inicio Rápido Local

### 1. Requisitos Previos
- Python 3.10+
- PostgreSQL 14+ instalado y corriendo

### 2. Configuración
```bash
# Crear entorno virtual
python -m venv venv
# Activar entorno virtual (Windows)
.\venv\Scripts\activate
# Activar entorno virtual (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Ajusta tus credenciales de PostgreSQL en .env
```

### 3. Poblar Base de Datos de Prueba
```bash
python seed_data.py
```

### 4. Iniciar Servidor de Desarrollo
```bash
python app/main.py
```
Abre tu navegador en: `http://localhost:8000`  
Documentación Swagger API: `http://localhost:8000/docs`

---

## ☁️ Despliegue en DigitalOcean

Consulta la guía completa en [DEPLOY_DIGITALOCEAN.md](DEPLOY_DIGITALOCEAN.md).

---

## 📁 Estructura del Proyecto

```
GTR/
├── app/
│   ├── main.py                  # Entrypoint de FastAPI
│   ├── config.py                # Variables de entorno y configuración
│   ├── database.py              # Motor SQLAlchemy y sesiones PostgreSQL
│   ├── models/                  # Modelos relacionales (User, Delivery, Route, Driver)
│   ├── schemas/                 # Esquemas de validación Pydantic
│   ├── services/                # Algoritmo de optimización y ruteo
│   ├── routers/                 # Enrutadores API REST y Web
│   ├── static/                  # CSS personalizado, JS y assets
│   └── templates/               # Plantillas Jinja2 (Dashboard, Optimizador, Formulario, Móvil)
├── seed_data.py                 # Datos de prueba de Cartagena
├── requirements.txt             # Dependencias de Python
├── Dockerfile                   # Contenedor de producción
├── docker-compose.yml           # Orquestación PostgreSQL + FastAPI + Nginx
├── nginx.conf                   # Configuración optimizada de Nginx
├── gtr.service                  # Servicio Systemd para Linux
├── deploy.sh                    # Script de despliegue automatizado
├── DEPLOY_DIGITALOCEAN.md       # Guía de producción
└── README.md                    # Documentación
```
