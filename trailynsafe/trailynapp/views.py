"""
Vista simple para endpoint de status
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection


@csrf_exempt
def status_check(request):
    """Endpoint de status para Railway"""
    return JsonResponse({
        'status': 'ok',
        'message': 'running'
    })


@csrf_exempt
def db_test(request):
    """Endpoint para probar conexión a base de datos"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
        
        return JsonResponse({
            'status': 'ok',
            'message': 'Database connected',
            'database': connection.settings_dict['NAME'],
            'engine': connection.settings_dict['ENGINE'],
            'host': connection.settings_dict['HOST'],
            'version': db_version
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
