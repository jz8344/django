# 🚀 SERVIDOR DJANGO K-MEANS - RAILWAY

## Variables de entorno necesarias

```bash
# Django Settings
SECRET_KEY=tu_secret_key_super_secreta_aqui
DEBUG=False
ALLOWED_HOSTS=*.railway.app,localhost,127.0.0.1

# Google Maps API
GOOGLE_MAPS_API_KEY=tu_google_maps_api_key_aqui

# Laravel Integration
LARAVEL_WEBHOOK_URL=https://tu-backend-laravel.railway.app/api/webhook/ruta-generada
WEBHOOK_SECRET=token_secreto_compartido_con_laravel

# CORS
CORS_ALLOWED_ORIGINS=https://tu-frontend.railway.app,http://localhost:5173
```

## 📦 Instalación local

```bash
cd backend_django
python -m venv env
.\env\Scripts\activate  # Windows
pip install -r requirements.txt
cd trailynsafe
python manage.py migrate
python manage.py runserver
```

## 🧪 Probar endpoint

```bash
curl -X POST http://localhost:8000/api/generar-ruta \
  -H "Content-Type: application/json" \
  -d '{
    "viaje_id": 1,
    "capacidad_unidad": 30,
    "destino": {
      "nombre": "Escuela",
      "latitud": 20.676667,
      "longitud": -103.347222
    },
    "puntos_recogida": [
      {
        "confirmacion_id": 1,
        "hijo_id": 1,
        "nombre": "Juan",
        "direccion": "Calle 1",
        "latitud": 20.680,
        "longitud": -103.350
      }
    ],
    "hora_salida": "07:00:00"
  }'
```

## 🚂 Despliegue en Railway

1. Crear nuevo proyecto en Railway
2. Conectar con repositorio GitHub
3. Seleccionar carpeta `backend_django`
4. Agregar variables de entorno
5. Railway detectará `railway.json` automáticamente
6. Deploy!

La URL será: `https://tu-proyecto.railway.app`
