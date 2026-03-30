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
                'volume_mean_rms': result['volume_mean_rms'],
                'volume_min_rms': result['volume_min_rms'],
                'volume_max_rms': result['volume_max_rms'],
                'volume_std_rms': result['volume_std_rms'],
                'dbfs_mean': result['dbfs_mean'],
                'dbfs_min': result['dbfs_min'],
                'dbfs_max': result['dbfs_max'],
                'too_soft_segments': result['too_soft_segments'],
                'too_soft_count': result['too_soft_count'],
                'too_loud_segments': result['too_loud_segments'],
                'too_loud_count': result['too_loud_count'],
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
            'service': 'volume-analysis-ms'
        },
        status=status.HTTP_200_OK
    )
