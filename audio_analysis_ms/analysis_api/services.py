"""
Simple audio analysis service for extracting and visualizing audio amplitude.
"""
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import (
    get_recording_by_id,
    get_analysis_by_recording_id
)


class AudioAnalysisService:
    """Service for analyzing audio files and creating amplitude visualizations."""

    def __init__(self):
        pass

    def save_amplitude_plot(self, audio: np.ndarray, sr: float, recording_id: str) -> Optional[str]:
        """
        Create and save a simple amplitude plot without normalization or resampling.

        Args:
            audio: Raw audio data
            sr: Sample rate
            recording_id: Recording ID for debug output

        Returns:
            Path to saved visualization or None
        """
        try:
            # Create debug output directory for this recording
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Calculate time axis
            duration = len(audio) / sr
            time = np.linspace(0, duration, len(audio))

            # Create simple amplitude plot
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(time, audio, linewidth=0.5)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_title(f'Audio Waveform - Sample Rate: {sr} Hz')
            ax.grid(True, alpha=0.3)

            # Save the figure
            output_path = debug_dir / 'audio_amplitude.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Amplitude visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving amplitude visualization: {e}")
            return None

    def analyze_audio(self, recording_id: int) -> dict:
        """
        Analyze audio file and create amplitude visualization.

        Args:
            recording_id: ID of the recording in the database

        Returns:
            Dictionary with analysis results
        """
        try:
            # Get the recording to find the filename
            recording = get_recording_by_id(recording_id)
            if not recording:
                return {
                    'success': False,
                    'error': f'Recording with ID {recording_id} not found'
                }

            # Construct WAV file path (same as video filename but with .wav extension)
            video_filename = recording['filename']
            wav_filename = Path(video_filename).stem + '.wav'
            wav_path = Path(settings.VIDEO_STORAGE_PATH) / wav_filename

            # Check if WAV file exists
            if not wav_path.exists():
                return {
                    'success': False,
                    'error': f'WAV file not found at: {wav_path}'
                }

            # Get the analysis record for this recording
            analysis = get_analysis_by_recording_id(recording_id)
            if not analysis:
                return {
                    'success': False,
                    'error': f'No analysis found for recording ID: {recording_id}'
                }

            analysis_id = analysis['id']

            # Load audio without any normalization or resampling
            print(f"Loading audio from: {wav_path}")
            audio, sr = sf.read(str(wav_path))
            print(f"Audio loaded: {len(audio)} samples at {sr} Hz ({len(audio)/sr:.2f}s)")

            # Create amplitude visualization
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
