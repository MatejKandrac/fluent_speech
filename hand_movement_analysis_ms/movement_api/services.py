"""
Hand movement analysis service using change point detection.
"""
import numpy as np
import ruptures as rpt
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any, Optional
from bson import ObjectId
from django.conf import settings

from .db_connection import get_analysis_collection


class HandMovementAnalysisService:
    """Service for analyzing hand movements from video analysis data."""

    def __init__(self):
        self.config = settings.MOVEMENT_ANALYSIS_CONFIG
        print(f"Loaded configuration {self.config}")

    def get_video_analysis(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch video analysis from MongoDB.

        Args:
            video_id: The MongoDB ObjectId of the video

        Returns:
            Analysis document or None if not found
        """
        analysis_collection = get_analysis_collection()

        # Find the most recent analysis for this video
        analysis = analysis_collection.find_one(
            {'video_id': video_id},
            sort=[('created_at', -1)]
        )

        return analysis

    def extract_hand_positions(self, analysis_data: Dict[str, Any]) -> tuple:
        """
        Extract hand positions from analysis data.

        Args:
            analysis_data: The analysis document from MongoDB

        Returns:
            Tuple of (timestamps, left_wrist_positions, right_wrist_positions)
        """
        timestamps = []
        left_wrist_positions = []
        right_wrist_positions = []

        for frame_data in analysis_data.get('data', []):
            timestamp = frame_data.get('timestamp')
            landmarks = frame_data.get('landmarks', {})

            # Get left and right wrist landmarks
            left_wrist = landmarks.get('left_wrist')
            right_wrist = landmarks.get('right_wrist')

            if left_wrist and right_wrist:
                timestamps.append(timestamp)

                # Store (x, y, z) coordinates
                left_wrist_positions.append([
                    left_wrist['x'],
                    left_wrist['y'],
                    left_wrist['z']
                ])

                right_wrist_positions.append([
                    right_wrist['x'],
                    right_wrist['y'],
                    right_wrist['z']
                ])

        return timestamps, np.array(left_wrist_positions), np.array(right_wrist_positions)

    def calculate_velocity(self, positions: np.ndarray) -> np.ndarray:
        """
        Calculate velocity between frames.

        Args:
            positions: Array of shape (n_frames, 3) with x, y, z coordinates

        Returns:
            Array of velocities (magnitude)
        """
        if len(positions) < 2:
            return np.array([])

        # Calculate displacement between consecutive frames
        displacements = np.diff(positions, axis=0)

        # Calculate velocity magnitude
        velocities = np.linalg.norm(displacements, axis=1)

        return velocities

    def calculate_acceleration(self, velocities: np.ndarray) -> np.ndarray:
        """
        Calculate acceleration from velocities.

        Args:
            velocities: Array of velocities

        Returns:
            Array of accelerations (magnitude)
        """
        if len(velocities) < 2:
            return np.array([])

        # Calculate change in velocity
        accelerations = np.diff(velocities)

        return accelerations

    def detect_change_points(self, signal: np.ndarray) -> List[int]:
        """
        Detect change points in acceleration signal using ruptures.

        Args:
            signal: 1D array of acceleration values

        Returns:
            List of change point indices
        """
        if len(signal) < self.config['min_segment_length']:
            return []

        try:
            # Use Pelt algorithm for change point detection
            # This is faster than ClasPy and works well for our use case
            algo = rpt.Pelt(model="rbf", min_size=self.config['min_segment_length']).fit(signal)

            # Predict change points with penalty parameter
            change_points = algo.predict(pen=self.config['change_point_penalty'])

            # Remove the last point (end of signal)
            if change_points and change_points[-1] == len(signal):
                change_points = change_points[:-1]

            return change_points
        except Exception as e:
            print(f"Error detecting change points: {e}")
            return []

    def classify_segments(self, accelerations: np.ndarray, change_points: List[int]) -> List[Dict[str, Any]]:
        """
        Classify segments based on acceleration characteristics.

        Args:
            accelerations: Array of acceleration values
            change_points: List of change point indices

        Returns:
            List of segment dictionaries with classification
        """
        segments = []

        # Add start point
        points = [0] + change_points + [len(accelerations)]

        for i in range(len(points) - 1):
            start_idx = points[i]
            end_idx = points[i + 1]

            segment_data = accelerations[start_idx:end_idx]

            if len(segment_data) == 0:
                continue

            # Calculate segment statistics
            mean_acceleration = np.mean(np.abs(segment_data))
            max_acceleration = np.max(np.abs(segment_data))
            std_acceleration = np.std(segment_data)

            # Classify segment
            segment_type = self._classify_segment_type(mean_acceleration, max_acceleration)

            segments.append({
                'start_index': start_idx,
                'end_index': end_idx,
                'mean_acceleration': float(mean_acceleration),
                'max_acceleration': float(max_acceleration),
                'std_acceleration': float(std_acceleration),
                'type': segment_type,
                'importance': 'high' if segment_type == 'fast_movement' else 'medium'
            })

        return segments

    def _classify_segment_type(self, mean_accel: float, max_accel: float) -> str:
        """
        Classify segment based on acceleration values.

        Args:
            mean_accel: Mean acceleration in segment
            max_accel: Maximum acceleration in segment

        Returns:
            Segment type string
        """
        threshold = self.config['acceleration_threshold']

        if mean_accel > threshold or max_accel > threshold * 1.5:
            return 'fast_movement'
        elif mean_accel < threshold * 0.3:
            return 'slow_movement'
        else:
            return 'normal_movement'

    def generate_debug_visualizations(
        self,
        video_id: str,
        timestamps: List[str],
        left_positions: np.ndarray,
        right_positions: np.ndarray,
        left_velocities: np.ndarray,
        right_velocities: np.ndarray,
        left_accelerations: np.ndarray,
        right_accelerations: np.ndarray,
        left_change_points: List[int],
        right_change_points: List[int],
        left_segments: List[Dict[str, Any]],
        right_segments: List[Dict[str, Any]]
    ):
        """
        Generate debug visualization plots for hand movement analysis.

        Args:
            video_id: The video ID for folder naming
            timestamps: List of timestamp strings
            left_positions: Left hand position array
            right_positions: Right hand position array
            left_velocities: Left hand velocity array
            right_velocities: Right hand velocity array
            left_accelerations: Left hand acceleration array
            right_accelerations: Right hand acceleration array
            left_change_points: Left hand change point indices
            right_change_points: Right hand change point indices
            left_segments: Left hand segment data
            right_segments: Right hand segment data
        """
        # Create debug output directory
        debug_dir = Path(settings.BASE_DIR) / 'debug_output' / video_id
        debug_dir.mkdir(parents=True, exist_ok=True)

        print(f"Generating debug visualizations in {debug_dir}")

        # Create time arrays for plotting
        time_positions = np.arange(len(timestamps))
        time_velocities = np.arange(len(timestamps) - 1)
        time_accelerations = np.arange(len(timestamps) - 2)

        # 1. Position plots (X, Y, Z coordinates)
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('Hand Position Coordinates Over Time', fontsize=16)

        for idx, (coord_name, coord_idx) in enumerate([('X', 0), ('Y', 1), ('Z', 2)]):
            # Left hand
            axes[idx, 0].plot(time_positions, left_positions[:, coord_idx], 'b-', linewidth=1)
            axes[idx, 0].set_title(f'Left Hand - {coord_name} Coordinate')
            axes[idx, 0].set_xlabel('Frame')
            axes[idx, 0].set_ylabel(f'{coord_name} Position')
            axes[idx, 0].grid(True, alpha=0.3)

            # Right hand
            axes[idx, 1].plot(time_positions, right_positions[:, coord_idx], 'r-', linewidth=1)
            axes[idx, 1].set_title(f'Right Hand - {coord_name} Coordinate')
            axes[idx, 1].set_xlabel('Frame')
            axes[idx, 1].set_ylabel(f'{coord_name} Position')
            axes[idx, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(debug_dir / 'positions.png', dpi=150)
        plt.close()

        # 2. Velocity plots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        fig.suptitle('Hand Velocity Over Time', fontsize=16)

        # Left hand velocity
        ax1.plot(time_velocities, left_velocities, 'b-', linewidth=1, label='Velocity')
        ax1.axhline(y=np.mean(left_velocities), color='g', linestyle='--',
                    label=f'Mean: {np.mean(left_velocities):.4f}')
        ax1.set_title('Left Hand Velocity')
        ax1.set_xlabel('Frame')
        ax1.set_ylabel('Velocity (magnitude)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Right hand velocity
        ax2.plot(time_velocities, right_velocities, 'r-', linewidth=1, label='Velocity')
        ax2.axhline(y=np.mean(right_velocities), color='g', linestyle='--',
                    label=f'Mean: {np.mean(right_velocities):.4f}')
        ax2.set_title('Right Hand Velocity')
        ax2.set_xlabel('Frame')
        ax2.set_ylabel('Velocity (magnitude)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(debug_dir / 'velocities.png', dpi=150)
        plt.close()

        # 3. Acceleration plots with change points
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        fig.suptitle('Hand Acceleration with Change Points', fontsize=16)

        # Left hand acceleration
        ax1.plot(time_accelerations, left_accelerations, 'b-', linewidth=1, label='Acceleration')
        ax1.axhline(y=np.mean(left_accelerations), color='g', linestyle='--',
                    label=f'Mean: {np.mean(left_accelerations):.4f}')
        ax1.axhline(y=self.config['acceleration_threshold'], color='orange', linestyle=':',
                    label=f'Threshold: {self.config["acceleration_threshold"]}')

        # Mark change points
        for cp in left_change_points:
            ax1.axvline(x=cp, color='red', linestyle='--', alpha=0.7)

        ax1.set_title(f'Left Hand Acceleration ({len(left_change_points)} change points)')
        ax1.set_xlabel('Frame')
        ax1.set_ylabel('Acceleration')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Right hand acceleration
        ax2.plot(time_accelerations, right_accelerations, 'r-', linewidth=1, label='Acceleration')
        ax2.axhline(y=np.mean(right_accelerations), color='g', linestyle='--',
                    label=f'Mean: {np.mean(right_accelerations):.4f}')
        ax2.axhline(y=self.config['acceleration_threshold'], color='orange', linestyle=':',
                    label=f'Threshold: {self.config["acceleration_threshold"]}')

        # Mark change points
        for cp in right_change_points:
            ax2.axvline(x=cp, color='red', linestyle='--', alpha=0.7)

        ax2.set_title(f'Right Hand Acceleration ({len(right_change_points)} change points)')
        ax2.set_xlabel('Frame')
        ax2.set_ylabel('Acceleration')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(debug_dir / 'accelerations.png', dpi=150)
        plt.close()

        # 4. Segment classification visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        fig.suptitle('Segment Classification', fontsize=16)

        # Left hand segments
        for segment in left_segments:
            start = segment['start_index']
            end = segment['end_index']
            segment_type = segment['type']
            color = 'red' if segment_type == 'fast_movement' else 'blue' if segment_type == 'slow_movement' else 'gray'

            ax1.axvspan(start, end, alpha=0.3, color=color,
                       label=segment_type if segment_type not in ax1.get_legend_handles_labels()[1] else '')
            ax1.plot([start + (end - start) / 2], [segment['mean_acceleration']],
                    'o', color=color, markersize=8)

        if len(left_accelerations) > 0:
            ax1.plot(time_accelerations, left_accelerations, 'k-', linewidth=0.5, alpha=0.5)
        ax1.set_title(f'Left Hand - Segments ({len(left_segments)} total)')
        ax1.set_xlabel('Frame')
        ax1.set_ylabel('Acceleration')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Right hand segments
        for segment in right_segments:
            start = segment['start_index']
            end = segment['end_index']
            segment_type = segment['type']
            color = 'red' if segment_type == 'fast_movement' else 'blue' if segment_type == 'slow_movement' else 'gray'

            ax2.axvspan(start, end, alpha=0.3, color=color,
                       label=segment_type if segment_type not in ax2.get_legend_handles_labels()[1] else '')
            ax2.plot([start + (end - start) / 2], [segment['mean_acceleration']],
                    'o', color=color, markersize=8)

        if len(right_accelerations) > 0:
            ax2.plot(time_accelerations, right_accelerations, 'k-', linewidth=0.5, alpha=0.5)
        ax2.set_title(f'Right Hand - Segments ({len(right_segments)} total)')
        ax2.set_xlabel('Frame')
        ax2.set_ylabel('Acceleration')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(debug_dir / 'segments.png', dpi=150)
        plt.close()

        # 5. Summary statistics
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')

        summary_text = f"""
        HAND MOVEMENT ANALYSIS SUMMARY
        Video ID: {video_id}

        LEFT HAND:
        - Total frames: {len(timestamps)}
        - Velocity: mean={np.mean(left_velocities):.4f}, std={np.std(left_velocities):.4f}, max={np.max(left_velocities):.4f}
        - Acceleration: mean={np.mean(left_accelerations):.4f}, std={np.std(left_accelerations):.4f}, max={np.max(np.abs(left_accelerations)):.4f}
        - Change points detected: {len(left_change_points)}
        - Total segments: {len(left_segments)}
        - Fast movement segments: {len([s for s in left_segments if s['type'] == 'fast_movement'])}
        - Normal movement segments: {len([s for s in left_segments if s['type'] == 'normal_movement'])}
        - Slow movement segments: {len([s for s in left_segments if s['type'] == 'slow_movement'])}

        RIGHT HAND:
        - Total frames: {len(timestamps)}
        - Velocity: mean={np.mean(right_velocities):.4f}, std={np.std(right_velocities):.4f}, max={np.max(right_velocities):.4f}
        - Acceleration: mean={np.mean(right_accelerations):.4f}, std={np.std(right_accelerations):.4f}, max={np.max(np.abs(right_accelerations)):.4f}
        - Change points detected: {len(right_change_points)}
        - Total segments: {len(right_segments)}
        - Fast movement segments: {len([s for s in right_segments if s['type'] == 'fast_movement'])}
        - Normal movement segments: {len([s for s in right_segments if s['type'] == 'normal_movement'])}
        - Slow movement segments: {len([s for s in right_segments if s['type'] == 'slow_movement'])}

        CONFIGURATION:
        - Acceleration threshold: {self.config['acceleration_threshold']}
        - Min segment length: {self.config['min_segment_length']}
        - Change point penalty: {self.config['change_point_penalty']}
        """

        ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
                verticalalignment='center')

        plt.savefig(debug_dir / 'summary.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Debug visualizations saved to {debug_dir}")

    def analyze_hand_movements(self, video_id: str) -> Dict[str, Any]:
        """
        Analyze hand movements for a video.

        Args:
            video_id: The MongoDB ObjectId of the video

        Returns:
            Dictionary with analysis results
        """
        print(f"Analyzing hand movements for video ID: {video_id}")

        # Fetch analysis data
        analysis_data = self.get_video_analysis(video_id)

        if not analysis_data:
            return {
                'success': False,
                'error': 'Video analysis not found'
            }

        # Extract hand positions
        timestamps, left_positions, right_positions = self.extract_hand_positions(analysis_data)

        if len(timestamps) < 3:
            return {
                'success': False,
                'error': 'Insufficient hand position data'
            }

        print(f"Extracted {len(timestamps)} frames with hand data")

        # Analyze left hand
        left_results = self._analyze_single_hand(timestamps, left_positions, 'left')

        # Analyze right hand
        right_results = self._analyze_single_hand(timestamps, right_positions, 'right')

        print(f"Analysis complete. Left: {len(left_results['segments'])} segments, Right: {len(right_results['segments'])} segments")

        # Generate debug visualizations
        try:
            self.generate_debug_visualizations(
                video_id=video_id,
                timestamps=timestamps,
                left_positions=left_positions,
                right_positions=right_positions,
                left_velocities=left_results['velocities'],
                right_velocities=right_results['velocities'],
                left_accelerations=left_results['accelerations'],
                right_accelerations=right_results['accelerations'],
                left_change_points=left_results['change_points'],
                right_change_points=right_results['change_points'],
                left_segments=left_results['segments'],
                right_segments=right_results['segments']
            )
        except Exception as e:
            print(f"Error generating debug visualizations: {e}")

        return {
            'success': True,
            'video_id': video_id,
            'total_frames': len(timestamps),
            'left_hand': left_results,
            'right_hand': right_results
        }

    def _analyze_single_hand(self, timestamps: List[str], positions: np.ndarray, hand_name: str) -> Dict[str, Any]:
        """
        Analyze movements for a single hand.

        Args:
            timestamps: List of timestamp strings
            positions: Array of hand positions
            hand_name: Name of the hand ('left' or 'right')

        Returns:
            Dictionary with hand-specific results
        """
        # Calculate velocities
        velocities = self.calculate_velocity(positions)

        # Calculate accelerations
        accelerations = self.calculate_acceleration(velocities)

        # Detect change points
        change_points = self.detect_change_points(accelerations)

        # Classify segments
        segments = self.classify_segments(accelerations, change_points)

        # Add timestamps to segments
        for segment in segments:
            start_idx = segment['start_index']
            # Acceleration array is 2 indices shorter than timestamps
            # (one diff for velocity, another for acceleration)
            timestamp_idx = min(start_idx + 2, len(timestamps) - 1)
            segment['timestamp'] = timestamps[timestamp_idx]

        # Sort segments by importance (fast movements first)
        segments.sort(key=lambda x: (
            0 if x['importance'] == 'high' else 1,
            -x['max_acceleration']
        ))

        return {
            'hand': hand_name,
            'segments': segments,
            'total_segments': len(segments),
            'fast_movement_segments': len([s for s in segments if s['type'] == 'fast_movement']),
            # Include raw data for debugging
            'velocities': velocities,
            'accelerations': accelerations,
            'change_points': change_points
        }
