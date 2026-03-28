from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import AnalysisOrchestratorService, ANALYSIS_REGISTRY


@api_view(['POST'])
def run_analysis(request, recording_id):
    try:
        recording_id = int(recording_id)
    except (ValueError, TypeError):
        return Response(
            {'success': False, 'error': 'Invalid recording_id — must be an integer'},
            status=status.HTTP_400_BAD_REQUEST
        )

    body = request.data if request.data else {}

    # If no flags provided at all, default to running everything
    known_flags = set(ANALYSIS_REGISTRY.keys())
    provided_flags = {k: v for k, v in body.items() if k in known_flags}
    if not provided_flags:
        flags = {k: True for k in known_flags}
    else:
        flags = {k: bool(provided_flags.get(k, False)) for k in known_flags}

    service = AnalysisOrchestratorService()
    result = service.run_analysis(recording_id, flags)

    response_status = status.HTTP_200_OK if result['success'] else status.HTTP_207_MULTI_STATUS
    return Response(result, status=response_status)


@api_view(['GET'])
def health_check(request):
    return Response(
        {'status': 'healthy', 'service': 'analysis-orchestrator'},
        status=status.HTTP_200_OK
    )
