from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import VideoProcessingService
from .db_connection import (
    delete_analysis_by_id
)


@api_view(['POST'])
def analyze_video(request, video_id):
    try:
        video_id = int(video_id)
    except (ValueError, TypeError):
        return Response(
            {
                'success': False,
                'error': 'Invalid video ID format - must be an integer'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    service = VideoProcessingService()
    result = service.process_video(video_id)

    if result['success']:
        return Response(
            {
                'analysis_id': result['analysis_id'],
                'frames_processed': result['frames_processed'],
                'total_frames': result['total_frames'],
                'duration': result['duration'],
                'max_x': result.get('max_x'),
                'max_y': result.get('max_y')
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


@api_view(['DELETE'])
def delete_analysis(request, analysis_id):
    try:
        analysis_id = int(analysis_id)
    except (ValueError, TypeError):
        return Response(
            {
                'success': False,
                'error': 'Invalid analysis ID format - must be an integer'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    deleted = delete_analysis_by_id(analysis_id)

    if not deleted:
        return Response(
            {
                'success': False,
                'error': 'Analysis not found'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        {
            'success': True,
            'message': 'Analysis deleted successfully'
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def health_check(request):
    return Response(
        {
            'status': 'healthy',
            'service': 'video-analysis-service'
        },
        status=status.HTTP_200_OK
    )
