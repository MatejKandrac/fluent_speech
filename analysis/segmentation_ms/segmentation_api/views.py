from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import SegmentationService


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'healthy', 'service': 'segmentation'})


@api_view(['POST'])
def segment(request):
    try:
        series = request.data.get('series')
        if not series:
            return Response(
                {'success': False, 'error': 'Missing required field: series'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        methods = request.data.get('methods', ['mean', 'std'])
        sensitivity = float(request.data.get('sensitivity', -1))
        label = request.data.get('label')

        service = SegmentationService()
        if sensitivity < 0:
            sensitivity = service.config['default_sensitivity']

        result = service.segment(series, methods, sensitivity, label=label)

        http_status = status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)

    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
