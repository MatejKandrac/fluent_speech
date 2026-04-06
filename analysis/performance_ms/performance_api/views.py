from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import PerformanceService


@api_view(['POST'])
def calculate_performance(request):

    body = request.data if request.data else {}
    service = PerformanceService()
    result = service.calculate_performance(body)

    response_status = status.HTTP_200_OK if result['success'] else status.HTTP_500_INTERNAL_SERVER_ERROR
    return Response(result, status=response_status)


@api_view(['GET'])
def health_check(request):
    return Response(
        {'status': 'healthy', 'service': 'analysis-performance'},
        status=status.HTTP_200_OK
    )
