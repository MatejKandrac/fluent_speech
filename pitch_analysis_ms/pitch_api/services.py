from pathlib import Path
from typing import Optional

import librosa
import matplotlib
import numpy as np

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import get_recording_by_id


class PitchAnalysisService:
    def __init__(self):
        pass

    def save_pitch_plot(self, pitch: np.ndarray, sr: float, recording_id: str) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Calculate time based on hop_length (800 samples)
            hop_length = 800
            duration_per_frame = hop_length / sr
            time = np.arange(len(pitch)) * duration_per_frame

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(time, pitch, linewidth=1, color='green')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Frequency (Hz)')
            ax.set_title(f'Pitch - Mean: {pitch.mean():.2f} Hz - Sample Rate: {sr} Hz')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 400])

            output_path = debug_dir / 'pitch.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Pitch visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving pitch visualization: {e}")
            return None

    def analyze_pitch(self, recording_id: int) -> dict:
        try:
            print(f"[DEBUG] Starting pitch analysis for recording_id: {recording_id}")

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

            # Extract pitch using YIN algorithm
            hop_length = 800
            pitch = librosa.yin(
                audio, fmin=50, fmax=300, sr=sr,
                frame_length=1600, hop_length=hop_length
            )
            print(f"Pitch extracted: mean={pitch.mean():.2f} Hz, min={pitch.min():.2f}, max={pitch.max():.2f}")

            # Save debug plot
            self.save_pitch_plot(pitch, sr, str(recording_id))

            # TODO: Save pitch data to database (implement later)

            return {
                'success': True,
                'recording_id': recording_id,
                'pitch_frames': len(pitch),
                'pitch_mean': float(pitch.mean()),
                'pitch_min': float(pitch.min()),
                'pitch_max': float(pitch.max()),
                'pitch_std': float(pitch.std())
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing pitch: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
