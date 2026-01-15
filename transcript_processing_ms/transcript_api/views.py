from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import TranscriptProcessingService


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'healthy', 'service': 'transcript_processing'})


@api_view(['POST'])
def process_transcript(request, recording_id):
    try:
        service = TranscriptProcessingService()
        result = service.process_transcript(recording_id)

        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
