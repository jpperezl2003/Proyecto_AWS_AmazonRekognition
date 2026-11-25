#!/bin/bash
set -euo pipefail

echo "==================================="
echo " INICIANDO DESPLIEGUE ANIMAL VISION "
echo "==================================="

APP_DIR="/opt/animal-vision"
FRONTEND_DIR="/var/www/animal-vision"

cd "$APP_DIR"

# ===================================
# 1. ACTUALIZAR BACKEND
# ===================================

echo "Actualizando dependencias Python..."

sudo -u ubuntu .venv/bin/python -m pip install \
  --no-cache-dir \
  -r requirements.txt

# ===================================
# 2. COMPILAR FRONTEND
# ===================================

echo "Compilando React..."

cd "$APP_DIR/web"

sudo -u ubuntu npm ci
sudo -u ubuntu npm run build

# ===================================
# 3. PUBLICAR FRONTEND EN NGINX
# ===================================

echo "Publicando frontend..."

mkdir -p "$FRONTEND_DIR"

cp -a dist/. "$FRONTEND_DIR/"

# ===================================
# 4. ACTUALIZAR CONFIGURACION NGINX
# ===================================

echo "Actualizando configuracion Nginx..."

cat > /etc/nginx/sites-available/animal-vision <<'NGINX'
server {
    listen 80;
    server_name _;

    root /var/www/animal-vision;
    index index.html;

    client_max_body_size 5m;

    location = /predict {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 90s;
    }

    location = /feedback {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 90s;
    }

    location = /health {
        proxy_pass http://127.0.0.1:8000;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX

nginx -t

systemctl reload nginx

# ===================================
# 5. REINICIAR FASTAPI
# ===================================

echo "Reiniciando servicio FastAPI..."

systemctl restart animal-vision

# ===================================
# 6. VERIFICAR SALUD DEL BACKEND
# ===================================

echo "Verificando /health..."

for intento in $(seq 1 15); do

  if curl --fail --silent --show-error \
    http://127.0.0.1:8000/health; then

    echo ""

    # Verificar que Nginx dirige /feedback a FastAPI.
    # Una solicitud GET debe devolver 405,
    # ya que el endpoint solamente acepta POST.

    FEEDBACK_STATUS=$(curl --silent \
      --output /dev/null \
      --write-out "%{http_code}" \
      http://127.0.0.1/feedback)

    if [ "$FEEDBACK_STATUS" != "405" ]; then
      echo "ERROR: Proxy /feedback no funciona."
      echo "HTTP Status: $FEEDBACK_STATUS"
      exit 1
    fi

    echo "Endpoint /feedback disponible."

    echo "==================================="
    echo " DESPLIEGUE COMPLETADO CORRECTAMENTE "
    echo "==================================="

    exit 0
  fi

  echo "Intento $intento: esperando FastAPI..."
  sleep 2
done

echo "ERROR: FastAPI no responde."
exit 1
