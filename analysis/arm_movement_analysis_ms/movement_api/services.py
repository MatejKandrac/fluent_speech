from typing import Dict, Any, Optional, List
from django.conf import settings
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests

from .db_connection import get_analysis_by_recording_id


class ArmMovementAnalysisService:

    def __init__(self):
        self.config = settings.MOVEMENT_ANALYSIS_CONFIG
        print(f"Loaded configuration: {self.config}")

    def get_video_analysis(self, recording_id: int) -> Optional[Dict[str, Any]]:
        return get_analysis_by_recording_id(recording_id)

    def normalize_landmarks(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    def _merge_excessive_events(self, events: List[Dict[str, Any]], merge_gap_s: float) -> List[Dict[str, Any]]:
        """Merge events of the same wrist that are closer than merge_gap_s seconds."""
        if not events:
            return []
        merged = []
        current = dict(events[0])
        for ev in events[1:]:
            gap = ev['start_timestamp'] - current['end_timestamp']
            if gap <= merge_gap_s:
                current['end_timestamp'] = ev['end_timestamp']
                current['duration_frames'] += ev['duration_frames']
            else:
                merged.append(current)
                current = dict(ev)
        merged.append(current)
        return merged

    def detect_movement_anomalies(self, kinematics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect periods of no movement and excessive movement.

        No-movement: bilateral — ALL visible wrists must be below threshold
        simultaneously for min_consecutive_frames.  A single active hand breaks
        the streak.

        Excessive movement: per-hand — any frame above threshold starts an
        event (min_excessive_frames is typically 1).  Nearby events from the
        same hand are then merged so that a single back-and-forth swing
        produces one event rather than several isolated spikes.
        """
        no_movement_threshold = self.config['no_movement_velocity_threshold']
        excessive_movement_threshold = self.config['excessive_movement_velocity_threshold']
        min_frames = self.config['min_consecutive_frames']
        min_excessive_frames = self.config['min_excessive_frames']
        merge_gap_s = self.config['excessive_merge_gap_s']

        print(f"Detecting movement anomalies with thresholds:")
        print(f"  No movement: all visible wrists velocity < {no_movement_threshold}, min_frames={min_frames}")
        print(f"  Excessive movement: velocity > {excessive_movement_threshold}, min_frames={min_excessive_frames}, merge_gap={merge_gap_s}s")

        no_movement_periods = []
        raw_left_excessive = []
        raw_right_excessive = []

        no_movement_streak = []
        left_excessive_streak = []
        right_excessive_streak = []

        for frame in kinematics_data:
            timestamp = frame.get('timestamp')
            left_vel = frame['left_wrist']['velocity'] if frame.get('left_wrist') else None
            right_vel = frame['right_wrist']['velocity'] if frame.get('right_wrist') else None

            # ── Bilateral no-movement ──────────────────────────────────────────
            active_vels = [v for v in [left_vel, right_vel] if v is not None]
            both_still = bool(active_vels) and max(active_vels) < no_movement_threshold

            if both_still:
                no_movement_streak.append(timestamp)
            else:
                if len(no_movement_streak) >= min_frames:
                    no_movement_periods.append({
                        'start_timestamp': no_movement_streak[0],
                        'end_timestamp': no_movement_streak[-1],
                        'duration_frames': len(no_movement_streak)
                    })
                no_movement_streak = []

            # ── Per-hand excessive movement ────────────────────────────────────
            if left_vel is not None:
                if left_vel > excessive_movement_threshold:
                    left_excessive_streak.append(timestamp)
                else:
                    if len(left_excessive_streak) >= min_excessive_frames:
                        raw_left_excessive.append({
                            'wrist': 'left',
                            'start_timestamp': left_excessive_streak[0],
                            'end_timestamp': left_excessive_streak[-1],
                            'duration_frames': len(left_excessive_streak)
                        })
                    left_excessive_streak = []

            if right_vel is not None:
                if right_vel > excessive_movement_threshold:
                    right_excessive_streak.append(timestamp)
                else:
                    if len(right_excessive_streak) >= min_excessive_frames:
                        raw_right_excessive.append({
                            'wrist': 'right',
                            'start_timestamp': right_excessive_streak[0],
                            'end_timestamp': right_excessive_streak[-1],
                            'duration_frames': len(right_excessive_streak)
                        })
                    right_excessive_streak = []

        # Flush remaining streaks
        if len(no_movement_streak) >= min_frames:
            no_movement_periods.append({
                'start_timestamp': no_movement_streak[0],
                'end_timestamp': no_movement_streak[-1],
                'duration_frames': len(no_movement_streak)
            })
        if len(left_excessive_streak) >= min_excessive_frames:
            raw_left_excessive.append({
                'wrist': 'left',
                'start_timestamp': left_excessive_streak[0],
                'end_timestamp': left_excessive_streak[-1],
                'duration_frames': len(left_excessive_streak)
            })
        if len(right_excessive_streak) >= min_excessive_frames:
            raw_right_excessive.append({
                'wrist': 'right',
                'start_timestamp': right_excessive_streak[0],
                'end_timestamp': right_excessive_streak[-1],
                'duration_frames': len(right_excessive_streak)
            })

        # Merge nearby events per hand, then combine
        excessive_movement_periods = (
            self._merge_excessive_events(raw_left_excessive, merge_gap_s) +
            self._merge_excessive_events(raw_right_excessive, merge_gap_s)
        )

        print(f"Detected {len(no_movement_periods)} no-movement periods")
        print(f"Detected {len(excessive_movement_periods)} excessive-movement periods "
              f"(from {len(raw_left_excessive)} left + {len(raw_right_excessive)} right raw events)")

        return {
            'no_movement_periods': no_movement_periods,
            'excessive_movement_periods': excessive_movement_periods,
            'thresholds_used': {
                'no_movement_velocity_threshold': no_movement_threshold,
                'excessive_movement_velocity_threshold': excessive_movement_threshold,
                'min_consecutive_frames': min_frames,
                'min_excessive_frames': min_excessive_frames,
                'excessive_merge_gap_s': merge_gap_s,
            }
        }

    def call_segmentation(self, kinematics_data: List[Dict[str, Any]], fps: float, recording_id: int) -> dict:
        sensitivity = self.config['arm_segmentation_sensitivity']
        frames_per_second = max(1, round(fps))
        series = []

        for i in range(0, len(kinematics_data), frames_per_second):
            window = kinematics_data[i:i + frames_per_second]
            frame_vels = []
            for f in window:
                left_vel = f['left_wrist']['velocity'] if f.get('left_wrist') else None
                right_vel = f['right_wrist']['velocity'] if f.get('right_wrist') else None
                active = [v for v in [left_vel, right_vel] if v is not None]
                if active:
                    frame_vels.append(max(active))
            if not frame_vels:
                continue
            t = round(i / fps, 3)
            series.append({'time': t, 'value': round(float(sum(frame_vels) / len(frame_vels)), 6)})

        if len(series) < 2:
            return {'success': False, 'error': 'Not enough data for segmentation'}

        url = f"{settings.SEGMENTATION_SERVICE_URL}/api/v1/segment/"
        payload = {
            'series': series,
            'methods': ['std'],
            'sensitivity': sensitivity,
            'label': f'arm_{recording_id}',
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Segmentation service error: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_arm_movements(self, recording_id: int) -> Dict[str, Any]:
        print(f"Analyzing arm movements for recording ID: {recording_id}")

        # Step 1: Fetch data
        analysis_data = self.get_video_analysis(recording_id)
        if not analysis_data:
            return {'success': False, 'error': 'Video analysis not found'}

        fps = analysis_data.get('fps') or 30.0
        self.config['min_consecutive_frames'] = max(1, round(self.config['min_consecutive_duration_ms'] * fps / 1000))
        self.config['min_excessive_frames'] = max(1, round(self.config['excessive_min_consecutive_duration_ms'] * fps / 1000)) if self.config['excessive_min_consecutive_duration_ms'] > 0 else 1
        self.config['excessive_merge_gap_s'] = self.config['excessive_merge_gap_ms'] / 1000.0
        print(f"Using fps={fps}: min_consecutive_frames={self.config['min_consecutive_frames']}, "
              f"min_excessive_frames={self.config['min_excessive_frames']}, "
              f"excessive_merge_gap={self.config['excessive_merge_gap_s']}s")

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

        # Convert string timestamps to relative float seconds so that
        # anomaly period start_timestamp / end_timestamp are proper numbers.
        from datetime import datetime

        def _parse_ts(ts_str):
            s = str(ts_str)
            for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S',
                        '%H:%M:%S.%f', '%H:%M:%S'):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            return None

        first_dt = _parse_ts(normalized_frames[0]['timestamp'])
        if first_dt is not None:
            for frame in normalized_frames:
                dt = _parse_ts(frame['timestamp'])
                frame['timestamp'] = round((dt - first_dt).total_seconds(), 3) if dt else 0.0

        # Step 3: Calculate kinematics
        kinematics_data = self.calculate_wrist_kinematics(normalized_frames)
        print(f"Calculated kinematics for {len(kinematics_data)} frames")

        # Step 4: Generate visualization
        visualization_path = self.visualize_wrist_kinematics(kinematics_data, recording_id)

        # Step 5: Detect anomalies
        anomalies = self.detect_movement_anomalies(kinematics_data)

        # Step 6: Segmentation via segmentation_ms
        pelt_segmentation = self.call_segmentation(kinematics_data, fps, recording_id)

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
            'segmentation': pelt_segmentation,
            'message': 'Arm movement analysis completed successfully.'
        }
