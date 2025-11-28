"""
Vista simple para endpoint de status
"""
from django.http import JsonResponse


def status_check(request):
    """Endpoint de status para Railway"""
    return JsonResponse({
        'status': 'ok',
        'message': 'running'
    })
