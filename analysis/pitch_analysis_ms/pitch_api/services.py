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

    def detect_monotonous_segments(
        self,
        pitch: np.ndarray,
        sr: float,
        hop_length: int,
        window_size: int = 30,
        std_threshold: float = 10.0,
        range_threshold: float = 20.0
    ) -> list:

        monotonous_segments = []
        duration_per_frame = hop_length / sr

        # Iterate through pitch data with sliding window
        for i in range(len(pitch) - window_size + 1):
            window = pitch[i:i + window_size]

            # Filter out NaN values (unvoiced segments)
            voiced_window = window[~np.isnan(window)]

            # Skip if window has too few voiced frames (less than 50% voiced)
            if len(voiced_window) < window_size * 0.5:
                continue

            # Calculate statistics for this window
            window_std = np.std(voiced_window)
            window_range = np.max(voiced_window) - np.min(voiced_window)

            # Check if segment is monotonous
            if window_std < std_threshold or window_range < range_threshold:
                start_time = i * duration_per_frame
                end_time = (i + window_size) * duration_per_frame

                # Check if this segment overlaps with the last one
                # If yes, merge them; if no, create a new segment
                if monotonous_segments and monotonous_segments[-1]['end_timestamp'] >= start_time:
                    # Extend the previous segment
                    monotonous_segments[-1]['end_timestamp'] = end_time
                    monotonous_segments[-1]['duration_seconds'] = (
                        monotonous_segments[-1]['end_timestamp'] -
                        monotonous_segments[-1]['start_timestamp']
                    )
                else:
                    # Create new segment
                    monotonous_segments.append({
                        'start_timestamp': round(start_time, 2),
                        'end_timestamp': round(end_time, 2),
                        'duration_seconds': round(end_time - start_time, 2),
                        'std_dev': round(float(window_std), 2),
                        'range': round(float(window_range), 2)
                    })

        return monotonous_segments

    def save_pitch_plot(self, pitch: np.ndarray, sr: float, recording_id: str) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Calculate time based on hop_length (800 samples)
            hop_length = 800
            duration_per_frame = hop_length / sr
            time = np.arange(len(pitch)) * duration_per_frame

            # Separate voiced (non-NaN) and unvoiced (NaN) segments
            voiced_mask = ~np.isnan(pitch)
            unvoiced_mask = np.isnan(pitch)

            # Calculate mean only from voiced segments
            voiced_pitch = pitch[voiced_mask]
            pitch_mean = voiced_pitch.mean() if len(voiced_pitch) > 0 else 0

            fig, ax = plt.subplots(figsize=(14, 6))

            # Plot pitch - matplotlib will automatically break the line at NaN values
            ax.plot(time, pitch, linewidth=1.5, color='green',
                   label=f'Voiced (mean: {pitch_mean:.1f} Hz)')

            # Add light gray shaded regions for unvoiced/silent segments
            # Find continuous unvoiced regions
            unvoiced_indices = np.where(unvoiced_mask)[0]
            if len(unvoiced_indices) > 0:
                # Group consecutive indices
                splits = np.where(np.diff(unvoiced_indices) != 1)[0] + 1
                unvoiced_groups = np.split(unvoiced_indices, splits)

                # Shade each unvoiced region
                for group in unvoiced_groups:
                    if len(group) > 0:
                        start_time = time[group[0]]
                        end_time = time[group[-1]] + duration_per_frame
                        ax.axvspan(start_time, end_time, color='lightgray',
                                  alpha=0.3, label='Unvoiced/Silent' if group is unvoiced_groups[0] else '')

            ax.set_xlabel('Time (s)', fontsize=12)
            ax.set_ylabel('Frequency (Hz)', fontsize=12)
            ax.set_title(f'Pitch Analysis - Sample Rate: {sr} Hz', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([50, 350])

            # Remove duplicate labels in legend
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper right')

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
            frame_length = 1600
            pitch = librosa.yin(
                audio, fmin=50, fmax=300, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            print(f"Pitch extracted (raw): mean={pitch.mean():.2f} Hz, min={pitch.min():.2f}, max={pitch.max():.2f}")

            # Calculate RMS energy to detect unvoiced/silent segments
            rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]

            # Filter pitch: set to 0 where energy is low or pitch is unreliable
            energy_threshold = 0.02  # Minimum RMS energy for voiced segments
            pitch_threshold = 70     # Minimum valid pitch (Hz) - below this is likely error

            # Create mask for valid voiced segments
            valid_mask = (rms > energy_threshold) & (pitch >= pitch_threshold)

            # Set invalid segments to NaN (creates discontinuous plot)
            pitch_filtered = pitch.copy()
            pitch_filtered[~valid_mask] = np.nan

            # Calculate statistics only from voiced segments (non-NaN)
            voiced_pitch = pitch_filtered[~np.isnan(pitch_filtered)]

            if len(voiced_pitch) > 0:
                pitch_mean = float(voiced_pitch.mean())
                pitch_min = float(voiced_pitch.min())
                pitch_max = float(voiced_pitch.max())
                pitch_std = float(voiced_pitch.std())
            else:
                pitch_mean = 0.0
                pitch_min = 0.0
                pitch_max = 0.0
                pitch_std = 0.0

            print(f"Pitch filtered: voiced_frames={len(voiced_pitch)}/{len(pitch_filtered)}, mean={pitch_mean:.2f} Hz")

            # Save debug plot with filtered pitch
            self.save_pitch_plot(pitch_filtered, sr, str(recording_id))

            # Detect monotonous segments using sliding window analysis
            monotonous_segments = self.detect_monotonous_segments(
                pitch_filtered,
                sr,
                hop_length,
                window_size=30,
                std_threshold=10.0,
                range_threshold=20.0
            )

            print(f"[DEBUG] Detected {len(monotonous_segments)} monotonous segments")

            # TODO: Save pitch data to database (implement later)

            return {
                'success': True,
                'recording_id': recording_id,
                'pitch_frames': len(pitch_filtered),
                'voiced_frames': len(voiced_pitch),
                'pitch_mean': pitch_mean,
                'pitch_min': pitch_min,
                'pitch_max': pitch_max,
                'pitch_std': pitch_std,
                'monotonous_segments': monotonous_segments,
                'monotonous_segments_count': len(monotonous_segments)
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing pitch: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
