from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import HipAnalysisService


@api_view(['POST'])
def analyze_hip_movement(request, recording_id):
    try:
        recording_id = int(recording_id)
    except (ValueError, TypeError):
        return Response(
            {
                'success': False,
                'error': 'Invalid recording_id format - must be an integer'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    service = HipAnalysisService()
    result = service.analyze_hip_movement(recording_id)

    if result['success']:
        return Response(
            {
                'success': True,
                'recording_id': result['recording_id'],
                'statistics': result['statistics'],
                'swaying_segments': result['swaying_segments'],
                'swaying_segments_count': result['swaying_segments_count'],
                'segmentation': result.get('segmentation'),
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    return Response(
        {
            'status': 'healthy',
            'service': 'hip-analysis-ms'
        },
        status=status.HTTP_200_OK
    )
