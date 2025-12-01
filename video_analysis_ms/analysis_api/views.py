"""
API views for video analysis endpoints.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import VideoProcessingService
from .db_connection import (
    get_analysis_by_id,
    get_analyses_by_recording_id,
    delete_analysis_by_id
)


@api_view(['POST'])
def analyze_video(request, video_id):
    """
    Analyze a video and extract pose landmarks.
    """
    # Validate video_id format
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


@api_view(['GET'])
def get_analysis(request, analysis_id):
    """
    Retrieve analysis results by ID.

    Args:
        analysis_id: The ID of the analysis record

    Returns:
        JSON response with analysis data
    """
    # Validate analysis_id format
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

    # Get analysis from PostgreSQL
    analysis = get_analysis_by_id(analysis_id)

    if not analysis:
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
            'analysis': analysis
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def get_video_analyses(request, video_id):
    """
    Get all analyses for a specific video.

    Args:
        video_id: The ID of the video recording

    Returns:
        JSON response with list of analyses
    """
    # Validate video_id format
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

    # Get all analyses for this video
    analyses = get_analyses_by_recording_id(video_id)

    # Convert datetime objects to ISO format strings
    for analysis in analyses:
        if 'created_at' in analysis:
            analysis['created_at'] = analysis['created_at'].isoformat()

    return Response(
        {
            'success': True,
            'count': len(analyses),
            'analyses': analyses
        },
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
def delete_analysis(request, analysis_id):
    """
    Delete an analysis by ID.

    Args:
        analysis_id: The ID of the analysis to delete

    Returns:
        JSON response with deletion status
    """
    # Validate analysis_id format
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

    # Delete the analysis
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
    """
    Health check endpoint.

    Returns:
        JSON response indicating service health
    """
    return Response(
        {
            'status': 'healthy',
            'service': 'video-analysis-service'
        },
        status=status.HTTP_200_OK
    )
