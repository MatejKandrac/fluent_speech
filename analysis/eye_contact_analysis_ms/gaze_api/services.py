import math
from pathlib import Path
from typing import Dict, Any, Optional, List

import matplotlib
import numpy as np
import requests
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

        required = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 'left_shoulder', 'right_shoulder']
        if not all(lm in landmarks for lm in required):
            return None

        nose = landmarks['nose']
        left_ear = landmarks['left_ear']
        right_ear = landmarks['right_ear']
        left_shoulder = landmarks['left_shoulder']
        right_shoulder = landmarks['right_shoulder']

        # --- BACK-FACING DETECTION ---
        shoulder_center_z = (left_shoulder['z'] + right_shoulder['z']) / 2
        facing_back = (nose['z'] - shoulder_center_z) > self.config['back_facing_threshold']

        # --- YAW CALCULATION (rotation-invariant) ---
        # Decompose the interaural axis (3D ear-to-ear vector) into:
        #   • its magnitude projected onto the image plane: sqrt(Δx² + Δy²)
        #   • its depth component: Δz
        # atan2 of these gives yaw — the angle between the interaural axis and its
        # image-plane projection. Using the 2D Euclidean distance (rather than just
        # Δx) makes this work regardless of camera roll or portrait/landscape
        # orientation, which is essential since MediaPipe landmarks come in raw
        # image coordinates. Result naturally bounded to (-90°, +90°), monotonic
        # across the full range, no calibration needed.
        #
        # Sign convention: MediaPipe z grows away from camera. When the subject
        # turns to their right, the right ear moves away (right.z > left.z), so
        # Δz = right.z - left.z > 0 → positive yaw. Matches prior convention.
        delta_x_ear = right_ear['x'] - left_ear['x']
        delta_y_ear = right_ear['y'] - left_ear['y']
        ear_image_dist = math.sqrt(delta_x_ear ** 2 + delta_y_ear ** 2)
        delta_z_ear = right_ear['z'] - left_ear['z']
        yaw_raw = math.degrees(math.atan2(delta_z_ear, ear_image_dist))

        # --- PITCH CALCULATION (rotation-independent) ---
        ear_level_x = (left_ear['x'] + right_ear['x']) / 2
        ear_level_y = (left_ear['y'] + right_ear['y']) / 2
        shoulder_vec_x = right_shoulder['x'] - left_shoulder['x']
        shoulder_vec_y = right_shoulder['y'] - left_shoulder['y']
        shoulder_len = math.sqrt(shoulder_vec_x ** 2 + shoulder_vec_y ** 2)

        nose_ear_vertical = 0.0
        face_radius = 0.0
        if shoulder_len > 0.001:
            su_x = shoulder_vec_x / shoulder_len
            su_y = shoulder_vec_y / shoulder_len
            bu_x = -su_y
            bu_y = su_x

            nex = nose['x'] - ear_level_x
            ney = nose['y'] - ear_level_y
            nose_ear_vertical = nex * bu_x + ney * bu_y

            inter_ear_dist = math.sqrt(
                (right_ear['x'] - left_ear['x']) ** 2 +
                (right_ear['y'] - left_ear['y']) ** 2
            )
            face_radius = inter_ear_dist / 2 if inter_ear_dist > 0.001 else shoulder_len * 0.15
            pitch = math.degrees(math.atan2(nose_ear_vertical, face_radius))
        else:
            pitch = 0.0

        pitch = max(-90.0, min(90.0, pitch + self.config['pitch_bias']))

        # When facing backwards yaw/pitch are geometrically meaningless —
        # nullify so downstream detection and visualisation skip these frames.
        yaw = None if facing_back else yaw_raw
        if facing_back:
            pitch = None

        return {
            'yaw': yaw,
            'yaw_raw': yaw,
            'pitch': pitch,
            'timestamp': frame_data.get('timestamp'),
            'facing_back': facing_back,
            'delta_z_ear': delta_z_ear,
            'ear_image_dist': ear_image_dist,
            'z_depth': {
                'nose_z': nose['z'],
                'shoulder_center_z': shoulder_center_z,
                'z_diff': nose['z'] - shoulder_center_z,
            },
            'nose': {
                'x': nose['x'],
                'y': nose['y'],
                'z': nose['z'],
            },
            'pitch_debug': {
                'nose_ear_vertical': nose_ear_vertical,
                'face_radius': face_radius,
                'pitch_ratio': (nose_ear_vertical / face_radius) if face_radius > 0.001 else 0,
                'shoulder_len': shoulder_len,
            },
        }

    def smooth_yaw(self, angle_data: List[Dict[str, Any]]) -> None:
        # Median-filter Δz across frames, then recompute yaw. Smoothing the depth
        # signal (the noisy input) rather than the yaw output keeps the geometry
        # honest at all angles, where atan2 is non-linear w.r.t. Δz.
        window = max(1, int(self.config.get('yaw_smoothing_window', 5)))
        if window <= 1 or not angle_data:
            return

        half = window // 2
        n = len(angle_data)
        delta_z_series = [f['delta_z_ear'] for f in angle_data]

        for i, frame in enumerate(angle_data):
            if frame['yaw'] is None:
                continue
            lo = max(0, i - half)
            hi = min(n, i + half + 1)
            window_vals = [
                delta_z_series[j] for j in range(lo, hi)
                if angle_data[j]['yaw'] is not None
            ]
            if not window_vals:
                continue
            sorted_vals = sorted(window_vals)
            smoothed_dz = sorted_vals[len(sorted_vals) // 2]
            denom = frame['ear_image_dist']
            yaw_smoothed = math.degrees(math.atan2(smoothed_dz, denom))
            frame['yaw'] = max(-90.0, min(90.0, yaw_smoothed))

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
                'pitch': pitch_bin_size,
            },
            'shape': {
                'n_yaw_bins': n_yaw_bins,
                'n_pitch_bins': n_pitch_bins,
            },
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

        def flush():
            if len(current_streak) >= min_frames:
                avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
                avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)
                events.append({
                    'start_timestamp': current_streak[0]['timestamp'],
                    'end_timestamp': current_streak[-1]['timestamp'],
                    'duration_frames': len(current_streak),
                    'duration_seconds': len(current_streak) * frame_duration,
                    'avg_yaw': avg_yaw,
                    'avg_pitch': avg_pitch,
                })

        for frame in angle_data:
            yaw = frame['yaw']
            pitch = frame['pitch']
            timestamp = frame['timestamp']

            if yaw is None or pitch is None:
                flush()
                current_streak = []
                continue

            looking_away = (
                yaw < audience_yaw_min or yaw > audience_yaw_max or
                pitch < audience_pitch_min or pitch > audience_pitch_max
            )

            if looking_away:
                current_streak.append({'timestamp': timestamp, 'yaw': yaw, 'pitch': pitch})
            else:
                flush()
                current_streak = []

        flush()
        return events

    def detect_staring_events(self, angle_data: List[Dict[str, float]], frame_duration: float, fps: float) -> List[Dict[str, Any]]:
        angle_threshold = self.config['staring_angle_threshold']
        min_duration = self.config['min_staring_time']
        min_frames = max(1, min_duration * fps / 1000)

        events = []
        current_streak = []

        def flush():
            if len(current_streak) >= min_frames:
                avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
                avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)
                events.append({
                    'start_timestamp': current_streak[0]['timestamp'],
                    'end_timestamp': current_streak[-1]['timestamp'],
                    'duration_frames': len(current_streak),
                    'duration_seconds': len(current_streak) * frame_duration,
                    'avg_yaw': avg_yaw,
                    'avg_pitch': avg_pitch,
                })

        for frame in angle_data:
            yaw = frame['yaw']
            pitch = frame['pitch']
            timestamp = frame['timestamp']

            if yaw is None or pitch is None:
                flush()
                current_streak = []
                continue

            if current_streak:
                avg_yaw = sum(f['yaw'] for f in current_streak) / len(current_streak)
                avg_pitch = sum(f['pitch'] for f in current_streak) / len(current_streak)
                if abs(yaw - avg_yaw) <= angle_threshold and abs(pitch - avg_pitch) <= angle_threshold:
                    current_streak.append({'timestamp': timestamp, 'yaw': yaw, 'pitch': pitch})
                else:
                    flush()
                    current_streak = [{'timestamp': timestamp, 'yaw': yaw, 'pitch': pitch}]
            else:
                current_streak.append({'timestamp': timestamp, 'yaw': yaw, 'pitch': pitch})

        flush()
        return events

    def detect_back_facing_events(self, angle_data: List[Dict[str, float]], frame_duration: float, fps: float) -> List[Dict[str, Any]]:
        min_duration = self.config.get('min_back_facing_duration', 300)
        min_frames = max(1, round(min_duration * fps / 1000))

        events = []
        current_streak = []

        for frame in angle_data:
            if frame.get('facing_back', False):
                current_streak.append(frame)
            else:
                if len(current_streak) >= min_frames:
                    events.append({
                        'start_timestamp': current_streak[0]['timestamp'],
                        'end_timestamp': current_streak[-1]['timestamp'],
                        'duration_frames': len(current_streak),
                        'duration_seconds': len(current_streak) * frame_duration,
                    })
                current_streak = []

        if len(current_streak) >= min_frames:
            events.append({
                'start_timestamp': current_streak[0]['timestamp'],
                'end_timestamp': current_streak[-1]['timestamp'],
                'duration_frames': len(current_streak),
                'duration_seconds': len(current_streak) * frame_duration,
            })

        return events

    def calculate_statistics(self, angle_data: List[Dict[str, float]],
                           looking_away_events: List[Dict[str, Any]],
                           frame_duration: float) -> Dict[str, Any]:
        total_frames = len(angle_data)
        total_duration = total_frames * frame_duration

        back_facing_frames = sum(1 for f in angle_data if f.get('facing_back', False))
        back_facing_duration = back_facing_frames * frame_duration

        looking_away_frames = sum(event['duration_frames'] for event in looking_away_events)
        looking_away_duration = looking_away_frames * frame_duration

        active_frames = total_frames - back_facing_frames
        looking_at_audience_frames = max(0, active_frames - looking_away_frames)
        looking_at_audience_duration = looking_at_audience_frames * frame_duration

        looking_at_audience_pct = (looking_at_audience_frames / active_frames * 100) if active_frames > 0 else 0
        looking_away_pct = (looking_away_frames / active_frames * 100) if active_frames > 0 else 0

        valid_frames = [f for f in angle_data if f['yaw'] is not None and f['pitch'] is not None]
        yaw_values = [f['yaw'] for f in valid_frames]
        pitch_values = [f['pitch'] for f in valid_frames]
        avg_yaw = sum(yaw_values) / len(yaw_values) if yaw_values else 0
        avg_pitch = sum(pitch_values) / len(pitch_values) if pitch_values else 0
        yaw_range = max(yaw_values) - min(yaw_values) if yaw_values else 0
        pitch_range = max(pitch_values) - min(pitch_values) if pitch_values else 0

        return {
            'total_frames': total_frames,
            'total_duration': round(total_duration, 2),
            'back_facing_frames': back_facing_frames,
            'back_facing_duration': round(back_facing_duration, 2),
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
            'num_looking_away_events': len(looking_away_events),
        }

    def visualize_gaze_heatmap(self, heatmap_data: Dict[str, Any],
                              angle_data: List[Dict[str, float]],
                              recording_id: int,
                              frame_duration: float,
                              output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        yaw_bins = np.array(heatmap_data['yaw_bins'])
        pitch_bins = np.array(heatmap_data['pitch_bins'])
        duration_matrix = np.array(heatmap_data['duration_matrix'])

        times = [i * frame_duration for i in range(len(angle_data))]
        yaw_values = [frame['yaw'] if frame['yaw'] is not None else float('nan') for frame in angle_data]
        yaw_raw_values = [frame.get('yaw_raw') if frame.get('yaw_raw') is not None else float('nan') for frame in angle_data]
        pitch_values = [frame['pitch'] if frame['pitch'] is not None else float('nan') for frame in angle_data]
        facing_back_values = [1 if frame.get('facing_back', False) else 0 for frame in angle_data]
        delta_z_values = [frame.get('delta_z_ear', 0.0) for frame in angle_data]

        nose_z_values = [frame.get('z_depth', {}).get('nose_z', 0) for frame in angle_data]
        shoulder_z_values = [frame.get('z_depth', {}).get('shoulder_center_z', 0) for frame in angle_data]
        z_diff_values = [frame.get('z_depth', {}).get('z_diff', 0) for frame in angle_data]

        fig = plt.figure(figsize=(16, 16))
        gs = fig.add_gridspec(4, 1, height_ratios=[2, 1, 1, 1], hspace=0.35)

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

        ax2.plot(times, yaw_raw_values, color='lightsteelblue', linewidth=1, alpha=0.6, label='Yaw (raw)')
        ax2.plot(times, yaw_values, color='blue', linewidth=1.2, label='Yaw (smoothed)')
        ax2.axhline(audience_yaw_min, color='lime', linestyle='--', linewidth=2, label=f'Audience Min ({audience_yaw_min}°)')
        ax2.axhline(audience_yaw_max, color='lime', linestyle='--', linewidth=2, label=f'Audience Max ({audience_yaw_max}°)')
        ax2.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax2.set_xlabel('Time (s)', fontsize=12)
        ax2.set_ylabel('Yaw (°)', fontsize=12)
        ax2.set_title('Yaw Angle Over Time (atan2 of ear vector)', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3)

        ax3.plot(times, pitch_values, color='red', linewidth=1, label='Pitch')
        ax3.axhline(audience_pitch_min, color='lime', linestyle='--', linewidth=2, label=f'Audience Min ({audience_pitch_min}°)')
        ax3.axhline(audience_pitch_max, color='lime', linestyle='--', linewidth=2, label=f'Audience Max ({audience_pitch_max}°)')
        ax3.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax3.set_xlabel('Time (s)', fontsize=12)
        ax3.set_ylabel('Pitch (°)', fontsize=12)
        ax3.set_title('Pitch Angle Over Time', fontsize=12, fontweight='bold')
        ax3.legend(loc='upper right', fontsize=9)
        ax3.grid(True, alpha=0.3)

        ax4.plot(times, nose_z_values, color='blue', linewidth=1.5, label='Nose Z')
        ax4.plot(times, shoulder_z_values, color='green', linewidth=1.5, label='Shoulder Center Z')
        ax4.plot(times, z_diff_values, color='orange', linewidth=1.5, label='Z Difference')
        ax4.axhline(self.config['back_facing_threshold'], color='red', linestyle='--', linewidth=2,
                    label=f'Back-Facing Threshold ({self.config["back_facing_threshold"]})')
        ax4.axhline(0, color='gray', linestyle=':', alpha=0.5)

        for i, is_back in enumerate(facing_back_values):
            if is_back:
                t = i * frame_duration
                ax4.axvspan(t - frame_duration / 2, t + frame_duration / 2, color='red', alpha=0.1)

        ax4.set_xlabel('Time (s)', fontsize=12)
        ax4.set_ylabel('Z-Coordinate', fontsize=12)
        ax4.set_title('Z-Depth Analysis (Back-Facing Detection)', fontsize=12, fontweight='bold')
        ax4.legend(loc='upper right', fontsize=9)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = output_dir / f'gaze_heatmap_{recording_id}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Gaze heatmap saved to: {output_path}")

    def call_segmentation(self, angle_data: List[Dict[str, float]], fps: float, recording_id: int) -> dict:
        sensitivity = self.config['eye_segmentation_sensitivity']
        frames_per_second = max(1, round(fps))

        aud_yaw_min = self.config['audience_yaw_min']
        aud_yaw_max = self.config['audience_yaw_max']
        aud_pitch_min = self.config['audience_pitch_min']
        aud_pitch_max = self.config['audience_pitch_max']

        series = []
        for i in range(0, len(angle_data), frames_per_second):
            window = angle_data[i:i + frames_per_second]
            if not window:
                continue
            outside = sum(
                1 for f in window
                if f['yaw'] is None or f['pitch'] is None or
                   f['yaw'] < aud_yaw_min or f['yaw'] > aud_yaw_max or
                   f['pitch'] < aud_pitch_min or f['pitch'] > aud_pitch_max
            )
            t = round(i / fps, 3)
            series.append({'time': t, 'value': round(outside / len(window), 4)})

        if len(series) < 2:
            return {'success': False, 'error': 'Not enough data for segmentation'}

        url = f"{settings.SEGMENTATION_SERVICE_URL}/api/v1/segment/"
        payload = {
            'series': series,
            'methods': ['mean'],
            'sensitivity': sensitivity,
            'label': f'eye_{recording_id}',
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Segmentation service error: {e}")
            return {'success': False, 'error': str(e)}

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
            s = str(ts_str)
            for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S',
                        '%H:%M:%S.%f', '%H:%M:%S'):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unrecognised timestamp format: {ts_str!r}")

        first_ts = parse_timestamp(angle_data[0]['timestamp'])
        last_ts = parse_timestamp(angle_data[-1]['timestamp'])

        if isinstance(first_ts, datetime):
            total_duration = (last_ts - first_ts).total_seconds()
        else:
            total_duration = last_ts - first_ts

        for frame in angle_data:
            ts = parse_timestamp(frame['timestamp'])
            if isinstance(first_ts, datetime):
                frame['timestamp'] = round((ts - first_ts).total_seconds(), 3)
            else:
                frame['timestamp'] = round(ts - first_ts, 3)

        fps = analysis_data['fps']
        frame_duration = 1.0 / fps
        print(f"Calculated FPS: {fps:.2f} (frame duration: {frame_duration*1000:.2f}ms)")

        # Median-smooth Δz across frames before recomputing yaw, suppressing
        # MediaPipe z-noise without producing the plateau artifacts that the
        # old hold-last-value strategy did.
        self.smooth_yaw(angle_data)

        # Per-video pitch normalization: subtract the median pitch so that the
        # person's typical gaze direction maps to 0°.  The raw pitch is biased
        # downward by a variable amount on every video because MediaPipe places
        # the nose below the ears in 2-D image coordinates even when looking
        # straight ahead, and the offset depends on camera height, distance, and
        # individual anatomy.  Yaw does not need this — atan2 of the ear depth
        # vector is already zero-centred by construction.
        valid_pitches = [f['pitch'] for f in angle_data if f['pitch'] is not None]
        if valid_pitches:
            median_pitch = sorted(valid_pitches)[len(valid_pitches) // 2]
            print(f"Pitch median offset: {median_pitch:.2f}° → subtracting from all frames")
            for frame in angle_data:
                if frame['pitch'] is not None:
                    frame['pitch'] = max(-90.0, min(90.0, frame['pitch'] - median_pitch))

        heatmap_data = self.build_heatmap(angle_data, frame_duration)
        print(f"Built heatmap with {heatmap_data['shape']['n_yaw_bins']}x{heatmap_data['shape']['n_pitch_bins']} bins")

        looking_away_events = self.detect_looking_away_events(angle_data, frame_duration, analysis_data['fps'])
        print(f"Detected {len(looking_away_events)} looking away events")

        staring_events = self.detect_staring_events(angle_data, frame_duration, analysis_data['fps'])
        print(f"Detected {len(staring_events)} staring events")

        back_facing_events = self.detect_back_facing_events(angle_data, frame_duration, analysis_data['fps'])
        print(f"Detected {len(back_facing_events)} back-facing events")

        statistics = self.calculate_statistics(angle_data, looking_away_events, frame_duration)

        if settings.DEBUG:
            self.visualize_gaze_heatmap(heatmap_data, angle_data, recording_id, frame_duration)

        segmentation = self.call_segmentation(angle_data, fps, recording_id)

        return {
            'success': True,
            'recording_id': recording_id,
            'total_frames': total_frames,
            'analyzed_frames': len(angle_data),
            'heatmap': heatmap_data,
            'statistics': statistics,
            'looking_away_events': looking_away_events,
            'staring_events': staring_events,
            'back_facing_events': back_facing_events,
            'audience_zone_thresholds': {
                'yaw_min': self.config['audience_yaw_min'],
                'yaw_max': self.config['audience_yaw_max'],
                'pitch_min': self.config['audience_pitch_min'],
                'pitch_max': self.config['audience_pitch_max'],
            },
            'staring_thresholds': {
                'angle_threshold': self.config['staring_angle_threshold'],
                'min_frames': self.config['min_staring_time'],
            },
            'segmentation': segmentation,
            'message': 'Eye contact analysis completed successfully.',
        }