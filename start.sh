#!/bin/bash

echo "🚀 Iniciando TrailynSafe Django Backend..."

cd trailynsafe || exit 1

echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📁 Colectando archivos estáticos..."
python manage.py collectstatic --noinput --clear || true

echo "🌐 Iniciando Gunicorn en puerto $PORT..."
exec gunicorn trailynsafe.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
