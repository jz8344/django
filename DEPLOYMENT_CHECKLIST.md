# 🚀 Checklist de Deployment Django en Railway

## ❌ Error Actual
```
404 Not Found - Application not found
```

Laravel está llamando a: `https://backend-django-production-6d57.up.railway.app/api/generar-ruta`
Pero Django responde con 404.

## 🔍 Diagnóstico

### 1. Verificar que Django esté corriendo en Railway

```bash
# Accede a los logs de Railway para el servicio Django
# Deberías ver:
# - "🚀 Iniciando TrailynSafe Django Backend..."
# - "📦 Ejecutando migraciones..."
# - "🌐 Iniciando Gunicorn en puerto..."
# - "[INFO] Listening at: http://0.0.0.0:8080"
```

### 2. Verificar Variables de Entorno en Railway

Asegúrate de que estas variables estén configuradas:

```bash
DJANGO_SECRET_KEY=s+x0)$fr+zu*!ziy67rgxmg(ur!o20co$5lyd@2+m4m*2gz!c$
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=*
DATABASE_URL=postgresql://postgres:password@host:port/database
LARAVEL_API_URL=https://web-production-86356.up.railway.app
LARAVEL_WEBHOOK_SECRET=MKB0F4FoRIB-GAzR0LOmxU7VPKBCNxKuysJ5-QHKJ7s
GOOGLE_MAPS_API_KEY=AIzaSyCz4QsA_tgZv3Hw3O-RZLVoKefkXX7ZNoA
PORT=8080
```

### 3. Verificar que el servicio esté PUBLIC

En Railway:
1. Ve al servicio Django
2. Settings → Networking
3. Asegúrate de que tenga un **dominio público** asignado
4. El dominio debe ser: `backend-django-production-6d57.up.railway.app`

### 4. Probar el Health Check

```bash
curl https://backend-django-production-6d57.up.railway.app/health

# Debe responder:
# {"status":"ok","service":"TrailynSafe k-Means","version":"1.0.0"}
```

### 5. Probar el Endpoint de Generación de Ruta

```bash
curl -X POST https://backend-django-production-6d57.up.railway.app/api/generar-ruta \
  -H "Content-Type: application/json" \
  -d '{
    "viaje_id": 3,
    "puntos": [
      {
        "confirmacion_id": 1,
        "hijo_id": 1,
        "hijo_nombre": "Test",
        "latitud": 20.6736,
        "longitud": -103.3444,
        "direccion": "Test",
        "referencia": "Test"
      }
    ],
    "destino": {
      "escuela_id": 2,
      "nombre": "COBAEJ 21",
      "latitud": 20.6597,
      "longitud": -103.3496,
      "direccion": "Test"
    },
    "hora_salida": "07:00:00",
    "capacidad": 50,
    "webhook_url": "https://web-production-86356.up.railway.app/api/webhook/ruta-generada"
  }'
```

## 🔧 Soluciones Posibles

### Solución 1: Redeploy Django en Railway

1. Ve al dashboard de Railway
2. Selecciona el servicio Django
3. Click en "Deploy" → "Redeploy"
4. Espera a que termine el deployment
5. Verifica los logs

### Solución 2: Verificar el Procfile

El `Procfile` debe tener:
```
web: cd trailynsafe && python manage.py migrate --noinput && gunicorn trailynsafe.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
```

### Solución 3: Verificar settings.py

En `trailynsafe/trailynsafe/settings.py`:

```python
import os
from pathlib import Path

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE'),
        'USER': os.environ.get('PGUSER'),
        'PASSWORD': os.environ.get('PGPASSWORD'),
        'HOST': os.environ.get('PGHOST'),
        'PORT': os.environ.get('PGPORT', '5432'),
    }
}
```

### Solución 4: Verificar que gunicorn esté instalado

En `requirements.txt` debe estar:
```
gunicorn==21.2.0
```

## 🧪 Test Rápido desde PowerShell

```powershell
# Test 1: Health Check
Invoke-WebRequest -Uri "https://backend-django-production-6d57.up.railway.app/health" -Method Get

# Test 2: Endpoint principal
$body = @{
    viaje_id = 3
    puntos = @(
        @{
            confirmacion_id = 1
            hijo_id = 1
            hijo_nombre = "Test"
            latitud = 20.6736
            longitud = -103.3444
            direccion = "Test"
            referencia = "Test"
        }
    )
    destino = @{
        escuela_id = 2
        nombre = "COBAEJ 21"
        latitud = 20.6597
        longitud = -103.3496
        direccion = "Test"
    }
    hora_salida = "07:00:00"
    capacidad = 50
    webhook_url = "https://web-production-86356.up.railway.app/api/webhook/ruta-generada"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://backend-django-production-6d57.up.railway.app/api/generar-ruta" -Method Post -Body $body -ContentType "application/json"
```

## 📋 Checklist Final

- [ ] Django está corriendo en Railway (logs visibles)
- [ ] Variables de entorno configuradas
- [ ] Dominio público asignado y accesible
- [ ] Health check responde 200 OK
- [ ] Endpoint `/api/generar-ruta` responde (no 404)
- [ ] Backend Laravel tiene `DJANGO_API_URL` configurado correctamente
- [ ] Logs de Django muestran requests entrantes

## 🆘 Si Sigue Sin Funcionar

1. **Revisa los logs de Railway** para ver el error exacto
2. **Verifica la URL del dominio** - puede que Railway haya cambiado el dominio
3. **Actualiza la variable `DJANGO_API_URL` en el backend Laravel** si el dominio cambió
4. **Considera usar el servicio interno de Railway** si ambos servicios están en el mismo proyecto

### URL Interna de Railway (más rápida)

Si ambos servicios están en el mismo proyecto de Railway, puedes usar:
```
DJANGO_API_URL=http://backend-django-production-6d57.railway.internal:8080
```

Esto evita hacer requests por internet público y es más rápido.
