"""
API views for hand movement analysis endpoints.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from bson.errors import InvalidId

from .services import HandMovementAnalysisService


@api_view(['POST'])
def analyze_hand_movements(request, video_id):
    """
    Analyze hand movements from video analysis data.

    Args:
        video_id: The MongoDB ObjectId of the video

    Returns:
        JSON response with hand movement analysis results
    """
    # Validate video_id format
    try:
        ObjectId(video_id)
    except InvalidId:
        return Response(
            {
                'success': False,
                'error': 'Invalid video ID format'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Analyze hand movements
    service = HandMovementAnalysisService()
    result = service.analyze_hand_movements(video_id)

    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            result,
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.

    Returns:
        JSON response indicating service health
    """
    return Response(
        {
            'status': 'healthy',
            'service': 'hand-movement-analysis-service'
        },
        status=status.HTTP_200_OK
    )
