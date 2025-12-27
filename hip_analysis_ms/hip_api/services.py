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

    def calculate_hip_metrics(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate hip movement metrics from landmark data.

        Metrics include:
        - Hip center position (x, y, z) over time
        - Hip sway (lateral movement)
        - Hip distance (width between hips)
        """
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

    def save_hip_movement_plots(self, metrics: Dict[str, Any], recording_id: str) -> Optional[str]:
        """
        Save hip movement visualizations to debug directory.

        Creates multiple subplots showing:
        - Hip center position over time (X, Y, Z)
        - Hip distance (width) over time
        - Hip sway (lateral movement)
        """
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug' / recording_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Convert timestamps to frame indices for plotting
            frame_indices = list(range(len(metrics['timestamps'])))

            # Create figure with multiple subplots
            fig, axs = plt.subplots(3, 2, figsize=(16, 12))
            fig.suptitle(f'Hip Movement Analysis - Recording {recording_id}', fontsize=16)

            # Plot 1: Hip Center X position over time
            axs[0, 0].plot(frame_indices, metrics['hip_center_x'], linewidth=1, color='blue')
            axs[0, 0].set_xlabel('Frame Index')
            axs[0, 0].set_ylabel('X Position')
            axs[0, 0].set_title('Hip Center - Lateral Movement (X)')
            axs[0, 0].grid(True, alpha=0.3)

            # Plot 2: Hip Center Y position over time
            axs[0, 1].plot(frame_indices, metrics['hip_center_y'], linewidth=1, color='green')
            axs[0, 1].set_xlabel('Frame Index')
            axs[0, 1].set_ylabel('Y Position')
            axs[0, 1].set_title('Hip Center - Vertical Movement (Y)')
            axs[0, 1].grid(True, alpha=0.3)

            # Plot 3: Hip Center Z position over time
            axs[1, 0].plot(frame_indices, metrics['hip_center_z'], linewidth=1, color='red')
            axs[1, 0].set_xlabel('Frame Index')
            axs[1, 0].set_ylabel('Z Position')
            axs[1, 0].set_title('Hip Center - Depth Movement (Z)')
            axs[1, 0].grid(True, alpha=0.3)

            # Plot 4: Hip Distance (width) over time
            axs[1, 1].plot(frame_indices, metrics['hip_distance'], linewidth=1, color='purple')
            axs[1, 1].set_xlabel('Frame Index')
            axs[1, 1].set_ylabel('Distance')
            axs[1, 1].set_title('Hip Distance (Width)')
            axs[1, 1].grid(True, alpha=0.3)

            # Plot 5: Left vs Right Hip X positions
            axs[2, 0].plot(frame_indices, metrics['left_hip_x'], linewidth=1, color='orange', label='Left Hip')
            axs[2, 0].plot(frame_indices, metrics['right_hip_x'], linewidth=1, color='cyan', label='Right Hip')
            axs[2, 0].set_xlabel('Frame Index')
            axs[2, 0].set_ylabel('X Position')
            axs[2, 0].set_title('Left vs Right Hip - Lateral Position')
            axs[2, 0].legend()
            axs[2, 0].grid(True, alpha=0.3)

            # Plot 6: Hip sway statistics
            if len(metrics['hip_center_x']) > 0:
                sway_x = np.array(metrics['hip_center_x'])
                sway_std = np.std(sway_x)
                sway_range = np.max(sway_x) - np.min(sway_x)

                axs[2, 1].text(0.5, 0.7, f"Hip Sway Statistics", ha='center', fontsize=14, weight='bold')
                axs[2, 1].text(0.5, 0.5, f"Lateral Range: {sway_range:.4f}", ha='center', fontsize=12)
                axs[2, 1].text(0.5, 0.4, f"Std Dev: {sway_std:.4f}", ha='center', fontsize=12)
                axs[2, 1].text(0.5, 0.3, f"Mean X: {np.mean(sway_x):.4f}", ha='center', fontsize=12)
                axs[2, 1].text(0.5, 0.2, f"Total Frames: {len(frame_indices)}", ha='center', fontsize=12)
                axs[2, 1].axis('off')

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
        """
        Analyze hip movements from landmark data.

        Args:
            recording_id: ID of the recording to analyze

        Returns:
            Dictionary with success status and hip movement analysis results
        """
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

            # Save debug plots
            self.save_hip_movement_plots(metrics, str(recording_id))

            print(f"[DEBUG] Hip movement analysis completed successfully")

            return {
                'success': True,
                'recording_id': recording_id,
                'statistics': stats
            }

        except Exception as e:
            import traceback
            print(f"Error analyzing hip movement: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
