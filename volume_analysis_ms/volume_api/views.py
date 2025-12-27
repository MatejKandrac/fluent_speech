from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import VolumeAnalysisService


@api_view(['POST'])
def analyze_volume(request, recording_id):
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

    service = VolumeAnalysisService()
    result = service.analyze_volume(recording_id)

    if result['success']:
        return Response(
            {
                'success': True,
                'recording_id': result['recording_id'],
                'volume_frames': result['volume_frames'],
                'volume_mean': result['volume_mean'],
                'volume_min': result['volume_min'],
                'volume_max': result['volume_max'],
                'volume_std': result['volume_std']
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
            'service': 'volume-analysis-ms'
        },
        status=status.HTTP_200_OK
    )
