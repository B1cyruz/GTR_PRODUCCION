# 🚀 Guía de Despliegue en DigitalOcean - GTR Logistics

Esta guía detalla paso a paso cómo desplegar la plataforma **GTR (Gestión Logística y Rutas)** en un Droplet de **DigitalOcean** bajo el stack estándar oficial:
- **Lenguaje Backend**: Python 3.12
- **Framework Web**: Django 5.2
- **Base de Datos**: PostgreSQL 16
- **ORM**: Django ORM
- **Servidor de Aplicación**: Gunicorn WSGI (`gtr_project.wsgi:application`)
- **Servidor Web / Proxy**: Nginx
- **Archivos Estáticos**: WhiteNoise
- **Sistema Operativo**: Ubuntu 24.04 LTS
- **Entorno Virtual**: Python `venv`
- **Configuración**: `.env`
- **Autenticación**: Django Auth (RBAC: `ROOT`, `COORDINADOR`, `REPARTIDOR`)
- **Infraestructura**: DigitalOcean Droplet VPS

---

## Opción A: Despliegue Automatizado con Script (Recomendado)

### 1. Crear el Droplet en DigitalOcean
1. Inicia sesión en [DigitalOcean](https://cloud.digitalocean.com/).
2. Haz clic en **Create** > **Droplets**.
3. Selecciona:
   - **Distribución**: Ubuntu 24.04 LTS (x64).
   - **Plan**: Basic (Regular con 1 GB o 2 GB RAM / 1 vCPU es ideal).
   - **Data Center Region**: Más cercana a tus usuarios (ej. Miami, New York).
   - **Autenticación**: Llave SSH (recomendado) o contraseña segura.
4. Haz clic en **Create Droplet** y copia la dirección **IP pública** asignada.

### 2. Subir el Proyecto y Ejecutar el Despliegue
Conéctate por SSH a tu Droplet desde tu terminal:

```bash
ssh root@TU_IP_DEL_DROPLET
```

Clona o transfiere tu carpeta del proyecto al servidor y ejecuta:

```bash
cd /root/GTR
chmod +x deploy.sh
./deploy.sh
```

El script se encargará automáticamente de:
1. Actualizar el sistema e instalar Python 3.12, PostgreSQL 16 y Nginx.
2. Crear la base de datos `gtr_db` y el usuario `gtr_user`.
3. Crear el entorno virtual `venv` e instalar `requirements.txt`.
4. Ejecutar migraciones (`python manage.py migrate`).
5. Recolectar archivos estáticos (`python manage.py collectstatic`).
6. Poblar datos iniciales y usuarios de prueba con contraseñas seguras (`python manage.py seed_data`).
7. Configurar e iniciar el servicio systemd `gtr.service` con Gunicorn WSGI.
8. Configurar el proxy reverso Nginx con enrutamiento de `/static/` y `/media/` (fotos de fachada y comprobantes).

---

## Opción B: Despliegue Manual Paso a Paso

```bash
# 1. Instalar paquetes de sistema
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv postgresql postgresql-contrib nginx git curl ufw

# 2. Configurar base de datos PostgreSQL
sudo -u postgres psql -c "CREATE USER gtr_user WITH PASSWORD 'tu_password_seguro';"
sudo -u postgres psql -c "CREATE DATABASE gtr_db OWNER gtr_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gtr_db TO gtr_user;"

# 3. Preparar código y entorno virtual
mkdir -p /var/www/gtr
cp -r . /var/www/gtr/
cd /var/www/gtr
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Crear archivo .env
cat <<EOF > /var/www/gtr/.env
SECRET_KEY=tu_secret_key_django
DEBUG=False
POSTGRES_DB=gtr_db
POSTGRES_USER=gtr_user
POSTGRES_PASSWORD=tu_password_seguro
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
ALLOWED_HOSTS=*
DEFAULT_CITY=Cartagena
DEFAULT_LAT=10.3997
DEFAULT_LNG=-75.5144
DEFAULT_ZOOM=13
EOF

# 5. Ejecutar migraciones y semilla
./venv/bin/python manage.py migrate
./venv/bin/python manage.py collectstatic --noinput
./venv/bin/python manage.py seed_data

# 6. Activar servicio Gunicorn
sudo cp gtr.service /etc/systemd/system/gtr.service
sudo systemctl daemon-reload
sudo systemctl enable gtr.service
sudo systemctl start gtr.service

# 7. Configurar Nginx
sudo cp nginx.conf /etc/nginx/sites-available/gtr
sudo ln -sf /etc/nginx/sites-available/gtr /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## Configuración de Dominio y Certificado SSL HTTPS Gratis (Let's Encrypt)

Si tienes un dominio apuntando a la IP de tu Droplet (ej. `gtr.tudominio.com`):

```bash
# Instalar Certbot
apt-get install -y certbot python3-certbot-nginx

# Obtener e instalar certificado SSL automáticamente
certbot --nginx -d gtr.tudominio.com
```

---

## Comandos Útiles de Mantenimiento

- **Ver estado del servicio backend (Gunicorn)**:
  ```bash
  systemctl status gtr.service
  ```
- **Ver logs en tiempo real**:
  ```bash
  journalctl -u gtr.service -f
  ```
- **Reiniciar servicio tras cambios de código**:
  ```bash
  systemctl restart gtr.service
  ```
- **Consola de PostgreSQL**:
  ```bash
  sudo -u postgres psql -d gtr_db
  ```
- **Ejecutar tests unitarios en el servidor**:
  ```bash
  ./venv/bin/python manage.py test core
  ```
- **Crear superusuario Django manual**:
  ```bash
  ./venv/bin/python manage.py createsuperuser
  ```
