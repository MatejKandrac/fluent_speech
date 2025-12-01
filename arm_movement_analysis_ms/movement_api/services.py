"""Arm movement analysis service."""
from typing import Dict, Any, Optional, List
from django.conf import settings
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .db_connection import get_analysis_by_recording_id


class ArmMovementAnalysisService:
    """Service for analyzing arm movements and detecting anomalous patterns."""

    def __init__(self):
        self.config = settings.MOVEMENT_ANALYSIS_CONFIG
        print(f"Loaded configuration: {self.config}")

    def get_video_analysis(self, recording_id: int) -> Optional[Dict[str, Any]]:
        """Fetch video analysis data from PostgreSQL."""
        return get_analysis_by_recording_id(recording_id)

    def normalize_landmarks(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize landmarks relative to body position and scale."""
        landmarks = frame_data.get('landmarks', {})

        required_landmarks = ['left_hip', 'right_hip', 'left_shoulder', 'right_shoulder']
        if not all(lm in landmarks for lm in required_landmarks):
            return None

        # Calculate body center (midpoint between hips)
        left_hip = landmarks['left_hip']
        right_hip = landmarks['right_hip']
        center_x = (left_hip['x'] + right_hip['x']) / 2
        center_y = (left_hip['y'] + right_hip['y']) / 2
        center_z = (left_hip['z'] + right_hip['z']) / 2

        # Calculate body scale (distance between shoulders)
        left_shoulder = landmarks['left_shoulder']
        right_shoulder = landmarks['right_shoulder']
        shoulder_distance = math.sqrt(
            (right_shoulder['x'] - left_shoulder['x']) ** 2 +
            (right_shoulder['y'] - left_shoulder['y']) ** 2 +
            (right_shoulder['z'] - left_shoulder['z']) ** 2
        )

        if shoulder_distance < 0.001:
            return None

        scale = shoulder_distance

        # Normalize all landmarks
        normalized_landmarks = {}
        arm_landmarks = ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                        'left_wrist', 'right_wrist', 'left_hip', 'right_hip']

        for landmark_name in arm_landmarks:
            if landmark_name in landmarks:
                original = landmarks[landmark_name]
                normalized_landmarks[landmark_name] = {
                    'x': (original['x'] - center_x) / scale,
                    'y': (original['y'] - center_y) / scale,
                    'z': (original['z'] - center_z) / scale,
                    'visibility': original['visibility']
                }

        return {
            'timestamp': frame_data.get('timestamp'),
            'landmarks': normalized_landmarks,
            'normalization_info': {
                'center': {'x': center_x, 'y': center_y, 'z': center_z},
                'scale': scale
            }
        }

    def calculate_wrist_kinematics(self, normalized_frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate velocity and acceleration for wrist movements."""
        kinematics_data = []

        prev_left_wrist_pos = None
        prev_right_wrist_pos = None
        prev_left_velocity = 0.0
        prev_right_velocity = 0.0

        for frame_idx, frame in enumerate(normalized_frames):
            landmarks = frame.get('landmarks', {})
            left_wrist = landmarks.get('left_wrist')
            right_wrist = landmarks.get('right_wrist')

            frame_data = {
                'timestamp': frame.get('timestamp'),
                'left_wrist': None,
                'right_wrist': None
            }

            # Left wrist kinematics
            if left_wrist:
                current_pos = {
                    'x': left_wrist['x'],
                    'y': left_wrist['y'],
                    'z': left_wrist['z']
                }

                if prev_left_wrist_pos is not None:
                    velocity = math.sqrt(
                        (current_pos['x'] - prev_left_wrist_pos['x']) ** 2 +
                        (current_pos['y'] - prev_left_wrist_pos['y']) ** 2 +
                        (current_pos['z'] - prev_left_wrist_pos['z']) ** 2
                    )
                else:
                    velocity = 0.0

                acceleration = abs(velocity - prev_left_velocity)

                frame_data['left_wrist'] = {
                    'position': current_pos,
                    'velocity': velocity,
                    'acceleration': acceleration,
                    'visibility': left_wrist['visibility']
                }

                prev_left_wrist_pos = current_pos
                prev_left_velocity = velocity

            # Right wrist kinematics
            if right_wrist:
                current_pos = {
                    'x': right_wrist['x'],
                    'y': right_wrist['y'],
                    'z': right_wrist['z']
                }

                if prev_right_wrist_pos is not None:
                    velocity = math.sqrt(
                        (current_pos['x'] - prev_right_wrist_pos['x']) ** 2 +
                        (current_pos['y'] - prev_right_wrist_pos['y']) ** 2 +
                        (current_pos['z'] - prev_right_wrist_pos['z']) ** 2
                    )
                else:
                    velocity = 0.0

                acceleration = abs(velocity - prev_right_velocity)

                frame_data['right_wrist'] = {
                    'position': current_pos,
                    'velocity': velocity,
                    'acceleration': acceleration,
                    'visibility': right_wrist['visibility']
                }

                prev_right_wrist_pos = current_pos
                prev_right_velocity = velocity

            kinematics_data.append(frame_data)

        return kinematics_data

    def visualize_wrist_kinematics(self, kinematics_data: List[Dict[str, Any]],
                                   recording_id: int,
                                   output_dir: Optional[str] = None) -> str:
        """Generate visualization graphs for wrist velocity and acceleration."""
        if output_dir is None:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract data for plotting
        timestamps = []
        left_velocities = []
        right_velocities = []
        left_accelerations = []
        right_accelerations = []

        for frame in kinematics_data:
            timestamp = frame.get('timestamp', '')
            timestamps.append(timestamp)

            if frame.get('left_wrist'):
                left_velocities.append(frame['left_wrist']['velocity'])
                left_accelerations.append(frame['left_wrist']['acceleration'])
            else:
                left_velocities.append(None)
                left_accelerations.append(None)

            if frame.get('right_wrist'):
                right_velocities.append(frame['right_wrist']['velocity'])
                right_accelerations.append(frame['right_wrist']['acceleration'])
            else:
                right_velocities.append(None)
                right_accelerations.append(None)

        frame_indices = list(range(len(timestamps)))

        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle(f'Wrist Movement Analysis - Recording {recording_id}',
                     fontsize=16, fontweight='bold')

        # Velocity subplot
        ax1.plot(frame_indices, left_velocities, label='Left Wrist',
                color='blue', linewidth=1.5, alpha=0.7)
        ax1.plot(frame_indices, right_velocities, label='Right Wrist',
                color='red', linewidth=1.5, alpha=0.7)
        ax1.set_xlabel('Frame Index', fontsize=12)
        ax1.set_ylabel('Velocity (normalized units/frame)', fontsize=12)
        ax1.set_title('Wrist Velocity Over Time', fontsize=13, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

        # Acceleration subplot
        ax2.plot(frame_indices, left_accelerations, label='Left Wrist',
                color='blue', linewidth=1.5, alpha=0.7)
        ax2.plot(frame_indices, right_accelerations, label='Right Wrist',
                color='red', linewidth=1.5, alpha=0.7)
        ax2.set_xlabel('Frame Index', fontsize=12)
        ax2.set_ylabel('Acceleration (change in velocity)', fontsize=12)
        ax2.set_title('Wrist Acceleration Over Time', fontsize=13, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

        # Add statistics
        if left_velocities and any(v is not None for v in left_velocities):
            left_vel_values = [v for v in left_velocities if v is not None]
            avg_left_vel = sum(left_vel_values) / len(left_vel_values) if left_vel_values else 0
            max_left_vel = max(left_vel_values) if left_vel_values else 0

            ax1.text(0.02, 0.98, f'Left Avg: {avg_left_vel:.4f}\nLeft Max: {max_left_vel:.4f}',
                    transform=ax1.transAxes, fontsize=9, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

        if right_velocities and any(v is not None for v in right_velocities):
            right_vel_values = [v for v in right_velocities if v is not None]
            avg_right_vel = sum(right_vel_values) / len(right_vel_values) if right_vel_values else 0
            max_right_vel = max(right_vel_values) if right_vel_values else 0

            ax1.text(0.98, 0.98, f'Right Avg: {avg_right_vel:.4f}\nRight Max: {max_right_vel:.4f}',
                    transform=ax1.transAxes, fontsize=9, verticalalignment='top',
                    horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

        plt.tight_layout()

        output_path = output_dir / f'wrist_kinematics_recording_{recording_id}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Visualization saved to: {output_path}")
        return str(output_path)

    def detect_movement_anomalies(self, kinematics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect periods of no movement and excessive movement."""
        no_movement_threshold = self.config['no_movement_velocity_threshold']
        excessive_movement_threshold = self.config['excessive_movement_velocity_threshold']
        min_frames = self.config['min_consecutive_frames']

        print(f"Detecting movement anomalies with thresholds:")
        print(f"  No movement: velocity < {no_movement_threshold}")
        print(f"  Excessive movement: velocity > {excessive_movement_threshold}")
        print(f"  Minimum consecutive frames: {min_frames}")

        no_movement_periods = []
        excessive_movement_periods = []

        left_no_movement_streak = []
        right_no_movement_streak = []
        left_excessive_streak = []
        right_excessive_streak = []

        for frame in kinematics_data:
            timestamp = frame.get('timestamp')

            # Check left wrist
            if frame.get('left_wrist'):
                left_vel = frame['left_wrist']['velocity']

                if left_vel < no_movement_threshold:
                    left_no_movement_streak.append(timestamp)
                else:
                    if len(left_no_movement_streak) >= min_frames:
                        no_movement_periods.append({
                            'wrist': 'left',
                            'start_timestamp': left_no_movement_streak[0],
                            'end_timestamp': left_no_movement_streak[-1],
                            'duration_frames': len(left_no_movement_streak)
                        })
                    left_no_movement_streak = []

                if left_vel > excessive_movement_threshold:
                    left_excessive_streak.append(timestamp)
                else:
                    if len(left_excessive_streak) >= min_frames:
                        excessive_movement_periods.append({
                            'wrist': 'left',
                            'start_timestamp': left_excessive_streak[0],
                            'end_timestamp': left_excessive_streak[-1],
                            'duration_frames': len(left_excessive_streak)
                        })
                    left_excessive_streak = []

            # Check right wrist
            if frame.get('right_wrist'):
                right_vel = frame['right_wrist']['velocity']

                if right_vel < no_movement_threshold:
                    right_no_movement_streak.append(timestamp)
                else:
                    if len(right_no_movement_streak) >= min_frames:
                        no_movement_periods.append({
                            'wrist': 'right',
                            'start_timestamp': right_no_movement_streak[0],
                            'end_timestamp': right_no_movement_streak[-1],
                            'duration_frames': len(right_no_movement_streak)
                        })
                    right_no_movement_streak = []

                if right_vel > excessive_movement_threshold:
                    right_excessive_streak.append(timestamp)
                else:
                    if len(right_excessive_streak) >= min_frames:
                        excessive_movement_periods.append({
                            'wrist': 'right',
                            'start_timestamp': right_excessive_streak[0],
                            'end_timestamp': right_excessive_streak[-1],
                            'duration_frames': len(right_excessive_streak)
                        })
                    right_excessive_streak = []

        # Handle remaining streaks at the end
        if len(left_no_movement_streak) >= min_frames:
            no_movement_periods.append({
                'wrist': 'left',
                'start_timestamp': left_no_movement_streak[0],
                'end_timestamp': left_no_movement_streak[-1],
                'duration_frames': len(left_no_movement_streak)
            })

        if len(right_no_movement_streak) >= min_frames:
            no_movement_periods.append({
                'wrist': 'right',
                'start_timestamp': right_no_movement_streak[0],
                'end_timestamp': right_no_movement_streak[-1],
                'duration_frames': len(right_no_movement_streak)
            })

        if len(left_excessive_streak) >= min_frames:
            excessive_movement_periods.append({
                'wrist': 'left',
                'start_timestamp': left_excessive_streak[0],
                'end_timestamp': left_excessive_streak[-1],
                'duration_frames': len(left_excessive_streak)
            })

        if len(right_excessive_streak) >= min_frames:
            excessive_movement_periods.append({
                'wrist': 'right',
                'start_timestamp': right_excessive_streak[0],
                'end_timestamp': right_excessive_streak[-1],
                'duration_frames': len(right_excessive_streak)
            })

        print(f"Detected {len(no_movement_periods)} no-movement periods")
        print(f"Detected {len(excessive_movement_periods)} excessive-movement periods")

        return {
            'no_movement_periods': no_movement_periods,
            'excessive_movement_periods': excessive_movement_periods,
            'thresholds_used': {
                'no_movement_velocity_threshold': no_movement_threshold,
                'excessive_movement_velocity_threshold': excessive_movement_threshold,
                'min_consecutive_frames': min_frames
            }
        }

    def _filter_segments_by_gap(self, segments: List[Dict[str, Any]], min_gap: int) -> List[Dict[str, Any]]:
        """Filter segments to ensure minimum gap between them."""
        if not segments:
            return []

        sorted_segments = sorted(segments, key=lambda s: s['frame_index'])
        filtered = []
        i = 0

        while i < len(sorted_segments):
            group = [sorted_segments[i]]
            j = i + 1

            # Find all segments within min_gap
            while j < len(sorted_segments) and sorted_segments[j]['frame_index'] - sorted_segments[i]['frame_index'] < min_gap:
                group.append(sorted_segments[j])
                j += 1

            # Keep the one with largest change_magnitude
            best_segment = max(group, key=lambda s: s['change_magnitude'])
            filtered.append(best_segment)

            i = j

        return filtered

    def segment_by_average_change(self, kinematics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect sudden changes in movement intensity using sliding window averages."""
        window_size = self.config['segmentation_window_size']
        threshold = self.config['average_change_threshold']

        print(f"Segmenting by average change:")
        print(f"  Window size: {window_size} frames")
        print(f"  Change threshold: {threshold}")

        # Process left wrist
        left_velocities = [
            f['left_wrist']['velocity'] if f.get('left_wrist') else 0.0
            for f in kinematics_data
        ]

        left_segments_raw = []
        for i in range(len(left_velocities) - window_size):
            current_window = left_velocities[i:i + window_size]
            current_avg = sum(current_window) / len(current_window)

            next_window = left_velocities[i + window_size:i + 2 * window_size]
            if len(next_window) < window_size:
                break

            next_avg = sum(next_window) / len(next_window)
            change = abs(next_avg - current_avg)

            if change > threshold:
                segment_idx = i + window_size
                left_segments_raw.append({
                    'frame_index': segment_idx,
                    'timestamp': kinematics_data[segment_idx]['timestamp'],
                    'average_before': current_avg,
                    'average_after': next_avg,
                    'change_magnitude': change,
                    'change_type': 'increase' if next_avg > current_avg else 'decrease'
                })

        # Process right wrist
        right_velocities = [
            f['right_wrist']['velocity'] if f.get('right_wrist') else 0.0
            for f in kinematics_data
        ]

        right_segments_raw = []
        for i in range(len(right_velocities) - window_size):
            current_window = right_velocities[i:i + window_size]
            current_avg = sum(current_window) / len(current_window)

            next_window = right_velocities[i + window_size:i + 2 * window_size]
            if len(next_window) < window_size:
                break

            next_avg = sum(next_window) / len(next_window)
            change = abs(next_avg - current_avg)

            if change > threshold:
                segment_idx = i + window_size
                right_segments_raw.append({
                    'frame_index': segment_idx,
                    'timestamp': kinematics_data[segment_idx]['timestamp'],
                    'average_before': current_avg,
                    'average_after': next_avg,
                    'change_magnitude': change,
                    'change_type': 'increase' if next_avg > current_avg else 'decrease'
                })

        # Filter segments by minimum gap
        min_gap = self.config['min_segment_gap']
        left_segments = self._filter_segments_by_gap(left_segments_raw, min_gap)
        right_segments = self._filter_segments_by_gap(right_segments_raw, min_gap)

        print(f"Found {len(left_segments_raw)} raw left segments, filtered to {len(left_segments)}")
        print(f"Found {len(right_segments_raw)} raw right segments, filtered to {len(right_segments)}")

        return {
            'left_wrist_segments': left_segments,
            'right_wrist_segments': right_segments,
            'parameters': {
                'window_size': window_size,
                'threshold': threshold
            }
        }

    def segment_by_trend_change(self, kinematics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect changes in movement trend (slope) using linear regression."""
        window_size = self.config['segmentation_window_size']
        threshold = self.config['trend_change_threshold']

        print(f"Segmenting by trend change:")
        print(f"  Window size: {window_size} frames")
        print(f"  Trend change threshold: {threshold}")

        def calculate_trend(values):
            """Calculate linear regression slope."""
            n = len(values)
            if n < 2:
                return 0.0

            x_vals = list(range(n))
            sum_x = sum(x_vals)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(x_vals, values))
            sum_x2 = sum(x ** 2 for x in x_vals)

            denominator = (n * sum_x2 - sum_x ** 2)
            if abs(denominator) < 1e-10:
                return 0.0

            slope = (n * sum_xy - sum_x * sum_y) / denominator
            return slope

        # Process left wrist
        left_velocities = [
            f['left_wrist']['velocity'] if f.get('left_wrist') else 0.0
            for f in kinematics_data
        ]

        left_segments_raw = []
        prev_trend = None
        for i in range(len(left_velocities) - window_size):
            window = left_velocities[i:i + window_size]
            current_trend = calculate_trend(window)

            if prev_trend is not None:
                sign_changed = (prev_trend > 0 and current_trend < 0) or (prev_trend < 0 and current_trend > 0)
                trend_change = abs(current_trend - prev_trend)
                significant_change = trend_change > threshold

                if sign_changed or significant_change:
                    segment_idx = i + window_size // 2
                    if segment_idx < len(kinematics_data):
                        left_segments_raw.append({
                            'frame_index': segment_idx,
                            'timestamp': kinematics_data[segment_idx]['timestamp'],
                            'trend_before': prev_trend,
                            'trend_after': current_trend,
                            'change_magnitude': trend_change,
                            'change_type': 'reversal' if sign_changed else 'magnitude_change'
                        })

            prev_trend = current_trend

        # Process right wrist
        right_velocities = [
            f['right_wrist']['velocity'] if f.get('right_wrist') else 0.0
            for f in kinematics_data
        ]

        right_segments_raw = []
        prev_trend = None
        for i in range(len(right_velocities) - window_size):
            window = right_velocities[i:i + window_size]
            current_trend = calculate_trend(window)

            if prev_trend is not None:
                sign_changed = (prev_trend > 0 and current_trend < 0) or (prev_trend < 0 and current_trend > 0)
                trend_change = abs(current_trend - prev_trend)
                significant_change = trend_change > threshold

                if sign_changed or significant_change:
                    segment_idx = i + window_size // 2
                    if segment_idx < len(kinematics_data):
                        right_segments_raw.append({
                            'frame_index': segment_idx,
                            'timestamp': kinematics_data[segment_idx]['timestamp'],
                            'trend_before': prev_trend,
                            'trend_after': current_trend,
                            'change_magnitude': trend_change,
                            'change_type': 'reversal' if sign_changed else 'magnitude_change'
                        })

            prev_trend = current_trend

        # Filter segments by minimum gap
        min_gap = self.config['min_segment_gap']
        left_segments = self._filter_segments_by_gap(left_segments_raw, min_gap)
        right_segments = self._filter_segments_by_gap(right_segments_raw, min_gap)

        print(f"Found {len(left_segments_raw)} raw left trend changes, filtered to {len(left_segments)}")
        print(f"Found {len(right_segments_raw)} raw right trend changes, filtered to {len(right_segments)}")

        return {
            'left_wrist_trend_changes': left_segments,
            'right_wrist_trend_changes': right_segments,
            'parameters': {
                'window_size': window_size,
                'threshold': threshold
            }
        }

    def analyze_arm_movements(self, recording_id: int) -> Dict[str, Any]:
        """Main analysis pipeline for arm movements."""
        print(f"Analyzing arm movements for recording ID: {recording_id}")

        # Step 1: Fetch data
        analysis_data = self.get_video_analysis(recording_id)
        if not analysis_data:
            return {'success': False, 'error': 'Video analysis not found'}

        total_frames = len(analysis_data.get('data', []))
        print(f"Retrieved {total_frames} frames from database")

        # Step 2: Normalize landmarks
        normalized_frames = []
        for frame in analysis_data.get('data', []):
            normalized = self.normalize_landmarks(frame)
            if normalized:
                normalized_frames.append(normalized)

        if not normalized_frames:
            return {'success': False, 'error': 'No frames could be normalized'}

        print(f"Normalized {len(normalized_frames)} frames")

        # Step 3: Calculate kinematics
        kinematics_data = self.calculate_wrist_kinematics(normalized_frames)
        print(f"Calculated kinematics for {len(kinematics_data)} frames")

        # Step 4: Generate visualization
        visualization_path = self.visualize_wrist_kinematics(kinematics_data, recording_id)

        # Step 5: Detect anomalies
        anomalies = self.detect_movement_anomalies(kinematics_data)

        # Step 6: Perform segmentation
        average_segments = self.segment_by_average_change(kinematics_data)
        trend_segments = self.segment_by_trend_change(kinematics_data)

        # Calculate statistics
        left_velocities = [f['left_wrist']['velocity'] for f in kinematics_data if f['left_wrist'] is not None]
        right_velocities = [f['right_wrist']['velocity'] for f in kinematics_data if f['right_wrist'] is not None]
        left_accelerations = [f['left_wrist']['acceleration'] for f in kinematics_data if f['left_wrist'] is not None]
        right_accelerations = [f['right_wrist']['acceleration'] for f in kinematics_data if f['right_wrist'] is not None]

        statistics = {
            'left_wrist': {
                'avg_velocity': sum(left_velocities) / len(left_velocities) if left_velocities else 0,
                'max_velocity': max(left_velocities) if left_velocities else 0,
                'avg_acceleration': sum(left_accelerations) / len(left_accelerations) if left_accelerations else 0,
                'max_acceleration': max(left_accelerations) if left_accelerations else 0
            },
            'right_wrist': {
                'avg_velocity': sum(right_velocities) / len(right_velocities) if right_velocities else 0,
                'max_velocity': max(right_velocities) if right_velocities else 0,
                'avg_acceleration': sum(right_accelerations) / len(right_accelerations) if right_accelerations else 0,
                'max_acceleration': max(right_accelerations) if right_accelerations else 0
            }
        }

        return {
            'success': True,
            'recording_id': recording_id,
            'total_frames': total_frames,
            'normalized_frames_count': len(normalized_frames),
            'visualization_path': visualization_path,
            'statistics': statistics,
            'anomalies': {
                'no_movement_periods': anomalies['no_movement_periods'],
                'excessive_movement_periods': anomalies['excessive_movement_periods'],
                'thresholds': anomalies['thresholds_used']
            },
            'segmentation': {
                'average_change': average_segments,
                'trend_change': trend_segments
            },
            'message': 'Arm movement analysis completed successfully.'
        }
