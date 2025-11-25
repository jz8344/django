#!/usr/bin/env python
"""
Script de diagnóstico para verificar la configuración de Django antes del deployment
"""
import os
import sys

print("=" * 80)
print("DIAGNÓSTICO DE CONFIGURACIÓN DJANGO")
print("=" * 80)

# 1. Variables de entorno críticas
print("\n1. Variables de Entorno:")
print(f"   DJANGO_SECRET_KEY: {'✓ Configurada' if os.getenv('DJANGO_SECRET_KEY') else '✗ NO configurada'}")
print(f"   DJANGO_DEBUG: {os.getenv('DJANGO_DEBUG', 'False')}")
print(f"   DJANGO_ALLOWED_HOSTS: {os.getenv('DJANGO_ALLOWED_HOSTS', '*')}")
print(f"   DATABASE_URL: {'✓ Configurada' if os.getenv('DATABASE_URL') else '✗ NO configurada'}")
print(f"   PORT: {os.getenv('PORT', '8080')}")
print(f"   GOOGLE_MAPS_API_KEY: {'✓ Configurada' if os.getenv('GOOGLE_MAPS_API_KEY') else '✗ NO configurada'}")
print(f"   LARAVEL_API_URL: {os.getenv('LARAVEL_API_URL', 'NO configurada')}")

# 2. Verificar DATABASE_URL
print("\n2. Análisis de DATABASE_URL:")
db_url = os.getenv('DATABASE_URL')
if db_url:
    print(f"   Valor: {db_url[:50]}...")  # Solo los primeros 50 caracteres
    
    # Verificar si tiene el formato correcto
    if db_url.startswith('postgresql://'):
        print("   ✓ Formato PostgreSQL correcto")
        
        # Intentar parsear
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            print(f"   Host: {parsed.hostname}")
            print(f"   Port: {parsed.port}")
            print(f"   Database: {parsed.path[1:]}")  # Remover el /
            print(f"   User: {parsed.username}")
            print(f"   Password: {'***' if parsed.password else 'NO'}")
        except Exception as e:
            print(f"   ✗ Error al parsear: {e}")
    else:
        print(f"   ✗ Formato incorrecto: {db_url[:30]}...")
else:
    print("   ✗ DATABASE_URL no está configurada")
    print("   Se usará SQLite por defecto (db.sqlite3)")

# 3. Verificar dependencias
print("\n3. Verificando Dependencias Críticas:")
try:
    import django
    print(f"   ✓ Django {django.VERSION} instalado")
except ImportError:
    print("   ✗ Django NO instalado")
    sys.exit(1)

try:
    import rest_framework
    print("   ✓ Django REST Framework instalado")
except ImportError:
    print("   ✗ Django REST Framework NO instalado")

try:
    import corsheaders
    print("   ✓ django-cors-headers instalado")
except ImportError:
    print("   ✗ django-cors-headers NO instalado")

try:
    import sklearn
    print("   ✓ scikit-learn instalado")
except ImportError:
    print("   ✗ scikit-learn NO instalado")

try:
    import psycopg2
    print("   ✓ psycopg2 instalado")
except ImportError:
    print("   ✗ psycopg2 NO instalado (necesario para PostgreSQL)")

try:
    import dj_database_url
    print("   ✓ dj-database-url instalado")
except ImportError:
    print("   ✗ dj-database-url NO instalado")

try:
    import gunicorn
    print("   ✓ gunicorn instalado")
except ImportError:
    print("   ✗ gunicorn NO instalado")

# 4. Verificar settings.py
print("\n4. Verificando settings.py:")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trailynsafe.settings')
    import django
    django.setup()
    from django.conf import settings
    print("   ✓ settings.py carga correctamente")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"   DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
except Exception as e:
    print(f"   ✗ Error al cargar settings.py: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 80)
