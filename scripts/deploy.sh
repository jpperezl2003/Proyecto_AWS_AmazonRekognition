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
# 4. REINICIAR FASTAPI
# ===================================

echo "Reiniciando servicio FastAPI..."

systemctl restart animal-vision

# ===================================
# 5. VERIFICAR SALUD DEL BACKEND
# ===================================

echo "Verificando /health..."

for intento in $(seq 1 15); do

  if curl --fail --silent --show-error \
    http://127.0.0.1:8000/health; then

    echo ""
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
