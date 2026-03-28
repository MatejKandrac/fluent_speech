from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

import requests
from django.conf import settings


# Maps each analysis flag to (service_key, url_builder, http_method)
def _build_url(base: str, path: str) -> str:
    return f"{base}/api/v1/{path}"


ANALYSIS_REGISTRY = {
    'arm_movement': lambda rid: (
        'arm_movement',
        _build_url(settings.ANALYSIS_SERVICES['arm_movement'], f'analyze/arm-movements/{rid}/'),
    ),
    'eye_contact': lambda rid: (
        'eye_contact',
        _build_url(settings.ANALYSIS_SERVICES['eye_contact'], f'eye-contact/{rid}/analyze/'),
    ),
    'pitch': lambda rid: (
        'pitch',
        _build_url(settings.ANALYSIS_SERVICES['pitch'], f'pitch/{rid}/analyze/'),
    ),
    'volume': lambda rid: (
        'volume',
        _build_url(settings.ANALYSIS_SERVICES['volume'], f'volume/{rid}/analyze/'),
    ),
    'hip': lambda rid: (
        'hip',
        _build_url(settings.ANALYSIS_SERVICES['hip'], f'hip/{rid}/analyze/'),
    ),
    'filler_words': lambda rid: (
        'filler_words',
        _build_url(settings.ANALYSIS_SERVICES['filler_words'], f'filler-words/{rid}/analyze/'),
    ),
}


def _call_service(name: str, url: str) -> tuple[str, Dict[str, Any]]:
    try:
        response = requests.post(url, timeout=settings.ANALYSIS_TIMEOUT)
        response.raise_for_status()
        return name, response.json()
    except requests.exceptions.Timeout:
        return name, {'success': False, 'error': f'Service timed out after {settings.ANALYSIS_TIMEOUT}s'}
    except requests.exceptions.ConnectionError:
        return name, {'success': False, 'error': 'Service unavailable'}
    except Exception as e:
        return name, {'success': False, 'error': str(e)}


class AnalysisOrchestratorService:

    def run_analysis(self, recording_id: int, flags: Dict[str, bool]) -> Dict[str, Any]:
        # Build list of (name, url) for enabled analyses
        tasks = []
        for flag_name, builder in ANALYSIS_REGISTRY.items():
            if flags.get(flag_name, False):
                name, url = builder(recording_id)
                tasks.append((name, url))

        if not tasks:
            return {
                'success': False,
                'error': 'No analyses selected. Set at least one flag to true.',
            }

        results = {}
        completed = []
        failed = []

        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {executor.submit(_call_service, name, url): name for name, url in tasks}
            for future in as_completed(futures):
                name, result = future.result()
                results[name] = result
                if result.get('success'):
                    completed.append(name)
                else:
                    failed.append(name)

        return {
            'success': len(failed) == 0,
            'recording_id': recording_id,
            'completed_analyses': completed,
            'failed_analyses': failed,
            'results': results,
        }