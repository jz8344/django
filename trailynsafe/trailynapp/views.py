"""
Vista simple para endpoint de status
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def status_check(request):
    """Endpoint de status para Railway"""
    return JsonResponse({
        'status': 'ok',
        'message': 'running'
    })
