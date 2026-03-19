from pathlib import Path
from typing import Optional
import subprocess
import threading
import requests

import librosa
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from django.conf import settings

from .db_connection import get_recording_by_id


class AudioAnalysisService:
    def __init__(self):
        pass

    def trigger_transcription_async(self, recording_id: int) -> None:

        def _trigger():
            try:
                url = f"{settings.TRANSCRIPT_SERVICE_URL}/{recording_id}/transcribe/"
                print(f"[ASYNC] Triggering transcription for recording {recording_id} at {url}")

                # Short timeout - we only need to send the request, not wait for transcription
                response = requests.post(url, timeout=2)

                # If we get here, request was sent successfully
                print(f"[ASYNC] Transcription request sent successfully for recording {recording_id}")

            except requests.exceptions.Timeout:
                # This is expected - transcription takes a long time
                # The important thing is the request was sent
                print(f"[ASYNC] Transcription request sent (processing will continue on server)")
            except requests.exceptions.ConnectionError as e:
                print(f"[ASYNC] Could not connect to transcript service: {e}")
            except Exception as e:
                print(f"[ASYNC] Error triggering transcription: {e}")

        # Start the request in a background thread
        thread = threading.Thread(target=_trigger, daemon=True)
        thread.start()
        print(f"[ASYNC] Transcription thread started for recording {recording_id}")

    def save_waveform_plot(self, audio: np.ndarray, sr: int, recording_id: str) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Calculate time axis
            duration = len(audio) / sr
            time = np.linspace(0, duration, len(audio))

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 6))
            ax.plot(time, audio, linewidth=0.5, color='#1f77b4')
            ax.set_xlabel('Time (s)', fontsize=12)
            ax.set_ylabel('Amplitude', fontsize=12)
            ax.set_title(f'Audio Waveform - Sample Rate: {sr} Hz', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([-1.1, 1.1])

            output_path = debug_dir / 'audio_amplitude.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Waveform visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving waveform visualization: {e}")
            return None

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


    def process_audio(self, recording_id: int) -> dict:
        try:
            print(f"[DEBUG] Starting audio processing for recording_id: {recording_id}")

            # Get recording information
            print(f"[DEBUG] Fetching recording from database...")
            recording = get_recording_by_id(recording_id)
            if not recording:
                print(f"[DEBUG] Recording not found!")
                return {
                    'success': False,
                    'error': f'Recording with ID {recording_id} not found'
                }
            print(f"[DEBUG] Recording found: {recording}")

            # Construct paths
            video_filename = recording['filename']
            wav_filename = Path(video_filename).stem + '.wav'
            processed_filename = Path(video_filename).stem + '_processed.wav'

            wav_path = Path(settings.VIDEO_STORAGE_PATH) / wav_filename
            video_path = Path(settings.VIDEO_STORAGE_PATH) / video_filename
            processed_path = Path(settings.VIDEO_STORAGE_PATH) / processed_filename

            print(f"[DEBUG] WAV path: {wav_path}")
            print(f"[DEBUG] Processed path: {processed_path}")

            # Exctract audio
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

            print(f"[DEBUG] WAV file exists, proceeding to audio processing...")

            # Load audio
            print(f"[DEBUG] Loading audio from: {wav_path}")
            audio, sr_original = librosa.load(str(wav_path))
            print(f"[DEBUG] Audio loaded: {len(audio)} samples at {sr_original} Hz")

            # Normalize
            audio_normalized = librosa.util.normalize(audio)
            print(f"Audio normalized: {len(audio_normalized)} samples")

            # Resample (in case audio was injected and not processed from before)
            target_sr = 16000
            audio_resampled = librosa.resample(audio_normalized, orig_sr=sr_original, target_sr=target_sr)
            print(f"Audio resampled to 16kHz: {len(audio_resampled)} samples at {target_sr} Hz")

            # Noise reduction
            # TODO: Implement noise reduction
            audio_final = audio_resampled

            # Save file
            import soundfile as sf
            sf.write(str(processed_path), audio_final, target_sr)
            print(f"Processed audio saved to: {processed_path}")

            # Generate visualization
            if settings.DEBUG:
                self.save_waveform_plot(audio_final, target_sr, str(recording_id))

            # Trigger transcription asynchronously (non-blocking)
            if settings.AUTO_TRIGGER_TRANSCRIPTION:
                print(f"[DEBUG] Auto-triggering transcription for recording {recording_id}")
                self.trigger_transcription_async(recording_id)
            else:
                print(f"[DEBUG] Auto-trigger transcription is disabled")

            return {
                'success': True,
                'recording_id': recording_id,
                'original_wav_path': str(wav_path),
                'processed_wav_path': str(processed_path),
                'duration': len(audio_final) / target_sr,
                'sample_rate': target_sr,
                'samples': len(audio_final),
                'transcription_triggered': settings.AUTO_TRIGGER_TRANSCRIPTION
            }

        except Exception as e:
            import traceback
            print(f"Error processing audio: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
