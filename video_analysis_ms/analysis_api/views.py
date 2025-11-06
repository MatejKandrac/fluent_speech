"""
API views for video analysis endpoints.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from bson.errors import InvalidId

from .services import VideoProcessingService
from .db_connection import get_analysis_collection


@api_view(['POST'])
def analyze_video(request, video_id):
    """
    Analyze a video and extract pose landmarks.

    Args:
        video_id: The MongoDB ObjectId of the video to analyze

    Returns:
        JSON response with analysis results
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

    # Process the video
    service = VideoProcessingService()
    result = service.process_video(video_id)

    if result['success']:
        return Response(
            {
                'success': True,
                'message': 'Video analysis completed successfully',
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
        analysis_id: The MongoDB ObjectId of the analysis document

    Returns:
        JSON response with analysis data
    """
    # Validate analysis_id format
    try:
        obj_id = ObjectId(analysis_id)
    except InvalidId:
        return Response(
            {
                'success': False,
                'error': 'Invalid analysis ID format'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get analysis from MongoDB
    analysis_collection = get_analysis_collection()
    analysis_doc = analysis_collection.find_one({'_id': obj_id})

    if not analysis_doc:
        return Response(
            {
                'success': False,
                'error': 'Analysis not found'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # Convert ObjectId to string for JSON serialization
    analysis_doc['_id'] = str(analysis_doc['_id'])

    return Response(
        {
            'success': True,
            'analysis': analysis_doc
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def get_video_analyses(request, video_id):
    """
    Get all analyses for a specific video.

    Args:
        video_id: The MongoDB ObjectId of the video

    Returns:
        JSON response with list of analyses
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

    # Get all analyses for this video
    analysis_collection = get_analysis_collection()
    analyses = list(analysis_collection.find({'video_id': video_id}))

    # Convert ObjectIds to strings
    for analysis in analyses:
        analysis['_id'] = str(analysis['_id'])

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
        analysis_id: The MongoDB ObjectId of the analysis to delete

    Returns:
        JSON response with deletion status
    """
    # Validate analysis_id format
    try:
        obj_id = ObjectId(analysis_id)
    except InvalidId:
        return Response(
            {
                'success': False,
                'error': 'Invalid analysis ID format'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Delete the analysis
    analysis_collection = get_analysis_collection()
    result = analysis_collection.delete_one({'_id': obj_id})

    if result.deleted_count == 0:
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
