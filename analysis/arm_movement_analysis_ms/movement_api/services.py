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
                                   output_dir: Optional[str] = None,
                                   anomalies: Optional[Dict[str, Any]] = None,
                                   thresholds: Optional[Dict[str, float]] = None) -> str:
        from matplotlib.patches import Patch

        if output_dir is None:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamps = []
        left_velocities = []
        right_velocities = []

        for frame in kinematics_data:
            timestamps.append(frame.get('timestamp', 0))
            left_velocities.append(frame['left_wrist']['velocity'] if frame.get('left_wrist') else None)
            right_velocities.append(frame['right_wrist']['velocity'] if frame.get('right_wrist') else None)

        # Rolling average (0.5 s window at 30 fps)
        win = 15
        def _rolling(data, w):
            out = []
            half = w // 2
            for i in range(len(data)):
                vals = [v for v in data[max(0, i - half):i + half + 1] if v is not None]
                out.append(sum(vals) / len(vals) if vals else None)
            return out

        left_smooth = _rolling(left_velocities, win)
        right_smooth = _rolling(right_velocities, win)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle(f'Wrist Movement Analysis – Recording {recording_id}',
                     fontsize=16, fontweight='bold')

        def _shade(ax):
            if not anomalies:
                return
            for p in anomalies.get('no_movement_periods', []):
                ax.axvspan(p['start_timestamp'], p['end_timestamp'], alpha=0.15, color='gray', zorder=0)
            for p in anomalies.get('excessive_movement_periods', []):
                ax.axvspan(p['start_timestamp'], p['end_timestamp'], alpha=0.20, color='tomato', zorder=0)

        def _threshold_lines(ax):
            if not thresholds:
                return
            ax.axhline(y=thresholds['no_movement'], color='dimgray', linestyle='--', linewidth=1.2,
                       label=f"No-movement thr. ({thresholds['no_movement']:.3f})")
            ax.axhline(y=thresholds['excessive'], color='darkorange', linestyle='--', linewidth=1.2,
                       label=f"Excessive thr. ({thresholds['excessive']:.3f})")

        def _legend_with_patches(ax):
            handles, labels = ax.get_legend_handles_labels()
            if anomalies:
                handles += [Patch(facecolor='gray', alpha=0.4), Patch(facecolor='tomato', alpha=0.4)]
                labels += ['No-movement period', 'Excessive movement period']
            ax.legend(handles=handles, labels=labels, loc='upper right', fontsize=9)

        # — Subplot 1: raw velocity —
        ax1.plot(timestamps, left_velocities, color='steelblue', linewidth=1, alpha=0.45, label='Left wrist')
        ax1.plot(timestamps, right_velocities, color='tomato', linewidth=1, alpha=0.45, label='Right wrist')
        _shade(ax1)
        _threshold_lines(ax1)
        ax1.set_xlabel('Time (s)', fontsize=12)
        ax1.set_ylabel('Velocity (normalized units/frame)', fontsize=12)
        ax1.set_title('Wrist Velocity', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        left_vals = [v for v in left_velocities if v is not None]
        right_vals = [v for v in right_velocities if v is not None]
        if left_vals:
            ax1.text(0.02, 0.98,
                     f'Left  avg: {sum(left_vals)/len(left_vals):.4f}\nLeft  max: {max(left_vals):.4f}',
                     transform=ax1.transAxes, fontsize=9, va='top',
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        if right_vals:
            ax1.text(0.98, 0.98,
                     f'Right avg: {sum(right_vals)/len(right_vals):.4f}\nRight max: {max(right_vals):.4f}',
                     transform=ax1.transAxes, fontsize=9, va='top', ha='right',
                     bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
        _legend_with_patches(ax1)

        # — Subplot 2: rolling average trend —
        ax2.plot(timestamps, left_smooth, color='steelblue', linewidth=2, label='Left wrist (smoothed)')
        ax2.plot(timestamps, right_smooth, color='tomato', linewidth=2, label='Right wrist (smoothed)')
        _shade(ax2)
        _threshold_lines(ax2)
        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Velocity (rolling avg, normalized)', fontsize=12)
        ax2.set_title(f'Movement Trend  (rolling average, window = {win} frames)',
                      fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        _legend_with_patches(ax2)

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

        Excessive movement: per-hand, applied on a rolling-average signal so
        that single-frame spikes are ignored.  Nearby events from the same hand
        are merged to consolidate a back-and-forth swing into one period.
        """
        no_movement_threshold = self.config['no_movement_velocity_threshold']
        z_score_k = self.config['excessive_z_score_k']
        win = self.config['excessive_rolling_window']
        min_frames = self.config['min_consecutive_frames']
        merge_gap_s = self.config['excessive_merge_gap_s']

        # Per-wrist rolling average (same window used in visualization)
        left_raw = [f['left_wrist']['velocity'] if f.get('left_wrist') else None for f in kinematics_data]
        right_raw = [f['right_wrist']['velocity'] if f.get('right_wrist') else None for f in kinematics_data]

        def _rolling(data, w):
            half = w // 2
            out = []
            for i in range(len(data)):
                vals = [v for v in data[max(0, i - half):i + half + 1] if v is not None]
                out.append(sum(vals) / len(vals) if vals else None)
            return out

        left_smooth = _rolling(left_raw, win)
        right_smooth = _rolling(right_raw, win)

        # Z-score threshold computed from the smoothed distribution
        all_smooth = [v for v in left_smooth + right_smooth if v is not None]
        if all_smooth:
            vel_mean = sum(all_smooth) / len(all_smooth)
            vel_std = math.sqrt(sum((v - vel_mean) ** 2 for v in all_smooth) / len(all_smooth))
            excessive_movement_threshold = vel_mean + z_score_k * vel_std
        else:
            vel_mean, vel_std = 0.0, 0.0
            excessive_movement_threshold = 0.15

        print(f"Detecting movement anomalies with thresholds:")
        print(f"  No movement: all visible wrists velocity < {no_movement_threshold}, min_frames={min_frames}")
        print(f"  Excessive (rolling window={win}, z-score): mean={vel_mean:.4f} + {z_score_k}*std({vel_std:.4f}) "
              f"= {excessive_movement_threshold:.4f}, merge_gap={merge_gap_s}s")

        no_movement_periods = []
        raw_left_excessive = []
        raw_right_excessive = []

        no_movement_streak = []
        left_excessive_streak = []
        right_excessive_streak = []

        for i, frame in enumerate(kinematics_data):
            timestamp = frame.get('timestamp')
            left_vel_raw = frame['left_wrist']['velocity'] if frame.get('left_wrist') else None
            right_vel_raw = frame['right_wrist']['velocity'] if frame.get('right_wrist') else None
            left_vel_s = left_smooth[i]
            right_vel_s = right_smooth[i]

            # ── Bilateral no-movement (raw — sensitive to any motion) ──────────
            active_vels = [v for v in [left_vel_raw, right_vel_raw] if v is not None]
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

            # ── Per-hand excessive movement (smoothed — stable, no min-frames needed) ──
            if left_vel_s is not None:
                if left_vel_s > excessive_movement_threshold:
                    left_excessive_streak.append(timestamp)
                else:
                    if left_excessive_streak:
                        raw_left_excessive.append({
                            'wrist': 'left',
                            'start_timestamp': left_excessive_streak[0],
                            'end_timestamp': left_excessive_streak[-1],
                            'duration_frames': len(left_excessive_streak)
                        })
                    left_excessive_streak = []

            if right_vel_s is not None:
                if right_vel_s > excessive_movement_threshold:
                    right_excessive_streak.append(timestamp)
                else:
                    if right_excessive_streak:
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
        if left_excessive_streak:
            raw_left_excessive.append({
                'wrist': 'left',
                'start_timestamp': left_excessive_streak[0],
                'end_timestamp': left_excessive_streak[-1],
                'duration_frames': len(left_excessive_streak)
            })
        if right_excessive_streak:
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
                'excessive_z_score_k': z_score_k,
                'excessive_rolling_window': win,
                'velocity_mean': vel_mean,
                'velocity_std': vel_std,
                'min_consecutive_frames': min_frames,
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
        self.config['excessive_merge_gap_s'] = self.config['excessive_merge_gap_ms'] / 1000.0
        print(f"Using fps={fps}: min_consecutive_frames={self.config['min_consecutive_frames']}, "
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

        # Step 4: Detect anomalies (must run before visualization to get computed thresholds)
        anomalies = self.detect_movement_anomalies(kinematics_data)

        # Step 5: Generate visualization with thresholds and anomaly regions
        viz_thresholds = {
            'no_movement': anomalies['thresholds_used']['no_movement_velocity_threshold'],
            'excessive': anomalies['thresholds_used']['excessive_movement_velocity_threshold'],
        }
        visualization_path = self.visualize_wrist_kinematics(
            kinematics_data, recording_id, anomalies=anomalies, thresholds=viz_thresholds
        )

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
