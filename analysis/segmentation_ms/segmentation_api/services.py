import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ruptures as rpt
from django.conf import settings


SUPPORTED_METHODS = {
    'mean': 'l2',      # detects shifts in mean (least-squares cost)
    'std':  'normal',  # detects shifts in variance/std (Gaussian log-likelihood cost)
}


class SegmentationService:

    def __init__(self):
        self.config = settings.SEGMENTATION_CONFIG

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def segment(
        self,
        series: List[Dict[str, float]],
        methods: List[str],
        sensitivity: float,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        if len(series) < 4:
            return {
                'success': False,
                'error': 'Series too short for segmentation (minimum 4 points required)',
            }

        # ruptures expects a 2-D array (n_samples, n_features)
        values = np.array([p['value'] for p in series], dtype=float).reshape(-1, 1)
        penalty = self._sensitivity_to_penalty(sensitivity)

        change_points: Dict[str, List[float]] = {}
        segments: Dict[str, List[Dict]] = {}

        for method in methods:
            if method not in SUPPORTED_METHODS:
                print(f"Unknown segmentation method '{method}', skipping")
                continue

            breakpoints = self._run_pelt(values, SUPPORTED_METHODS[method], penalty)
            change_points[method] = [series[bp]['time'] for bp in breakpoints[:-1]]
            segments[method] = self._build_segments(series, breakpoints)

        result = {
            'success': True,
            'change_points': change_points,
            'segments': segments,
            'penalty_used': round(penalty, 3),
            'sensitivity': sensitivity,
        }

        self.save_debug(series, result, label)
        return result

    # ------------------------------------------------------------------
    # Debug output
    # ------------------------------------------------------------------

    def save_debug(
        self,
        series: List[Dict[str, float]],
        result: Dict[str, Any],
        label: Optional[str],
    ):
        try:
            slug = label if label else 'unknown'
            out_dir = Path(settings.BASE_DIR) / 'debug_output' / slug
            out_dir.mkdir(parents=True, exist_ok=True)

            # Save JSON
            json_path = out_dir / 'segmentation.json'
            with open(json_path, 'w') as f:
                json.dump(result, f, indent=2)

            # Build plot
            times = [p['time'] for p in series]
            values = [p['value'] for p in series]

            method_colors = {'mean': 'steelblue', 'std': 'darkorange'}
            n_methods = len(result['change_points'])
            fig, axes = plt.subplots(n_methods, 1, figsize=(16, 4 * n_methods), squeeze=False)

            for ax, (method, cps) in zip(axes[:, 0], result['change_points'].items()):
                ax.plot(times, values, color='gray', linewidth=1, label='series')

                color = method_colors.get(method, 'red')
                for cp in cps:
                    ax.axvline(cp, color=color, linewidth=1.5, linestyle='--', alpha=0.8)

                # Shade alternating segments
                segs = result['segments'][method]
                for i, seg in enumerate(segs):
                    ax.axvspan(seg['start'], seg['end'],
                               alpha=0.07 if i % 2 == 0 else 0.14, color=color)
                    mid = (seg['start'] + seg['end']) / 2
                    ax.text(mid, ax.get_ylim()[1] if ax.get_ylim()[1] else max(values),
                            f"µ={seg['mean']:.1f}\nσ={seg['std']:.1f}",
                            ha='center', va='top', fontsize=6, color=color)

                ax.set_title(
                    f'Method: {method}  |  {len(cps)} change point(s)  |  '
                    f'penalty={result["penalty_used"]}  sensitivity={result["sensitivity"]}',
                    fontsize=11,
                )
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Value')
                ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plot_path = out_dir / 'segmentation.png'
            plt.savefig(str(plot_path), dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Segmentation debug saved to: {out_dir}")

        except Exception as e:
            print(f"Error saving segmentation debug output: {e}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sensitivity_to_penalty(self, sensitivity: float) -> float:
        """Map sensitivity in [0, 1] to a PELT penalty on a log scale.

        sensitivity=0  ->  max_penalty  (very few, only major change points)
        sensitivity=1  ->  min_penalty  (many, fine-grained change points)
        """
        sensitivity = max(0.0, min(1.0, sensitivity))
        min_pen = self.config['min_penalty']
        max_pen = self.config['max_penalty']
        return math.exp((1.0 - sensitivity) * math.log(max_pen / min_pen)) * min_pen

    def _run_pelt(self, values: np.ndarray, model: str, penalty: float) -> List[int]:
        min_size = self.config['min_segment_samples']
        try:
            algo = rpt.Pelt(model=model, min_size=min_size).fit(values)
            return algo.predict(pen=penalty)
        except Exception as e:
            print(f"PELT failed (model={model}, pen={penalty:.2f}): {e}")
            return [len(values)]  # single segment — no change points detected

    def _build_segments(
        self,
        series: List[Dict[str, float]],
        breakpoints: List[int],
    ) -> List[Dict[str, Any]]:
        """Build segment summary dicts from ruptures breakpoint indices."""
        segments = []
        prev = 0
        for bp in breakpoints:
            chunk = series[prev:bp]
            if not chunk:
                prev = bp
                continue
            vals = np.array([p['value'] for p in chunk], dtype=float)
            segments.append({
                'start': round(chunk[0]['time'], 3),
                'end': round(chunk[-1]['time'], 3),
                'mean': round(float(np.mean(vals)), 4),
                'std': round(float(np.std(vals)), 4),
                'min': round(float(np.min(vals)), 4),
                'max': round(float(np.max(vals)), 4),
                'count': len(chunk),
            })
            prev = bp
        return segments
