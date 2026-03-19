import math
from pathlib import Path
from typing import Dict, Any, Optional, List

import matplotlib
import numpy as np
from django.conf import settings

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .db_connection import get_analysis_by_recording_id


class EyeContactAnalysisService:

    def __init__(self):
        self.config = settings.EYE_CONTACT_ANALYSIS_CONFIG
        print(f"Loaded configuration: {self.config}")

    def get_video_analysis(self, recording_id: int) -> Optional[Dict[str, Any]]:
        return get_analysis_by_recording_id(recording_id)

    def calculate_head_angles(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        landmarks = frame_data.get('landmarks', {})

        # Check required landmarks
        required = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 'left_shoulder', 'right_shoulder']
        if not all(lm in landmarks for lm in required):
            return None

        nose = landmarks['nose']
        left_eye = landmarks['left_eye']
        right_eye = landmarks['right_eye']
        left_ear = landmarks['left_ear']
        right_ear = landmarks['right_ear']
        left_shoulder = landmarks['left_shoulder']
        right_shoulder = landmarks['right_shoulder']

        # Get configuration
        pitch_min = self.config['pitch_min']
        pitch_max = self.config['pitch_max']
        yaw_min = self.config['yaw_min']
        yaw_max = self.config['yaw_max']

        # Get yaw calculation weights
        weight_ear = self.config['yaw_weight_ear_ratio']
        weight_nose_face = self.config['yaw_weight_nose_face']
        weight_nose_shoulder = self.config['yaw_weight_nose_shoulder']

        # --- YAW CALCULATION 1: Ear ratio (pomer vzdialeností k ušiam) ---
        dist_to_left_ear = math.sqrt(
            (nose['x'] - left_ear['x']) ** 2 +
            (nose['y'] - left_ear['y']) ** 2
        )
        dist_to_right_ear = math.sqrt(
            (nose['x'] - right_ear['x']) ** 2 +
            (nose['y'] - right_ear['y']) ** 2
        )

        if dist_to_right_ear > 0:
            ear_ratio = dist_to_left_ear / dist_to_right_ear
        else:
            ear_ratio = 1.0

        if ear_ratio > 0:
            ear_yaw = math.log(ear_ratio) * 50  # Scale factor for sensitivity
        else:
            ear_yaw = 0

        # --- YAW CALCULATION 2: Nose vs face center (nos voči stredu tváre) ---
        face_center_x = (left_eye['x'] + right_eye['x']) / 2
        nose_offset_face_x = nose['x'] - face_center_x
        nose_face_yaw = nose_offset_face_x * 100

        # --- YAW CALCULATION 3: Nose vs shoulder center (nos voči stredu ramien) ---
        shoulder_center_x = (left_shoulder['x'] + right_shoulder['x']) / 2
        nose_offset_shoulder_x = nose['x'] - shoulder_center_x
        nose_shoulder_yaw = nose_offset_shoulder_x * 100

        # --- WEIGHTED AVERAGE of all three yaw calculations ---
        yaw = (
            ear_yaw * weight_ear +
            nose_face_yaw * weight_nose_face +
            nose_shoulder_yaw * weight_nose_shoulder
        )

        # --- BACK-FACING DETECTION ---
        # Calculate center of shoulders in Z-axis
        shoulder_center_z = (left_shoulder['z'] + right_shoulder['z']) / 2

        # If nose is further from camera than shoulders, person is facing backwards
        facing_back = (nose['z'] - shoulder_center_z) > self.config['back_facing_threshold']

        # --- PITCH CALCULATION ---
        eye_level_y = (left_eye['y'] + right_eye['y']) / 2
        nose_offset_y = nose['y'] - eye_level_y
        pitch = -nose_offset_y * 150

        return {
            'yaw': yaw,
            'pitch': pitch,
            'timestamp': frame_data.get('timestamp'),
            'facing_back': facing_back,
            # Debug info
            'yaw_components': {
                'ear_yaw': ear_yaw,
                'nose_face_yaw': nose_face_yaw,
                'nose_shoulder_yaw': nose_shoulder_yaw
            },
            'z_depth': {
                'nose_z': nose['z'],
                'shoulder_center_z': shoulder_center_z,
                'z_diff': nose['z'] - shoulder_center_z
            }
        }

    def build_heatmap(self, angle_data: List[Dict[str, float]], frame_duration: float) -> Dict[str, Any]:
        yaw_min = self.config['yaw_min']
        yaw_max = self.config['yaw_max']
        yaw_bin_size = self.config['yaw_bin_size']

        pitch_min = self.config['pitch_min']
        pitch_max = self.config['pitch_max']
        pitch_bin_size = self.config['pitch_bin_size']

        yaw_bins = np.arange(yaw_min, yaw_max + yaw_bin_size, yaw_bin_size)
        pitch_bins = np.arange(pitch_min, pitch_max + pitch_bin_size, pitch_bin_size)

        n_yaw_bins = len(yaw_bins) - 1
        n_pitch_bins = len(pitch_bins) - 1
        heatmap_counts = np.zeros((n_pitch_bins, n_yaw_bins))

        for frame in angle_data:
            yaw = frame['yaw']
            pitch = frame['pitch']

            # Skip frames where person is facing backwards (yaw is None)
            if yaw is None or pitch is None:
                continue

            yaw_idx = np.digitize(yaw, yaw_bins) - 1
            pitch_idx = np.digitize(pitch, pitch_bins) - 1

            yaw_idx = max(0, min(n_yaw_bins - 1, yaw_idx))
            pitch_idx = max(0, min(n_pitch_bins - 1, pitch_idx))

            heatmap_counts[pitch_idx, yaw_idx] += 1

        heatmap_duration = heatmap_counts * frame_duration

        return {
            'yaw_bins': yaw_bins.tolist(),
            'pitch_bins': pitch_bins.tolist(),
            'duration_matrix': heatmap_duration.tolist(),
            'bin_size': {
                'yaw': yaw_bin_size,
                'pitch': pitch_bin_size
            },
            'shape': {
                'n_yaw_bins': n_yaw_bins,
                'n_pitch_bins': n_pitch_bins
            }
        }

    def detect_looking_away_events(self, angle_data: List[Dict[str, float]], frame_duration: float, fps: float) -> List[Dict[str, Any]]:
        audience_yaw_min = self.config['audience_yaw_min']
        audience_yaw_max = self.config['audience_yaw_max']
        audience_pitch_min = self.config['audience_pitch_min']
        audience_pitch_max = self.config['audience_pitch_max']
        min_duration = self.config['min_looking_away_duration']
        min_frames = max(1, round(min_duration * fps / 1000))

        events = []
        current_streak = []

        for frame in angle_data:
            yaw = frame['yaw']
            pitch = frame['pitch']
            timestamp = frame['timestamp']

            looking_away = (
                yaw < audience_yaw_min or yaw > audience_yaw_max or
                pitch < audience_pitch_min or pitch > audience_pitch_max
            )

            if looking_away:
                current_streak.append({
                    'timestamp': timestamp,
                    'yaw': yaw,
                    'pitch': pitch
                })
            else:
                if len(current_streak) >= min_frames:
                    avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
                    avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)

                    events.append({
                        'start_timestamp': current_streak[0]['timestamp'],
                        'end_timestamp': current_streak[-1]['timestamp'],
                        'duration_frames': len(current_streak),
                        'duration_seconds': len(current_streak) * frame_duration,
                        'avg_yaw': avg_yaw,
                        'avg_pitch': avg_pitch
                    })

                current_streak = []

        if len(current_streak) >= min_frames:
            avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
            avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)

            events.append({
                'start_timestamp': current_streak[0]['timestamp'],
                'end_timestamp': current_streak[-1]['timestamp'],
                'duration_frames': len(current_streak),
                'duration_seconds': len(current_streak) * frame_duration,
                'avg_yaw': avg_yaw,
                'avg_pitch': avg_pitch
            })

        return events

    def detect_staring_events(self, angle_data: List[Dict[str, float]], frame_duration: float, fps: float) -> List[Dict[str, Any]]:
        angle_threshold = self.config['staring_angle_threshold']
        min_duration = self.config['min_staring_time']
        min_frames = max(1, min_duration * fps / 1000)

        events = []
        current_streak = []

        for i, frame in enumerate(angle_data):
            yaw = frame['yaw']
            pitch = frame['pitch']
            timestamp = frame['timestamp']

            if current_streak:
                avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
                avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)

                yaw_diff = abs(yaw - avg_yaw)
                pitch_diff = abs(pitch - avg_pitch)

                if yaw_diff <= angle_threshold and pitch_diff <= angle_threshold:
                    current_streak.append({
                        'timestamp': timestamp,
                        'yaw': yaw,
                        'pitch': pitch
                    })
                else:
                    if len(current_streak) >= min_frames:
                        final_avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
                        final_avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)

                        events.append({
                            'start_timestamp': current_streak[0]['timestamp'],
                            'end_timestamp': current_streak[-1]['timestamp'],
                            'duration_frames': len(current_streak),
                            'duration_seconds': len(current_streak) * frame_duration,
                            'avg_yaw': final_avg_yaw,
                            'avg_pitch': final_avg_pitch
                        })

                    current_streak = [{
                        'timestamp': timestamp,
                        'yaw': yaw,
                        'pitch': pitch
                    }]
            else:
                current_streak.append({
                    'timestamp': timestamp,
                    'yaw': yaw,
                    'pitch': pitch
                })

        if len(current_streak) >= min_frames:
            final_avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
            final_avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)

            events.append({
                'start_timestamp': current_streak[0]['timestamp'],
                'end_timestamp': current_streak[-1]['timestamp'],
                'duration_frames': len(current_streak),
                'duration_seconds': len(current_streak) * frame_duration,
                'avg_yaw': final_avg_yaw,
                'avg_pitch': final_avg_pitch
            })

        return events

    def calculate_statistics(self, angle_data: List[Dict[str, float]],
                           looking_away_events: List[Dict[str, Any]],
                           frame_duration: float) -> Dict[str, Any]:
        total_frames = len(angle_data)
        total_duration = total_frames * frame_duration

        looking_away_frames = sum(event['duration_frames'] for event in looking_away_events)
        looking_away_duration = looking_away_frames * frame_duration

        looking_at_audience_frames = total_frames - looking_away_frames
        looking_at_audience_duration = looking_at_audience_frames * frame_duration

        looking_at_audience_pct = (looking_at_audience_frames / total_frames * 100) if total_frames > 0 else 0
        looking_away_pct = (looking_away_frames / total_frames * 100) if total_frames > 0 else 0

        avg_yaw = sum(f['yaw'] for f in angle_data) / len(angle_data) if angle_data else 0
        avg_pitch = sum(f['pitch'] for f in angle_data) / len(angle_data) if angle_data else 0

        yaw_values = [f['yaw'] for f in angle_data]
        pitch_values = [f['pitch'] for f in angle_data]

        yaw_range = max(yaw_values) - min(yaw_values) if yaw_values else 0
        pitch_range = max(pitch_values) - min(pitch_values) if pitch_values else 0

        return {
            'total_frames': total_frames,
            'total_duration': round(total_duration, 2),
            'looking_at_audience_frames': looking_at_audience_frames,
            'looking_at_audience_duration': round(looking_at_audience_duration, 2),
            'looking_at_audience_percentage': round(looking_at_audience_pct, 2),
            'looking_away_frames': looking_away_frames,
            'looking_away_duration': round(looking_away_duration, 2),
            'looking_away_percentage': round(looking_away_pct, 2),
            'avg_yaw': round(avg_yaw, 2),
            'avg_pitch': round(avg_pitch, 2),
            'yaw_range': round(yaw_range, 2),
            'pitch_range': round(pitch_range, 2),
            'num_looking_away_events': len(looking_away_events)
        }

    def visualize_gaze_heatmap(self, heatmap_data: Dict[str, Any],
                              angle_data: List[Dict[str, float]],
                              recording_id: int,
                              output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        yaw_bins = np.array(heatmap_data['yaw_bins'])
        pitch_bins = np.array(heatmap_data['pitch_bins'])
        duration_matrix = np.array(heatmap_data['duration_matrix'])

        frame_indices = [i for i in range(len(angle_data))]
        yaw_values = [frame['yaw'] for frame in angle_data]
        pitch_values = [frame['pitch'] for frame in angle_data]
        facing_back_values = [1 if frame.get('facing_back', False) else 0 for frame in angle_data]

        # Extract Z-depth values for debugging
        nose_z_values = [frame.get('z_depth', {}).get('nose_z', 0) for frame in angle_data]
        shoulder_z_values = [frame.get('z_depth', {}).get('shoulder_center_z', 0) for frame in angle_data]
        z_diff_values = [frame.get('z_depth', {}).get('z_diff', 0) for frame in angle_data]

        fig = plt.figure(figsize=(16, 16))
        gs = fig.add_gridspec(4, 1, height_ratios=[2, 1, 1, 1], hspace=0.3)

        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax3 = fig.add_subplot(gs[2])
        ax4 = fig.add_subplot(gs[3])

        extent = [yaw_bins[0], yaw_bins[-1], pitch_bins[0], pitch_bins[-1]]
        im = ax1.imshow(duration_matrix, extent=extent, origin='lower',
                       cmap='hot', aspect='auto', interpolation='bilinear')

        audience_yaw_min = self.config['audience_yaw_min']
        audience_yaw_max = self.config['audience_yaw_max']
        audience_pitch_min = self.config['audience_pitch_min']
        audience_pitch_max = self.config['audience_pitch_max']

        rect = plt.Rectangle(
            (audience_yaw_min, audience_pitch_min),
            audience_yaw_max - audience_yaw_min,
            audience_pitch_max - audience_pitch_min,
            fill=False, edgecolor='lime', linewidth=3, label='Audience Zone'
        )
        ax1.add_patch(rect)

        ax1.axhline(0, color='white', linestyle='--', alpha=0.5, linewidth=1)
        ax1.axvline(0, color='white', linestyle='--', alpha=0.5, linewidth=1)

        ax1.set_xlabel('Yaw (°) - Left/Right', fontsize=12)
        ax1.set_ylabel('Pitch (°) - Down/Up', fontsize=12)
        ax1.set_title(f'Gaze Heatmap - Recording {recording_id}', fontsize=14, fontweight='bold')

        cbar = plt.colorbar(im, ax=ax1)
        cbar.set_label('Time (seconds)', fontsize=10)

        ax1.legend(loc='upper right', fontsize=10)

        ax1.grid(True, alpha=0.2, color='white')

        ax2.plot(frame_indices, yaw_values, color='blue', linewidth=1, label='Yaw')
        ax2.axhline(audience_yaw_min, color='lime', linestyle='--', linewidth=2, label=f'Audience Min ({audience_yaw_min}°)')
        ax2.axhline(audience_yaw_max, color='lime', linestyle='--', linewidth=2, label=f'Audience Max ({audience_yaw_max}°)')
        ax2.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax2.set_xlabel('Frame Index', fontsize=12)
        ax2.set_ylabel('Yaw (°)', fontsize=12)
        ax2.set_title('Yaw Angle Over Time', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3)

        ax3.plot(frame_indices, pitch_values, color='red', linewidth=1, label='Pitch')
        ax3.axhline(audience_pitch_min, color='lime', linestyle='--', linewidth=2, label=f'Audience Min ({audience_pitch_min}°)')
        ax3.axhline(audience_pitch_max, color='lime', linestyle='--', linewidth=2, label=f'Audience Max ({audience_pitch_max}°)')
        ax3.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax3.set_xlabel('Frame Index', fontsize=12)
        ax3.set_ylabel('Pitch (°)', fontsize=12)
        ax3.set_title('Pitch Angle Over Time', fontsize=12, fontweight='bold')
        ax3.legend(loc='upper right', fontsize=9)
        ax3.grid(True, alpha=0.3)

        # Fourth graph: Z-Depth Analysis
        ax4.plot(frame_indices, nose_z_values, color='blue', linewidth=1.5, label='Nose Z')
        ax4.plot(frame_indices, shoulder_z_values, color='green', linewidth=1.5, label='Shoulder Center Z')
        ax4.plot(frame_indices, z_diff_values, color='orange', linewidth=1.5, label='Z Difference')

        # Show threshold line for back-facing detection
        ax4.axhline(-0.1, color='red', linestyle='--', linewidth=2, label='Back-Facing Threshold (-0.1)')
        ax4.axhline(0, color='gray', linestyle=':', alpha=0.5)

        # Mark back-facing regions with red background
        for i, is_back in enumerate(facing_back_values):
            if is_back:
                ax4.axvspan(i - 0.5, i + 0.5, color='red', alpha=0.1)

        ax4.set_xlabel('Frame Index', fontsize=12)
        ax4.set_ylabel('Z-Coordinate', fontsize=12)
        ax4.set_title('Z-Depth Analysis (Back-Facing Detection)', fontsize=12, fontweight='bold')
        ax4.legend(loc='upper right', fontsize=9)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = output_dir / f'gaze_heatmap_{recording_id}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Gaze heatmap saved to: {output_path}")

    def analyze_eye_contact(self, recording_id: int) -> Dict[str, Any]:
        print(f"Analyzing eye contact for recording ID: {recording_id}")

        analysis_data = self.get_video_analysis(recording_id)

        if not analysis_data:
            return {'success': False, 'error': 'Video analysis not found'}

        total_frames = len(analysis_data.get('data', []))
        print(f"Retrieved {total_frames} frames from database")

        angle_data = []
        for frame in analysis_data.get('data', []):
            angles = self.calculate_head_angles(frame)
            if angles:
                angle_data.append(angles)

        if not angle_data:
            return {'success': False, 'error': 'No frames with sufficient landmarks for angle calculation'}

        print(f"Calculated angles for {len(angle_data)} frames")

        from datetime import datetime

        def parse_timestamp(ts_str):
            try:
                return datetime.fromisoformat(ts_str)
            except ValueError:
                t = datetime.strptime(ts_str, '%H:%M:%S.%f').time() if '.' in ts_str else datetime.strptime(ts_str, '%H:%M:%S').time()
                return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000

        first_ts = parse_timestamp(angle_data[0]['timestamp'])
        last_ts = parse_timestamp(angle_data[-1]['timestamp'])

        if isinstance(first_ts, datetime):
            total_duration = (last_ts - first_ts).total_seconds()
        else:
            total_duration = last_ts - first_ts

        fps = analysis_data['fps']
        frame_duration = 1.0 / fps
        print(f"Calculated FPS: {fps:.2f} (frame duration: {frame_duration*1000:.2f}ms)")

        heatmap_data = self.build_heatmap(angle_data, frame_duration)
        print(f"Built heatmap with {heatmap_data['shape']['n_yaw_bins']}x{heatmap_data['shape']['n_pitch_bins']} bins")

        looking_away_events = self.detect_looking_away_events(angle_data, frame_duration, analysis_data['fps'])
        print(f"Detected {len(looking_away_events)} looking away events")

        staring_events = self.detect_staring_events(angle_data, frame_duration, analysis_data['fps'])
        print(f"Detected {len(staring_events)} staring events")

        statistics = self.calculate_statistics(angle_data, looking_away_events, frame_duration)

        if settings.DEBUG:
            self.visualize_gaze_heatmap(heatmap_data, angle_data, recording_id)

        return {
            'success': True,
            'recording_id': recording_id,
            'total_frames': total_frames,
            'analyzed_frames': len(angle_data),
            'heatmap': heatmap_data,
            'statistics': statistics,
            'looking_away_events': looking_away_events,
            'staring_events': staring_events,
            'audience_zone_thresholds': {
                'yaw_min': self.config['audience_yaw_min'],
                'yaw_max': self.config['audience_yaw_max'],
                'pitch_min': self.config['audience_pitch_min'],
                'pitch_max': self.config['audience_pitch_max']
            },
            'staring_thresholds': {
                'angle_threshold': self.config['staring_angle_threshold'],
                'min_frames': self.config['min_staring_time']
            },
            'message': 'Eye contact analysis completed successfully.'
        }
