"""
Vista simple para endpoint de status
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def status_check(request):
    """Endpoint de status para Railway"""
    return Response({
        'status': 'ok',
        'message': 'running'
    })
