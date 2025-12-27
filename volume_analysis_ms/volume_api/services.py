from pathlib import Path
from typing import Optional

import librosa
import matplotlib
import numpy as np

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import get_recording_by_id


class VolumeAnalysisService:
    def __init__(self):
        pass

    def save_volume_plot(self, volume: np.ndarray, sr: float, recording_id: str) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Calculate time based on hop_length (800 samples)
            hop_length = 800
            duration_per_frame = hop_length / sr
            time = np.arange(len(volume)) * duration_per_frame

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(time, volume, linewidth=1, color='red')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('RMS Energy')
            ax.set_title(f'Volume - Mean RMS: {volume.mean():.4f} - Sample Rate: {sr} Hz')
            ax.grid(True, alpha=0.3)

            output_path = debug_dir / 'volume.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Volume visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving volume visualization: {e}")
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
            volume = librosa.feature.rms(
                y=audio, frame_length=2048, hop_length=hop_length
            )[0]
            print(f"Volume extracted: mean RMS={volume.mean():.4f}, min={volume.min():.4f}, max={volume.max():.4f}")

            # Save debug plot
            self.save_volume_plot(volume, sr, str(recording_id))

            # TODO: Save volume data to database (implement later)

            return {
                'success': True,
                'recording_id': recording_id,
                'volume_frames': len(volume),
                'volume_mean': float(volume.mean()),
                'volume_min': float(volume.min()),
                'volume_max': float(volume.max()),
                'volume_std': float(volume.std())
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing volume: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
