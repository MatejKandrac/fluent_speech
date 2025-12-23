from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import AudioAnalysisService


@api_view(['POST'])
def analyze_audio(request, recording_id):
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

    service = AudioAnalysisService()
    result = service.analyze_audio(recording_id)

    if result['success']:
        return Response(
            {
                'success': True,
                'recording_id': result['recording_id'],
                'duration': result['duration'],
                'sample_rate': result['sample_rate'],
                'samples': result['samples'],
                'audio_features_saved': result.get('audio_features_saved', 0)
            },
            status=status.HTTP_201_CREATED
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
            'service': 'audio-analysis-ms'
        },
        status=status.HTTP_200_OK
    )
