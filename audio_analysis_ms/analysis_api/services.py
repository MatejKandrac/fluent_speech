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
    insert_audio_features_batch
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

            output_path = debug_dir / 'amplitude.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Amplitude visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving amplitude visualization: {e}")
            return None

    def save_pitch_plot(self, pitch: np.ndarray, sr: float, recording_id: str) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / recording_id
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

    def save_volume_plot(self, volume: np.ndarray, sr: float, recording_id: str) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Calculate time based on hop_length (800 samples for alignment with pitch)
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

    def analyze_audio(self, recording_id: int) -> dict:
        try:
            print(f"[DEBUG] Starting audio analysis for recording_id: {recording_id}")

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
            wav_path = Path(settings.VIDEO_STORAGE_PATH) / wav_filename
            video_path = Path(settings.VIDEO_STORAGE_PATH) / video_filename
            print(f"[DEBUG] WAV path: {wav_path}")

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

            print(f"[DEBUG] WAV file exists, proceeding to audio analysis...")

            # === STAGE 1: Load audio (before normalization) ===
            print(f"[DEBUG] Loading audio from: {wav_path}")
            audio_before_norm, sr_original = librosa.load(str(wav_path))
            print(f"[DEBUG] Audio loaded (before normalization): {len(audio_before_norm)} samples at {sr_original} Hz")

            # === STAGE 2: Normalize audio ===
            audio_after_norm = librosa.util.normalize(audio_before_norm)
            sr_after_norm = sr_original
            print(f"Audio normalized: {len(audio_after_norm)} samples at {sr_after_norm} Hz")

            # === STAGE 3: Resample to 16kHz ===
            target_sr = 16000
            audio_after_resample = librosa.resample(audio_after_norm, orig_sr=sr_after_norm, target_sr=target_sr)
            sr_after_resample = target_sr
            print(f"Audio resampled to 16kHz: {len(audio_after_resample)} samples at {sr_after_resample} Hz")

            # === Calculate pitch and volume for final processed audio ===
            print("\nCalculating pitch and volume...")
            hop_length_aligned = 800

            # Calculate pitch after resampling
            pitch_final = librosa.yin(
                audio_after_resample, fmin=50, fmax=300, sr=sr_after_resample,
                frame_length=1600, hop_length=hop_length_aligned
            )
            print(f"Pitch: mean={pitch_final.mean():.2f} Hz, min={pitch_final.min():.2f}, max={pitch_final.max():.2f}")

            # Calculate volume with same hop_length as pitch for alignment
            volume_final = librosa.feature.rms(
                y=audio_after_resample, frame_length=2048, hop_length=hop_length_aligned
            )[0]
            print(f"Volume: mean RMS={volume_final.mean():.4f}")

            # Ensure they have the same length
            min_length = min(len(pitch_final), len(volume_final))
            pitch_final = pitch_final[:min_length]
            volume_final = volume_final[:min_length]

            print(f"Aligned features: {min_length} frames")

            # === Create visualizations ===
            print("\nGenerating visualizations...")
            self.save_amplitude_plot(audio_after_resample, sr_after_resample, str(recording_id))
            self.save_pitch_plot(pitch_final, sr_after_resample, str(recording_id))
            self.save_volume_plot(volume_final, sr_after_resample, str(recording_id))

            # === Save audio features to database ===
            print("\nSaving audio features to database...")
            from datetime import datetime, timedelta

            audio_features = []
            for i in range(min_length):
                # Calculate timestamp for this frame
                timestamp_seconds = (i * hop_length_aligned) / sr_after_resample
                timestamp = (datetime.min + timedelta(seconds=timestamp_seconds)).time().isoformat(
                    timespec='microseconds'
                )

                audio_features.append({
                    'timestamp': timestamp,
                    'pitch_hz': float(pitch_final[i]),
                    'volume_db': float(volume_final[i]),
                    'pitch_confidence': None  # YIN doesn't provide confidence directly
                })

            insert_audio_features_batch(recording_id, audio_features)
            print(f"Successfully saved {len(audio_features)} audio feature records to database")

            return {
                'success': True,
                'recording_id': recording_id,
                'duration': len(audio_after_resample) / sr_after_resample,
                'sample_rate': sr_after_resample,
                'samples': len(audio_after_resample),
                'audio_features_saved': len(audio_features)
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing audio: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
