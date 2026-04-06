from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from .services import ProcessingOrchestratorService


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_video(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'success': False, 'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    service = ProcessingOrchestratorService()
    result = service.upload_video(file)

    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_processing_status(request):
    recording_id = request.GET.get('recording-id')
    if not recording_id:
        return Response({'success': False, 'error': 'recording-id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        recording_id = int(recording_id)
    except ValueError:
        return Response({'success': False, 'error': 'recording-id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    service = ProcessingOrchestratorService()
    result = service.get_processing_status(recording_id)

    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def health_check(request):
    return Response(
        {'status': 'healthy', 'service': 'processing-orchestrator'},
        status=status.HTTP_200_OK
    )
