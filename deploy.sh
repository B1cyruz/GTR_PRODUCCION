#!/bin/bash
# ==============================================================================
# Script de Despliegue Automatizado - GTR Logistics en DigitalOcean Droplet
# Compatible con Ubuntu 22.04 / 24.04 LTS
# ==============================================================================

set -e

echo "🚀 ========================================================="
echo "   Iniciando Despliegue de GTR (Gestión Logística y Rutas)   "
echo "=========================================================="

# 1. Actualizar repositorios del sistema
echo "📦 1. Actualizando paquetes del sistema..."
apt-get update && apt-get upgrade -y
apt-get install -y python3-pip python3-venv postgresql postgresql-contrib nginx git curl ufw

# 2. Configurar Firewall UFW
echo "🛡️  2. Configurando Firewall UFW..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# 3. Configuración de Base de Datos PostgreSQL
echo "🐘 3. Configurando PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

DB_NAME="gtr_db"
DB_USER="gtr_user"
DB_PASS="gtr_secure_password_2026"

sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# 4. Preparar Directorio de la Aplicación
APP_DIR="/var/www/gtr"
echo "📂 4. Configurando directorio de aplicación en $APP_DIR..."
mkdir -p $APP_DIR
cp -r . $APP_DIR/
cd $APP_DIR

# 5. Configurar Entorno Virtual Python
echo "🐍 5. Creando entorno virtual e instalando dependencias..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 6. Crear archivo .env de producción
echo "⚙️  6. Generando variables de entorno de producción..."
cat <<EOF > $APP_DIR/.env
PROJECT_NAME="GTR - Gestión Logística y Rutas"
ENVIRONMENT="production"
DEBUG=False
SECRET_KEY="$(openssl rand -hex 32)"
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_DB=$DB_NAME
DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
HOST=127.0.0.1
PORT=8000
WORKERS=4
DEFAULT_CITY="Cartagena"
DEFAULT_LAT=10.3997
DEFAULT_LNG=-75.5144
DEFAULT_ZOOM=13
EOF

# 7. Ejecutar migraciones, recolectar estáticos e inicializar datos de prueba
echo "🌱 7. Ejecutando migraciones e inicializando datos en PostgreSQL 16..."
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py collectstatic --noinput
./venv/bin/python manage.py seed_data

# 8. Configurar e Iniciar Servicio Systemd (Gunicorn WSGI)
echo "🔧 8. Configurando servicio Systemd para GTR con Gunicorn..."
cp gtr.service /etc/systemd/system/gtr.service
systemctl daemon-reload
systemctl enable gtr.service
systemctl restart gtr.service

# 9. Configurar Nginx Reverse Proxy
echo "🌐 9. Configurando Nginx Reverse Proxy..."
cat <<'EOF' > /etc/nginx/sites-available/gtr
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    # Static Files (WhiteNoise / Nginx alias)
    location /static/ {
        alias /var/www/gtr/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media Files (Fotografías de Fachada y Comprobantes de GPS)
    location /media/ {
        alias /var/www/gtr/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Django WSGI via Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/gtr /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "✅ ========================================================="
echo "   ¡Despliegue Completado Exitosamente!                     "
echo "   Accede a tu servidor en: http://TU_IP_DIGITALOCEAN/      "
echo "   Documentación API: http://TU_IP_DIGITALOCEAN/docs        "
echo "=========================================================="
