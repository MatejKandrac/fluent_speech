from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import librosa
import matplotlib
import numpy as np
import requests

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import get_recording_by_id


class VolumeAnalysisService:
    def __init__(self):
        self.config = settings.VOLUME_ANALYSIS_CONFIG

    def rms_to_dbfs(self, rms: np.ndarray) -> np.ndarray:
        silence_floor = self.config['silence_floor_dbfs']
        min_rms = 10 ** (silence_floor / 20.0)
        return 20.0 * np.log10(np.maximum(rms, min_rms))

    def compute_silence_floor(self, dbfs: np.ndarray) -> float:
        dynamic = float(np.percentile(dbfs, 10)) + 6.0
        return max(dynamic, self.config['silence_floor_dbfs'])

    def compute_adaptive_thresholds(self, dbfs: np.ndarray, silence_floor: float) -> Tuple[float, float]:
        voiced = dbfs[dbfs > silence_floor]
        if len(voiced) == 0:
            return silence_floor + 10.0, 0.0
        # 75th percentile of voiced frames = comfortable speech level for this recording/mic
        reference = float(np.percentile(voiced, 75))
        too_soft = reference - self.config['soft_margin_db']
        too_loud = reference + self.config['loud_margin_db']
        print(f"Adaptive thresholds: reference={reference:.1f} dBFS, "
              f"too_soft={too_soft:.1f} dBFS, too_loud={too_loud:.1f} dBFS")
        return too_soft, too_loud

    def _merge_segments(
        self,
        segments: List[Dict[str, Any]],
        dbfs: np.ndarray,
        sr: float,
        hop_length: int,
        merge_gap_s: float,
        min_duration: float,
    ) -> List[Dict[str, Any]]:
        if not segments:
            return []
        duration_per_frame = hop_length / sr
        merged = [dict(segments[0])]
        for seg in segments[1:]:
            if seg['start_timestamp'] - merged[-1]['end_timestamp'] <= merge_gap_s:
                merged[-1]['end_timestamp'] = seg['end_timestamp']
                merged[-1]['duration_seconds'] = round(
                    merged[-1]['end_timestamp'] - merged[-1]['start_timestamp'], 2
                )
                start_frame = round(merged[-1]['start_timestamp'] / duration_per_frame)
                end_frame = round(merged[-1]['end_timestamp'] / duration_per_frame)
                merged[-1]['mean_dbfs'] = round(float(dbfs[start_frame:end_frame].mean()), 2)
            else:
                merged.append(dict(seg))
        return [s for s in merged if s['duration_seconds'] >= min_duration]

    def _coverage_filter(
        self,
        segments: List[Dict[str, Any]],
        dbfs: np.ndarray,
        sr: float,
        hop_length: int,
        silence_floor: float,
        low: Optional[float],
        high: Optional[float],
        min_coverage: float,
    ) -> List[Dict[str, Any]]:
        """Keep only segments where ≥ min_coverage fraction of frames actually violate threshold."""
        duration_per_frame = hop_length / sr
        filtered = []
        for seg in segments:
            start_frame = int(round(seg['start_timestamp'] / duration_per_frame))
            end_frame = int(round(seg['end_timestamp'] / duration_per_frame))
            window = dbfs[start_frame:end_frame]
            if len(window) == 0:
                continue
            if low is not None:
                bad = np.sum((window > silence_floor) & (window < low))
            elif high is not None:
                bad = np.sum(window > high)
            else:
                bad = 0
            if bad / len(window) >= min_coverage:
                filtered.append(seg)
        return filtered

    def detect_volume_segments(
        self,
        dbfs: np.ndarray,
        sr: float,
        hop_length: int,
        silence_floor: float,
        too_soft: float,
        too_loud: float,
    ) -> Dict[str, List[Dict[str, Any]]]:
        min_duration = self.config['min_segment_duration_ms'] / 1000.0
        duration_per_frame = hop_length / sr
        raw_min = duration_per_frame

        too_soft_segments: List[Dict[str, Any]] = []
        too_loud_segments: List[Dict[str, Any]] = []

        for mask, segments in [
            ((dbfs > silence_floor) & (dbfs < too_soft), too_soft_segments),
            (dbfs > too_loud, too_loud_segments),
        ]:
            current_start = None
            for i, flagged in enumerate(mask):
                if flagged and current_start is None:
                    current_start = i
                elif not flagged and current_start is not None:
                    start_time = current_start * duration_per_frame
                    end_time = i * duration_per_frame
                    if end_time - start_time >= raw_min:
                        segments.append({
                            'start_timestamp': round(start_time, 2),
                            'end_timestamp': round(end_time, 2),
                            'duration_seconds': round(end_time - start_time, 2),
                            'mean_dbfs': round(float(dbfs[current_start:i].mean()), 2),
                        })
                    current_start = None

            if current_start is not None:
                start_time = current_start * duration_per_frame
                end_time = len(mask) * duration_per_frame
                if end_time - start_time >= raw_min:
                    segments.append({
                        'start_timestamp': round(start_time, 2),
                        'end_timestamp': round(end_time, 2),
                        'duration_seconds': round(end_time - start_time, 2),
                        'mean_dbfs': round(float(dbfs[current_start:].mean()), 2),
                    })

        merge_gap = self.config.get('merge_gap_s', 0.5)
        min_coverage = self.config.get('min_bad_frame_coverage', 0.5)

        too_soft_segments = self._merge_segments(
            too_soft_segments, dbfs, sr, hop_length, merge_gap_s=merge_gap, min_duration=min_duration)
        too_soft_segments = self._coverage_filter(
            too_soft_segments, dbfs, sr, hop_length, silence_floor,
            low=too_soft, high=None, min_coverage=min_coverage)

        too_loud_segments = self._merge_segments(
            too_loud_segments, dbfs, sr, hop_length, merge_gap_s=merge_gap, min_duration=min_duration)
        too_loud_segments = self._coverage_filter(
            too_loud_segments, dbfs, sr, hop_length, silence_floor,
            low=None, high=too_loud, min_coverage=min_coverage)

        return {'too_soft': too_soft_segments, 'too_loud': too_loud_segments}

    def save_volume_plot(
        self,
        rms: np.ndarray,
        dbfs: np.ndarray,
        sr: float,
        recording_id: str,
        too_soft: float,
        too_loud: float,
        segments: Dict[str, List[Dict[str, Any]]] = None,
        silence_floor: float = None,
    ) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            hop_length = 800
            duration_per_frame = hop_length / sr
            time = np.arange(len(rms)) * duration_per_frame

            if silence_floor is None:
                silence_floor = self.config['silence_floor_dbfs']

            COLOR_SOFT = '#29B6F6'
            COLOR_LOUD = '#EF5350'

            fig, (ax_rms, ax_dbfs) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            fig.suptitle(f'Volume Analysis - Sample Rate: {sr} Hz', fontsize=14, fontweight='bold')

            # --- RMS plot ---
            ax_rms.plot(time, rms, linewidth=1, color='#455A64', label=f'RMS (mean: {rms.mean():.4f})')
            if segments:
                for i, seg in enumerate(segments.get('too_soft', [])):
                    ax_rms.axvspan(seg['start_timestamp'], seg['end_timestamp'],
                                   color=COLOR_SOFT, alpha=0.45,
                                   label='Too soft' if i == 0 else '')
                for i, seg in enumerate(segments.get('too_loud', [])):
                    ax_rms.axvspan(seg['start_timestamp'], seg['end_timestamp'],
                                   color=COLOR_LOUD, alpha=0.45,
                                   label='Too loud' if i == 0 else '')
            ax_rms.set_ylabel('RMS Energy')
            ax_rms.set_title('RMS Energy')
            ax_rms.grid(True, alpha=0.3)
            handles, labels = ax_rms.get_legend_handles_labels()
            ax_rms.legend(dict(zip(labels, handles)).values(), dict(zip(labels, handles)).keys(), loc='upper right')

            # --- dBFS plot ---
            voiced_dbfs = dbfs[dbfs > silence_floor]
            ax_dbfs.plot(time, dbfs, linewidth=1, color='steelblue',
                         label=f'dBFS (mean: {voiced_dbfs.mean():.1f} dBFS)')
            ax_dbfs.axhline(too_soft, color=COLOR_SOFT, linestyle='--', linewidth=2.0,
                            label=f'Too soft ({too_soft:.1f} dBFS, adaptive)')
            ax_dbfs.axhline(too_loud, color=COLOR_LOUD, linestyle='--', linewidth=2.0,
                            label=f'Too loud ({too_loud:.1f} dBFS, adaptive)')
            ax_dbfs.axhline(silence_floor, color='gray', linestyle=':', linewidth=1.0,
                            label=f'Silence floor ({silence_floor:.1f} dBFS, auto)')

            if segments:
                for i, seg in enumerate(segments.get('too_soft', [])):
                    ax_dbfs.axvspan(seg['start_timestamp'], seg['end_timestamp'],
                                    color=COLOR_SOFT, alpha=0.40,
                                    label='Too soft' if i == 0 else '')
                    if seg['duration_seconds'] >= 2.0:
                        ax_dbfs.text(
                            (seg['start_timestamp'] + seg['end_timestamp']) / 2,
                            too_soft + 1.5, 'TICHO',
                            ha='center', va='bottom', fontsize=7, color=COLOR_SOFT, fontweight='bold'
                        )
                for i, seg in enumerate(segments.get('too_loud', [])):
                    ax_dbfs.axvspan(seg['start_timestamp'], seg['end_timestamp'],
                                    color=COLOR_LOUD, alpha=0.40,
                                    label='Too loud' if i == 0 else '')
                    if seg['duration_seconds'] >= 2.0:
                        ax_dbfs.text(
                            (seg['start_timestamp'] + seg['end_timestamp']) / 2,
                            too_loud - 1.5, 'HLASNO',
                            ha='center', va='top', fontsize=7, color=COLOR_LOUD, fontweight='bold'
                        )

            ax_dbfs.set_xlabel('Time (s)')
            ax_dbfs.set_ylabel('dBFS')
            ax_dbfs.set_title('dBFS (Full Scale)')
            ax_dbfs.set_ylim([silence_floor - 5, 5])
            ax_dbfs.grid(True, alpha=0.3)
            handles, labels = ax_dbfs.get_legend_handles_labels()
            ax_dbfs.legend(dict(zip(labels, handles)).values(), dict(zip(labels, handles)).keys(), loc='upper right')

            plt.tight_layout()
            output_path = debug_dir / 'volume.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Volume visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving volume visualization: {e}")
            return None

    def call_segmentation(
        self,
        dbfs: np.ndarray,
        sr: float,
        hop_length: int,
        recording_id: int,
        silence_floor: float,
        too_soft: float,
    ) -> Optional[Dict]:
        try:
            speech_floor = max(silence_floor, too_soft)
            frames_per_second = round(sr / hop_length)

            series = []
            for i in range(0, len(dbfs), frames_per_second):
                window = dbfs[i:i + frames_per_second]
                voiced = window[window > speech_floor]
                if len(voiced) == 0:
                    continue
                t = round(i / frames_per_second, 3)
                series.append({'time': t, 'value': round(float(voiced.mean()), 3)})

            if len(series) < 4:
                print("Not enough voiced seconds for volume segmentation")
                return None

            url = f"{settings.SEGMENTATION_SERVICE_URL}/api/v1/segment/"
            response = requests.post(url, json={
                'series': series,
                'methods': ['mean'],
                'sensitivity': self.config['segmentation_sensitivity'],
                'label': f'volume_{recording_id}',
            }, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Segmentation service call failed: {e}")
            return None

    def analyze_volume(self, recording_id: int) -> dict:
        try:
            print(f"[DEBUG] Starting volume analysis for recording_id: {recording_id}")

            recording = get_recording_by_id(recording_id)
            if not recording:
                return {'success': False, 'error': f'Recording with ID {recording_id} not found'}

            video_filename = recording['filename']
            processed_filename = Path(video_filename).stem + '.wav'
            processed_path = Path(settings.VIDEO_STORAGE_PATH) / processed_filename

            if not processed_path.exists():
                return {'success': False, 'error': f'Processed audio file not found at: {processed_path}'}

            print(f"[DEBUG] Loading processed audio from: {processed_path}")
            audio, sr = librosa.load(str(processed_path), sr=None)
            print(f"[DEBUG] Audio loaded: {len(audio)} samples at {sr} Hz")

            hop_length = 800
            rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop_length)[0]
            print(f"Volume extracted: mean RMS={rms.mean():.4f}, min={rms.min():.4f}, max={rms.max():.4f}")

            dbfs = self.rms_to_dbfs(rms)
            silence_floor = self.compute_silence_floor(dbfs)
            voiced_dbfs = dbfs[dbfs > silence_floor]
            print(f"dBFS: mean={voiced_dbfs.mean():.1f}, min={dbfs.min():.1f}, max={dbfs.max():.1f} "
                  f"(silence_floor={silence_floor:.1f} dBFS)")

            too_soft, too_loud = self.compute_adaptive_thresholds(dbfs, silence_floor)

            segments = self.detect_volume_segments(dbfs, sr, hop_length, silence_floor, too_soft, too_loud)
            print(f"[DEBUG] Too-soft segments: {len(segments['too_soft'])}, "
                  f"Too-loud segments: {len(segments['too_loud'])}")

            self.save_volume_plot(rms, dbfs, sr, str(recording_id), too_soft, too_loud, segments, silence_floor)

            segmentation = self.call_segmentation(dbfs, sr, hop_length, recording_id, silence_floor, too_soft)

            return {
                'success': True,
                'recording_id': recording_id,
                'volume_frames': len(rms),
                'volume_mean_rms': float(rms.mean()),
                'volume_min_rms': float(rms.min()),
                'volume_max_rms': float(rms.max()),
                'volume_std_rms': float(rms.std()),
                'dbfs_mean': round(float(voiced_dbfs.mean()), 2) if len(voiced_dbfs) > 0 else None,
                'dbfs_min': round(float(dbfs.min()), 2),
                'dbfs_max': round(float(dbfs.max()), 2),
                'adaptive_too_soft_dbfs': round(too_soft, 2),
                'adaptive_too_loud_dbfs': round(too_loud, 2),
                'too_soft_segments': segments['too_soft'],
                'too_soft_count': len(segments['too_soft']),
                'too_loud_segments': segments['too_loud'],
                'too_loud_count': len(segments['too_loud']),
                'segmentation': segmentation,
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing volume: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {'success': False, 'error': str(e)}