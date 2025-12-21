from pathlib import Path
from typing import Optional
import subprocess

import librosa
import matplotlib
import numpy as np

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import (
    get_recording_by_id,
    get_analysis_by_recording_id
)


class AudioAnalysisService:
    def __init__(self):
        pass

    def extract_audio_from_video(self, video_path: str, output_wav_path: str) -> bool:
        try:
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("WARNING: ffmpeg not found in PATH. Cannot extract audio.")
                return False

            print(f"Extracting audio from video: {video_path}")

            sample_rate = str(settings.AUDIO_EXTRACTION_CONFIG['sample_rate'])

            result = subprocess.run(
                ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                 '-ar', sample_rate, '-ac', '1', '-y', str(output_wav_path)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"ffmpeg error: {result.stderr}")
                return False

            print(f"WAV file saved at: {output_wav_path}")
            return True

        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False

    def save_amplitude_plot(self, audio: np.ndarray, sr: float, recording_id: str) -> Optional[str]:

        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            duration = len(audio) / sr
            time = np.linspace(0, duration, len(audio))

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(time, audio, linewidth=0.5)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_title(f'Audio Waveform - Sample Rate: {sr} Hz')
            ax.grid(True, alpha=0.3)

            output_path = debug_dir / 'audio_amplitude.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Amplitude visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving amplitude visualization: {e}")
            return None

    def analyze_audio(self, recording_id: int) -> dict:
        try:
            # Get recording information
            recording = get_recording_by_id(recording_id)
            if not recording:
                return {
                    'success': False,
                    'error': f'Recording with ID {recording_id} not found'
                }

            # Construct paths
            video_filename = recording['filename']
            wav_filename = Path(video_filename).stem + '.wav'
            wav_path = Path(settings.VIDEO_STORAGE_PATH) / wav_filename
            video_path = Path(settings.VIDEO_STORAGE_PATH) / video_filename

            # Check if WAV file exists, if not, extract it from video
            if not wav_path.exists():
                print(f"WAV file not found at: {wav_path}")
                print("Attempting to extract audio from video...")

                # Check if video file exists
                if not video_path.exists():
                    return {
                        'success': False,
                        'error': f'Video file not found at: {video_path}'
                    }

                # Extract audio from video
                extraction_success = self.extract_audio_from_video(str(video_path), str(wav_path))
                if not extraction_success:
                    return {
                        'success': False,
                        'error': 'Failed to extract audio from video'
                    }

            # Get analysis record
            analysis = get_analysis_by_recording_id(recording_id)
            if not analysis:
                return {
                    'success': False,
                    'error': f'No analysis found for recording ID: {recording_id}'
                }

            analysis_id = analysis['id']

            # Load and analyze audio
            print(f"Loading audio from: {wav_path}")
            audio, sr = librosa.load(str(wav_path))
            audio = librosa.util.normalize(audio)
            pitch = librosa.yin(audio, fmin=50, fmax=300, sr=sr, frame_length=1600, hop_length=800)
            print(
                f"Pitch: {pitch.mean():.2f} Hz (min: {pitch.min():.2f}, max: {pitch.max():.2f})"
            )
            print(f"Audio loaded: {len(audio)} samples at {sr} Hz ({len(audio) / sr:.2f}s)")

            # Create visualization
            self.save_amplitude_plot(audio, sr, str(recording_id))

            return {
                'success': True,
                'analysis_id': analysis_id,
                'duration': len(audio) / sr,
                'sample_rate': sr,
                'samples': len(audio)
            }

        except Exception as e:
            print(f"Error analyzing audio: {e}")
            return {
                'success': False,
                'error': str(e)
            }
