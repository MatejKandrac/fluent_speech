from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import ArmMovementAnalysisService


@api_view(['POST'])
def analyze_arm_movements(request, recording_id):
    try:
        recording_id = int(recording_id)
    except (ValueError, TypeError):
        return Response(
            {
                'success': False,
                'error': 'Invalid recording ID format - must be an integer'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    service = ArmMovementAnalysisService()
    result = service.analyze_arm_movements(recording_id)

    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            result,
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def health_check(request):
    return Response(
        {
            'status': 'healthy',
            'service': 'arm-movement-analysis-service'
        },
        status=status.HTTP_200_OK
    )
