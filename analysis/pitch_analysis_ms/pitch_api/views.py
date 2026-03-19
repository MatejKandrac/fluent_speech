from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import PitchAnalysisService


@api_view(['POST'])
def analyze_pitch(request, recording_id):
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

    service = PitchAnalysisService()
    result = service.analyze_pitch(recording_id)

    if result['success']:
        return Response(
            {
                'success': True,
                'recording_id': result['recording_id'],
                'pitch_frames': result['pitch_frames'],
                'voiced_frames': result['voiced_frames'],
                'pitch_mean': result['pitch_mean'],
                'pitch_min': result['pitch_min'],
                'pitch_max': result['pitch_max'],
                'pitch_std': result['pitch_std'],
                'monotonous_segments': result['monotonous_segments'],
                'monotonous_segments_count': result['monotonous_segments_count']
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
            'service': 'pitch-analysis-ms'
        },
        status=status.HTTP_200_OK
    )
