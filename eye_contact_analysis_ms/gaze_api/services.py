"""Eye contact analysis service."""
from typing import Dict, Any, Optional, List
from django.conf import settings
import math
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .db_connection import get_analysis_by_recording_id


class EyeContactAnalysisService:
    """Service for analyzing eye contact and gaze patterns."""

    def __init__(self):
        self.config = settings.EYE_CONTACT_ANALYSIS_CONFIG
        print(f"Loaded configuration: {self.config}")

    def get_video_analysis(self, recording_id: int) -> Optional[Dict[str, Any]]:
        """Fetch video analysis data from PostgreSQL."""
        return get_analysis_by_recording_id(recording_id)

    def calculate_head_angles(self, frame_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Calculate yaw and pitch angles from pose landmarks.
        Yaw: Left-right rotation
        Pitch: Up-down rotation
        """
        landmarks = frame_data.get('landmarks', {})

        # Required landmarks for angle calculation
        required = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear']
        if not all(lm in landmarks for lm in required):
            return None

        nose = landmarks['nose']
        left_eye = landmarks['left_eye']
        right_eye = landmarks['right_eye']
        left_ear = landmarks['left_ear']
        right_ear = landmarks['right_ear']


        pitch_min = self.config['pitch_min']
        pitch_max = self.config['pitch_max']

        yaw_min = self.config['yaw_min']
        yaw_max = self.config['yaw_max']

        # Calculate face center (midpoint between eyes)
        face_center_x = (left_eye['x'] + right_eye['x']) / 2

        # Calculate YAW (left-right rotation)
        nose_offset_x = nose['x'] - face_center_x

        dist_to_left_ear = math.sqrt(
            (nose['x'] - left_ear['x']) ** 2 +
            (nose['y'] - left_ear['y']) ** 2
        )
        dist_to_right_ear = math.sqrt(
            (nose['x'] - right_ear['x']) ** 2 +
            (nose['y'] - right_ear['y']) ** 2
        )

        # Ear ratio: if left ear closer, ratio < 1 (looking left)
        if dist_to_right_ear > 0:
            ear_ratio = dist_to_left_ear / dist_to_right_ear
        else:
            ear_ratio = 1.0

        if ear_ratio > 0:
            ear_yaw = math.log(ear_ratio) * 50  # Scale factor for sensitivity
        else:
            ear_yaw = 0

        nose_yaw = nose_offset_x * 100

        # Weighted combination (ear ratio is more reliable)
        yaw = ear_yaw * 0.7 + nose_yaw * 0.3

        yaw = max(yaw_min, min(yaw_max, yaw))

        # Calculate PITCH (up-down rotation)
        eye_level_y = (left_eye['y'] + right_eye['y']) / 2
        nose_offset_y = nose['y'] - eye_level_y

        pitch = -nose_offset_y * 150

        pitch = max(pitch_min, min(pitch_max, pitch))

        return {
            'yaw': yaw,
            'pitch': pitch,
            'timestamp': frame_data.get('timestamp')
        }

    def build_heatmap(self, angle_data: List[Dict[str, float]], frame_duration: float) -> Dict[str, Any]:
        yaw_min = self.config['yaw_min']
        yaw_max = self.config['yaw_max']
        yaw_bin_size = self.config['yaw_bin_size']

        pitch_min = self.config['pitch_min']
        pitch_max = self.config['pitch_max']
        pitch_bin_size = self.config['pitch_bin_size']

        # Create bins
        yaw_bins = np.arange(yaw_min, yaw_max + yaw_bin_size, yaw_bin_size)
        pitch_bins = np.arange(pitch_min, pitch_max + pitch_bin_size, pitch_bin_size)

        # Initialize heatmap matrix
        n_yaw_bins = len(yaw_bins) - 1
        n_pitch_bins = len(pitch_bins) - 1
        heatmap_counts = np.zeros((n_pitch_bins, n_yaw_bins))

        for frame in angle_data:
            yaw = frame['yaw']
            pitch = frame['pitch']

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

    def detect_looking_away_events(self, angle_data: List[Dict[str, float]], frame_duration: float) -> List[Dict[str, Any]]:
        """Detect periods when person is not looking at audience."""
        audience_yaw_min = self.config['audience_yaw_min']
        audience_yaw_max = self.config['audience_yaw_max']
        audience_pitch_min = self.config['audience_pitch_min']
        audience_pitch_max = self.config['audience_pitch_max']
        min_frames = self.config['min_consecutive_frames']

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

    def detect_staring_events(self, angle_data: List[Dict[str, float]], frame_duration: float) -> List[Dict[str, Any]]:
        """Detect periods when person stares at the same position too long."""
        angle_threshold = self.config['staring_angle_threshold']
        min_frames = self.config['min_staring_frames']

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

                    # Start new streak
                    current_streak = [{
                        'timestamp': timestamp,
                        'yaw': yaw,
                        'pitch': pitch
                    }]
            else:
                # Start first streak
                current_streak.append({
                    'timestamp': timestamp,
                    'yaw': yaw,
                    'pitch': pitch
                })

        # Handle remaining streak at the end
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
        """Calculate eye contact statistics."""
        total_frames = len(angle_data)
        total_duration = total_frames * frame_duration

        # Calculate looking away duration
        looking_away_frames = sum(event['duration_frames'] for event in looking_away_events)
        looking_away_duration = looking_away_frames * frame_duration

        # Calculate looking at audience duration
        looking_at_audience_frames = total_frames - looking_away_frames
        looking_at_audience_duration = looking_at_audience_frames * frame_duration

        # Calculate percentages
        looking_at_audience_pct = (looking_at_audience_frames / total_frames * 100) if total_frames > 0 else 0
        looking_away_pct = (looking_away_frames / total_frames * 100) if total_frames > 0 else 0

        # Calculate average yaw and pitch
        avg_yaw = sum(f['yaw'] for f in angle_data) / len(angle_data) if angle_data else 0
        avg_pitch = sum(f['pitch'] for f in angle_data) / len(angle_data) if angle_data else 0

        # Calculate range (how much they scanned)
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
                              output_dir: Optional[str] = None) -> str:
        """Generate heatmap visualization with angle timeline."""
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

        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1], hspace=0.3)

        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax3 = fig.add_subplot(gs[2])

        # Plot 1: Heatmap
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

        # Plot 2: Yaw over time
        ax2.plot(frame_indices, yaw_values, color='blue', linewidth=1, label='Yaw')
        ax2.axhline(audience_yaw_min, color='lime', linestyle='--', linewidth=2, label=f'Audience Min ({audience_yaw_min}°)')
        ax2.axhline(audience_yaw_max, color='lime', linestyle='--', linewidth=2, label=f'Audience Max ({audience_yaw_max}°)')
        ax2.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax2.set_xlabel('Frame Index', fontsize=12)
        ax2.set_ylabel('Yaw (°)', fontsize=12)
        ax2.set_title('Yaw Angle Over Time', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3)

        # Plot 3: Pitch over time
        ax3.plot(frame_indices, pitch_values, color='red', linewidth=1, label='Pitch')
        ax3.axhline(audience_pitch_min, color='lime', linestyle='--', linewidth=2, label=f'Audience Min ({audience_pitch_min}°)')
        ax3.axhline(audience_pitch_max, color='lime', linestyle='--', linewidth=2, label=f'Audience Max ({audience_pitch_max}°)')
        ax3.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax3.set_xlabel('Frame Index', fontsize=12)
        ax3.set_ylabel('Pitch (°)', fontsize=12)
        ax3.set_title('Pitch Angle Over Time', fontsize=12, fontweight='bold')
        ax3.legend(loc='upper right', fontsize=9)
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = output_dir / f'gaze_heatmap_{recording_id}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Gaze heatmap saved to: {output_path}")
        return str(output_path)

    def analyze_eye_contact(self, recording_id: int) -> Dict[str, Any]:
        """Main analysis pipeline for eye contact."""
        print(f"Analyzing eye contact for recording ID: {recording_id}")

        # Step 1: Fetch data
        analysis_data = self.get_video_analysis(recording_id)
        if not analysis_data:
            return {'success': False, 'error': 'Video analysis not found'}

        total_frames = len(analysis_data.get('data', []))
        print(f"Retrieved {total_frames} frames from database")

        # Step 2: Calculate head angles for each frame
        angle_data = []
        for frame in analysis_data.get('data', []):
            angles = self.calculate_head_angles(frame)
            if angles:
                angle_data.append(angles)

        if not angle_data:
            return {'success': False, 'error': 'No frames with sufficient landmarks for angle calculation'}

        print(f"Calculated angles for {len(angle_data)} frames")

        # Calculate precise FPS from timestamps
        from datetime import datetime, time

        def parse_timestamp(ts_str):
            """Parse timestamp string (handles both datetime and time formats)."""
            try:
                # Try parsing as full datetime ISO format
                return datetime.fromisoformat(ts_str)
            except ValueError:
                # Parse as time only (HH:MM:SS.ffffff)
                t = datetime.strptime(ts_str, '%H:%M:%S.%f').time() if '.' in ts_str else datetime.strptime(ts_str, '%H:%M:%S').time()
                # Convert time to seconds
                return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000

        first_ts = parse_timestamp(angle_data[0]['timestamp'])
        last_ts = parse_timestamp(angle_data[-1]['timestamp'])

        # Calculate duration
        if isinstance(first_ts, datetime):
            total_duration = (last_ts - first_ts).total_seconds()
        else:
            # Both are float seconds
            total_duration = last_ts - first_ts

        fps = (len(angle_data) - 1) / total_duration if total_duration > 0 else 15.0
        frame_duration = 1.0 / fps
        print(f"Calculated FPS: {fps:.2f} (frame duration: {frame_duration*1000:.2f}ms)")

        # Step 3: Build heatmap
        heatmap_data = self.build_heatmap(angle_data, frame_duration)
        print(f"Built heatmap with {heatmap_data['shape']['n_yaw_bins']}x{heatmap_data['shape']['n_pitch_bins']} bins")

        # Step 4: Detect looking away events
        looking_away_events = self.detect_looking_away_events(angle_data, frame_duration)
        print(f"Detected {len(looking_away_events)} looking away events")

        # Step 5: Detect staring events
        staring_events = self.detect_staring_events(angle_data, frame_duration)
        print(f"Detected {len(staring_events)} staring events")

        # Step 6: Calculate statistics
        statistics = self.calculate_statistics(angle_data, looking_away_events, frame_duration)

        # Step 7: Generate visualization
        visualization_path = self.visualize_gaze_heatmap(heatmap_data, angle_data, recording_id)

        return {
            'success': True,
            'recording_id': recording_id,
            'total_frames': total_frames,
            'analyzed_frames': len(angle_data),
            'visualization_path': visualization_path,
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
                'min_frames': self.config['min_staring_frames']
            },
            'message': 'Eye contact analysis completed successfully.'
        }
