#!/bin/bash

# Script de inicio para Django en Railway

echo "🚀 Iniciando TrailynSafe Django Backend..."

# Navegar al directorio del proyecto
cd trailynsafe

# Ejecutar migraciones
echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

# Colectar archivos estáticos (si es necesario)
echo "📁 Colectando archivos estáticos..."
python manage.py collectstatic --noinput --clear || true

# Iniciar Gunicorn
echo "🌐 Iniciando Gunicorn en puerto $PORT..."
gunicorn trailynsafe.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300 \
  --graceful-timeout 300 \
  --keep-alive 5 \
  --worker-class gthread \
  --access-logfile - \
  --error-logfile - \
  --log-level info
