from pathlib import Path
from typing import Optional, List, Dict, Any

import librosa
import matplotlib
import numpy as np
import requests

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import get_recording_by_id


class VolumeAnalysisService:
    def __init__(self):
        self.config = settings.VOLUME_ANALYSIS_CONFIG

    def rms_to_dbfs(self, rms: np.ndarray) -> np.ndarray:
        # Clamp to silence floor to avoid log(0)
        silence_floor = self.config['silence_floor_dbfs']
        min_rms = 10 ** (silence_floor / 20.0)
        return 20.0 * np.log10(np.maximum(rms, min_rms))

    def compute_silence_floor(self, dbfs: np.ndarray) -> float:
        # 10th-percentile of all frames estimates the noise floor; +6 dB headroom
        dynamic = float(np.percentile(dbfs, 10)) + 6.0
        return max(dynamic, self.config['silence_floor_dbfs'])

    def detect_volume_segments(
        self,
        dbfs: np.ndarray,
        sr: float,
        hop_length: int,
        silence_floor: float,
    ) -> Dict[str, List[Dict[str, Any]]]:
        too_soft_threshold = self.config['too_soft_dbfs']
        too_loud_threshold = self.config['too_loud_dbfs']
        min_duration = self.config['min_segment_duration_ms'] / 1000.0
        duration_per_frame = hop_length / sr

        too_soft_segments = []
        too_loud_segments = []

        for label, mask, segments in [
            ('too_soft', (dbfs > silence_floor) & (dbfs < too_soft_threshold), too_soft_segments),
            ('too_loud', dbfs > too_loud_threshold, too_loud_segments),
        ]:
            current_start = None
            for i, flagged in enumerate(mask):
                if flagged and current_start is None:
                    current_start = i
                elif not flagged and current_start is not None:
                    start_time = current_start * duration_per_frame
                    end_time = i * duration_per_frame
                    if end_time - start_time >= min_duration:
                        segments.append({
                            'start_timestamp': round(start_time, 2),
                            'end_timestamp': round(end_time, 2),
                            'duration_seconds': round(end_time - start_time, 2),
                            'mean_dbfs': round(float(dbfs[current_start:i].mean()), 2),
                        })
                    current_start = None

            # Close any open segment at the end
            if current_start is not None:
                start_time = current_start * duration_per_frame
                end_time = len(mask) * duration_per_frame
                if end_time - start_time >= min_duration:
                    segments.append({
                        'start_timestamp': round(start_time, 2),
                        'end_timestamp': round(end_time, 2),
                        'duration_seconds': round(end_time - start_time, 2),
                        'mean_dbfs': round(float(dbfs[current_start:].mean()), 2),
                    })

        return {'too_soft': too_soft_segments, 'too_loud': too_loud_segments}

    def save_volume_plot(
        self,
        rms: np.ndarray,
        dbfs: np.ndarray,
        sr: float,
        recording_id: str,
        segments: Dict[str, List[Dict[str, Any]]] = None,
        silence_floor: float = None,
    ) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            hop_length = 800
            duration_per_frame = hop_length / sr
            time = np.arange(len(rms)) * duration_per_frame

            fig, (ax_rms, ax_dbfs) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            fig.suptitle(f'Volume Analysis - Sample Rate: {sr} Hz', fontsize=14, fontweight='bold')

            # --- RMS plot ---
            ax_rms.plot(time, rms, linewidth=1, color='red', label=f'RMS (mean: {rms.mean():.4f})')
            ax_rms.set_ylabel('RMS Energy')
            ax_rms.set_title('RMS Energy')
            ax_rms.grid(True, alpha=0.3)
            ax_rms.legend(loc='upper right')

            # --- dBFS plot ---
            too_soft = self.config['too_soft_dbfs']
            too_loud = self.config['too_loud_dbfs']
            if silence_floor is None:
                silence_floor = self.config['silence_floor_dbfs']

            ax_dbfs.plot(time, dbfs, linewidth=1, color='steelblue',
                         label=f'dBFS (mean: {dbfs[dbfs > silence_floor].mean():.1f} dBFS)')
            ax_dbfs.axhline(too_soft, color='orange', linestyle='--', linewidth=1.5,
                            label=f'Too soft ({too_soft} dBFS)')
            ax_dbfs.axhline(too_loud, color='red', linestyle='--', linewidth=1.5,
                            label=f'Too loud ({too_loud} dBFS)')
            ax_dbfs.axhline(silence_floor, color='gray', linestyle=':', linewidth=1.0,
                            label=f'Silence floor ({silence_floor:.1f} dBFS, auto)')

            # Shade violation segments
            if segments:
                for seg in segments.get('too_soft', []):
                    ax_dbfs.axvspan(seg['start_timestamp'], seg['end_timestamp'],
                                    color='orange', alpha=0.25,
                                    label='Too soft' if seg == segments['too_soft'][0] else '')
                for seg in segments.get('too_loud', []):
                    ax_dbfs.axvspan(seg['start_timestamp'], seg['end_timestamp'],
                                    color='red', alpha=0.25,
                                    label='Too loud' if seg == segments['too_loud'][0] else '')

            ax_dbfs.set_xlabel('Time (s)')
            ax_dbfs.set_ylabel('dBFS')
            ax_dbfs.set_title('dBFS (Full Scale)')
            ax_dbfs.set_ylim([silence_floor - 5, 5])
            ax_dbfs.grid(True, alpha=0.3)

            # Deduplicate legend labels
            handles, labels = ax_dbfs.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax_dbfs.legend(by_label.values(), by_label.keys(), loc='upper right')

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
    ) -> Optional[Dict]:
        try:
            speech_floor = max(silence_floor, self.config['too_soft_dbfs'])
            frames_per_second = round(sr / hop_length)

            # Build 1-second-averaged dBFS series using only speech-level frames.
            # Between-word gaps sit well below too_soft_dbfs and would drag the mean
            # down if included, so we filter them out here.
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

            # Get recording information
            recording = get_recording_by_id(recording_id)
            if not recording:
                return {
                    'success': False,
                    'error': f'Recording with ID {recording_id} not found'
                }

            # Construct path to processed audio
            video_filename = recording['filename']
            processed_filename = Path(video_filename).stem + '_processed.wav'
            processed_path = Path(settings.VIDEO_STORAGE_PATH) / processed_filename

            if not processed_path.exists():
                return {
                    'success': False,
                    'error': f'Processed audio file not found at: {processed_path}'
                }

            print(f"[DEBUG] Loading processed audio from: {processed_path}")

            # Load processed audio
            audio, sr = librosa.load(str(processed_path), sr=None)
            print(f"[DEBUG] Audio loaded: {len(audio)} samples at {sr} Hz")

            # Extract volume using RMS energy
            hop_length = 800
            rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop_length)[0]
            print(f"Volume extracted: mean RMS={rms.mean():.4f}, min={rms.min():.4f}, max={rms.max():.4f}")

            # Convert to dBFS
            dbfs = self.rms_to_dbfs(rms)
            silence_floor = self.compute_silence_floor(dbfs)
            voiced_dbfs = dbfs[dbfs > silence_floor]
            print(f"dBFS: mean={voiced_dbfs.mean():.1f}, min={dbfs.min():.1f}, max={dbfs.max():.1f} (silence_floor={silence_floor:.1f} dBFS)")

            # Detect too-soft and too-loud segments
            segments = self.detect_volume_segments(dbfs, sr, hop_length, silence_floor)
            print(f"[DEBUG] Too-soft segments: {len(segments['too_soft'])}, Too-loud segments: {len(segments['too_loud'])}")

            # Save debug plot
            self.save_volume_plot(rms, dbfs, sr, str(recording_id), segments, silence_floor)

            # Call segmentation service
            segmentation = self.call_segmentation(dbfs, sr, hop_length, recording_id, silence_floor)

            result = {
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
                'too_soft_segments': segments['too_soft'],
                'too_soft_count': len(segments['too_soft']),
                'too_loud_segments': segments['too_loud'],
                'too_loud_count': len(segments['too_loud']),
                'segmentation': segmentation,
            }

            import json
            from pathlib import Path
            result_path = Path(settings.BASE_DIR) / 'debug' / str(recording_id) / 'volume.json'
            result_path.parent.mkdir(parents=True, exist_ok=True)
            with open(result_path, 'w') as f:
                json.dump(result, f)

            return result

        except Exception as e:
            import traceback
            print(f"Error analyzing volume: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }