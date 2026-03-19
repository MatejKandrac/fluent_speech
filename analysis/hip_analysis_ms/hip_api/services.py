from pathlib import Path
from typing import Optional, List, Dict, Any
import math

import matplotlib
import numpy as np

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from django.conf import settings

from .db_connection import get_recording_by_id, get_hip_landmarks_by_recording_id


class HipAnalysisService:
    def __init__(self):
        pass

    def detect_swaying_segments(
        self,
        hip_center_y: np.ndarray,
        timestamps: List[str],
        fps: float = 10.0,
        window_duration: float = 10.0,
        min_direction_changes: int = 5,
        min_amplitude: float = 0.02
    ) -> List[Dict[str, Any]]:
        if len(hip_center_y) < 3:
            return []

        # Calculate velocity (first derivative)
        velocity = np.diff(hip_center_y)

        # Calculate acceleration (second derivative)
        acceleration = np.diff(velocity)

        # Detect local maxima and minima (direction changes)
        # Direction change occurs when velocity changes sign
        # BUT only count it if the amplitude is significant enough
        direction_changes = []
        last_extremum_idx = 0
        last_extremum_value = hip_center_y[0]

        for i in range(1, len(velocity)):
            # Check if velocity changed sign (crossed zero)
            if velocity[i-1] * velocity[i] < 0:
                # Found a potential extremum at index i
                current_value = hip_center_y[i]
                amplitude = abs(current_value - last_extremum_value)

                # Only register this extremum if the amplitude is significant
                if amplitude >= min_amplitude:
                    direction_changes.append(i)
                    last_extremum_idx = i
                    last_extremum_value = current_value

        print(f"[DEBUG] Detected {len(direction_changes)} significant direction changes in hip movement (min amplitude: {min_amplitude})")

        # Sliding window analysis to find segments with excessive direction changes
        swaying_segments = []
        window_frames = int(window_duration * fps)

        for i in range(len(hip_center_y) - window_frames + 1):
            # Count direction changes within this window
            changes_in_window = sum(
                1 for change_idx in direction_changes
                if i <= change_idx < i + window_frames
            )

            # If direction changes exceed threshold, mark as swaying
            if changes_in_window >= min_direction_changes:
                start_time = i / fps
                end_time = (i + window_frames) / fps

                # Check if this segment overlaps with the last one
                if swaying_segments and swaying_segments[-1]['end_timestamp'] >= start_time:
                    # Extend the previous segment
                    swaying_segments[-1]['end_timestamp'] = end_time
                    swaying_segments[-1]['duration_seconds'] = (
                        swaying_segments[-1]['end_timestamp'] -
                        swaying_segments[-1]['start_timestamp']
                    )
                    swaying_segments[-1]['direction_changes'] = max(
                        swaying_segments[-1]['direction_changes'],
                        changes_in_window
                    )
                else:
                    # Create new segment
                    swaying_segments.append({
                        'start_timestamp': round(start_time, 2),
                        'end_timestamp': round(end_time, 2),
                        'duration_seconds': round(end_time - start_time, 2),
                        'direction_changes': changes_in_window
                    })

        return swaying_segments

    def calculate_hip_metrics(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = {
            'left_hip_x': [],
            'left_hip_y': [],
            'left_hip_z': [],
            'right_hip_x': [],
            'right_hip_y': [],
            'right_hip_z': [],
            'hip_center_x': [],
            'hip_center_y': [],
            'hip_center_z': [],
            'hip_distance': [],
            'timestamps': []
        }

        for frame in frames:
            landmarks = frame.get('landmarks', {})
            left_hip = landmarks.get('left_hip')
            right_hip = landmarks.get('right_hip')

            # Only process frames where both hips are visible
            if left_hip and right_hip:
                metrics['left_hip_x'].append(left_hip['x'])
                metrics['left_hip_y'].append(left_hip['y'])
                metrics['left_hip_z'].append(left_hip['z'])

                metrics['right_hip_x'].append(right_hip['x'])
                metrics['right_hip_y'].append(right_hip['y'])
                metrics['right_hip_z'].append(right_hip['z'])

                # Calculate hip center (midpoint)
                center_x = (left_hip['x'] + right_hip['x']) / 2
                center_y = (left_hip['y'] + right_hip['y']) / 2
                center_z = (left_hip['z'] + right_hip['z']) / 2

                metrics['hip_center_x'].append(center_x)
                metrics['hip_center_y'].append(center_y)
                metrics['hip_center_z'].append(center_z)

                # Calculate hip distance (width)
                distance = math.sqrt(
                    (right_hip['x'] - left_hip['x']) ** 2 +
                    (right_hip['y'] - left_hip['y']) ** 2 +
                    (right_hip['z'] - left_hip['z']) ** 2
                )
                metrics['hip_distance'].append(distance)

                metrics['timestamps'].append(frame.get('timestamp', ''))

        return metrics

    def save_hip_movement_plots(
        self,
        metrics: Dict[str, Any],
        recording_id: str,
        swaying_segments: List[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Convert timestamps to frame indices for plotting
            frame_indices = list(range(len(metrics['timestamps'])))
            fps = 10.0  # Frames per second

            # Create figure with single plot
            fig, ax = plt.subplots(figsize=(16, 6))
            fig.suptitle(f'Hip Movement Analysis - Recording {recording_id}', fontsize=16)

            # Plot Hip Center Y position (lateral movement - side to side)
            # Note: Y is used because MediaPipe frames are rotated
            ax.plot(frame_indices, metrics['hip_center_y'], linewidth=1.5, color='blue', label='Hip Center Y')
            ax.set_xlabel('Frame Index', fontsize=12)
            ax.set_ylabel('Y Position (normalized)', fontsize=12)
            ax.set_title('Hip Center - Lateral Movement (Side to Side)', fontsize=14)
            ax.grid(True, alpha=0.3)

            # Highlight swaying segments
            if swaying_segments:
                for segment in swaying_segments:
                    start_frame = int(segment['start_timestamp'] * fps)
                    end_frame = int(segment['end_timestamp'] * fps)

                    # Add shaded region for swaying segment
                    ax.axvspan(
                        start_frame,
                        end_frame,
                        color='red',
                        alpha=0.2,
                        label='Swaying' if segment == swaying_segments[0] else ''
                    )

                    # Add text annotation with number of direction changes
                    mid_frame = (start_frame + end_frame) / 2
                    y_pos = ax.get_ylim()[1] * 0.95
                    ax.text(
                        mid_frame,
                        y_pos,
                        f"{segment['direction_changes']} changes",
                        ha='center',
                        va='top',
                        fontsize=9,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.3)
                    )

            # Remove duplicate labels in legend
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper right')

            plt.tight_layout()

            output_path = debug_dir / 'hip_movement.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"Hip movement visualization saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error saving hip movement visualization: {e}")
            return None

    def analyze_hip_movement(self, recording_id: int) -> dict:
        try:
            print(f"[DEBUG] Starting hip movement analysis for recording_id: {recording_id}")

            # Get recording information
            recording = get_recording_by_id(recording_id)
            if not recording:
                return {
                    'success': False,
                    'error': f'Recording with ID {recording_id} not found'
                }

            # Get hip landmark data from database
            print(f"[DEBUG] Fetching hip landmark data from database...")
            frames = get_hip_landmarks_by_recording_id(recording_id)

            if not frames:
                return {
                    'success': False,
                    'error': 'No hip landmark data found for this recording'
                }

            print(f"[DEBUG] Retrieved {len(frames)} frames with hip landmarks")

            # Calculate hip metrics
            metrics = self.calculate_hip_metrics(frames)

            if not metrics['hip_center_x']:
                return {
                    'success': False,
                    'error': 'No valid hip data to analyze (both hips must be visible)'
                }

            # Calculate statistics
            hip_sway_x = np.array(metrics['hip_center_x'])
            hip_sway_y = np.array(metrics['hip_center_y'])
            hip_distances = np.array(metrics['hip_distance'])

            stats = {
                'total_frames': len(frames),
                'valid_frames': len(metrics['hip_center_x']),
                'hip_sway': {
                    'x_mean': float(np.mean(hip_sway_x)),
                    'x_std': float(np.std(hip_sway_x)),
                    'x_range': float(np.max(hip_sway_x) - np.min(hip_sway_x)),
                    'y_mean': float(np.mean(hip_sway_y)),
                    'y_std': float(np.std(hip_sway_y)),
                    'y_range': float(np.max(hip_sway_y) - np.min(hip_sway_y))
                },
                'hip_distance': {
                    'mean': float(np.mean(hip_distances)),
                    'std': float(np.std(hip_distances)),
                    'min': float(np.min(hip_distances)),
                    'max': float(np.max(hip_distances))
                }
            }

            # Detect swaying/dancing segments
            # Use Y coordinate because MediaPipe frames are rotated (Y = lateral movement)
            # Assume 10 FPS based on video processing settings (frame_interval=0.1)
            fps = 10.0
            swaying_segments = self.detect_swaying_segments(
                hip_sway_y,
                metrics['timestamps'],
                fps=fps,
                window_duration=10.0,
                min_direction_changes=5,
                min_amplitude=0.02  # Minimum normalized position change to count as significant movement
            )

            print(f"[DEBUG] Detected {len(swaying_segments)} swaying segments")

            # Save debug plots with swaying segments highlighted
            self.save_hip_movement_plots(metrics, str(recording_id), swaying_segments)

            print(f"[DEBUG] Hip movement analysis completed successfully")

            return {
                'success': True,
                'recording_id': recording_id,
                'statistics': stats,
                'swaying_segments': swaying_segments,
                'swaying_segments_count': len(swaying_segments)
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing hip movement: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
