"""
Video processing service using MediaPipe for landmark extraction and audio analysis.
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import tempfile
import subprocess

import cv2
import mediapipe as mp
import requests
from django.conf import settings

from .db_connection import (
    get_video_by_id,
    insert_analysis,
    insert_frame_data,
    insert_landmarks_batch
)
from .models import LandmarkData

# MediaPipe Pose landmark names
POSE_LANDMARK_NAMES = [
    'nose',
    'left_eye_inner',
    'left_eye',
    'left_eye_outer',
    'right_eye_inner',
    'right_eye',
    'right_eye_outer',
    'left_ear',
    'right_ear',
    'mouth_left',
    'mouth_right',
    'left_shoulder',
    'right_shoulder',
    'left_elbow',
    'right_elbow',
    'left_wrist',
    'right_wrist',
    'left_pinky',
    'right_pinky',
    'left_index',
    'right_index',
    'left_thumb',
    'right_thumb',
    'left_hip',
    'right_hip',
    'left_knee',
    'right_knee',
    'left_ankle',
    'right_ankle',
    'left_heel',
    'right_heel',
    'left_foot_index',
    'right_foot_index',
]


class VideoProcessingService:
    """Service for processing videos and extracting pose landmarks."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        # Get MediaPipe configuration from settings
        mp_config = settings.MEDIAPIPE_CONFIG
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=mp_config['min_detection_confidence'],
            min_tracking_confidence=mp_config['min_tracking_confidence'],
            model_complexity=mp_config['model_complexity']
        )

        # Get video processing configuration
        self.frame_interval = settings.VIDEO_PROCESSING_CONFIG['frame_interval']
        self.max_duration = settings.VIDEO_PROCESSING_CONFIG['max_video_duration']

    def get_video_path(self, video_id: int) -> Optional[str]:
        try:
            video = get_video_by_id(video_id)

            if not video:
                print(f"Video with ID {video_id} not found in database")
                return None

            filename = video.get('filename')
            if not filename:
                print(f"Video record {video_id} has no filename")
                return None

            video_path = Path(settings.VIDEO_STORAGE_PATH) / filename

            if not video_path.exists():
                print(f"Video file not found at path: {video_path}")
                return None

            return str(video_path)

        except Exception as e:
            print(f"Error getting video path: {e}")
            return None

    def extract_landmarks(self, frame) -> Optional[Dict[str, LandmarkData]]:
        """
        Extract pose landmarks from a single frame.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            return None

        # Extract landmarks
        landmarks = {}
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            landmark_name = POSE_LANDMARK_NAMES[idx]
            landmarks[landmark_name] = LandmarkData(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility
            )

        return landmarks

    def save_visualization(self, frame, video_id: str, processed_frame_index: int) -> Optional[str]:
        """
        Save a frame with pose landmarks visualization.
        """
        try:
            # Create debug output directory for this video
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / video_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Convert BGR to RGB for processing
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process the frame
            results = self.pose.process(rgb_frame)

            if results.pose_landmarks:
                # Draw landmarks on the frame
                annotated_frame = frame.copy()
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=2, circle_radius=3
                    ),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(
                        color=(255, 0, 0), thickness=2
                    )
                )

                # Save the annotated frame
                output_path = debug_dir / f'frame_{processed_frame_index:04d}.png'
                cv2.imwrite(str(output_path), annotated_frame)

                return str(output_path)
            else:
                return None

        except Exception as e:
            print(f"Error saving visualization: {e}")
            return None

    def extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file using ffmpeg and save it next to the video.
        Returns: wav file path
        """
        try:
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("WARNING: ffmpeg not found in PATH. Skipping audio extraction.")
                print("Install ffmpeg to enable audio analysis: https://ffmpeg.org/download.html")
                return None

            print("Extracting audio from video...")
            # Create WAV file path next to the video file
            video_file = Path(video_path)
            audio_path = video_file.parent / f"{video_file.stem}.wav"

            # Get target sample rate from settings
            sample_rate = str(settings.AUDIO_EXTRACTION_CONFIG['sample_rate'])

            # Extract audio using ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                 '-ar', sample_rate, '-ac', '1', '-y', str(audio_path)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"ffmpeg error: {result.stderr}")
                return None

            print(f"WAV file saved at: {audio_path}")
            return str(audio_path)

        except Exception as e:
            print(f"Error extracting audio: {e}")
            return None

    def trigger_audio_analysis(self, recording_id: int):
        """
        Asynchronously trigger audio analysis in the audio analysis service.
        """
        try:
            audio_service_url = settings.AUDIO_ANALYSIS_SERVICE_URL
            endpoint = f"{audio_service_url}/api/v1/analyze/audio/{recording_id}/"

            # Send async request to audio service
            requests.post(
                endpoint,
                timeout=5
            )
            print(f"Audio analysis triggered for recording {recording_id}")
        except requests.exceptions.Timeout:
            # Expected for async call
            print(f"Audio analysis request sent (async) for recording {recording_id}")
        except Exception as e:
            print(f"Warning: Failed to trigger audio analysis: {e}")

    def process_video(self, video_id: int) -> Dict[str, Any]:
        """
        Process a video and extract pose landmarks at regular intervals.
        """
        # Get video path
        video_path = self.get_video_path(video_id)
        if not video_path:
            return {
                'success': False,
                'error': 'Video not found'
            }

        # Open video
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {
                'success': False,
                'error': 'Failed to open video file'
            }

        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            print(f"Processing video: {video_path}")
            print(f"FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")

            # Check if video is too long
            if duration > self.max_duration:
                cap.release()
                return {
                    'success': False,
                    'error': f'Video duration ({duration:.2f}s) exceeds maximum ({self.max_duration}s)'
                }

            # Extract audio from video
            wav_path = self.extract_audio_from_video(video_path)

            # Calculate frame skip interval
            frame_skip = int(fps * self.frame_interval)
            if frame_skip < 1:
                frame_skip = 1

            frames_per_second = fps / frame_skip
            print(f"Processing every {frame_skip} frames ({self.frame_interval}s interval)")
            print(f"This will process {frames_per_second:.2f} frames per second of video")

            frame_count = 0
            processed_count = 0
            max_x = 0.0
            max_y = 0.0
            frames_data = []

            while cap.isOpened():
                ret, frame = cap.read()

                if not ret:
                    break

                # Process frames at the specified interval
                if frame_count % frame_skip == 0:
                    # Calculate timestamp for this frame
                    timestamp_seconds = frame_count / fps
                    timestamp = (datetime.min + timedelta(seconds=timestamp_seconds)).time().isoformat(
                        timespec='microseconds')

                    # Extract landmarks
                    landmarks = self.extract_landmarks(frame)

                    if landmarks:
                        # Update max coordinates
                        for landmark in landmarks.values():
                            max_x = max(max_x, landmark.x)
                            max_y = max(max_y, landmark.y)

                        # Store frame data for batch insertion
                        frames_data.append({
                            'timestamp': timestamp,
                            'frame_index': processed_count,
                            'landmarks': landmarks
                        })

                        # Save visualization for this processed frame
                        self.save_visualization(frame, str(video_id), processed_count)

                        processed_count += 1

                        if processed_count % 10 == 0:
                            print(f"Processed {processed_count} frames...")

                frame_count += 1

            cap.release()

            print(f"Video processing complete. Processed {processed_count} frames out of {frame_count} total frames")
            print(f"Max coordinates: x={max_x:.4f}, y={max_y:.4f}")

            # Save to PostgreSQL
            # First, insert analysis record
            analysis_id = insert_analysis(
                recording_id=video_id,
                total_frames=processed_count,
                max_x=max_x,
                max_y=max_y
            )

            # Then, insert frame data and landmarks
            for frame_data in frames_data:
                frame_data_id = insert_frame_data(
                    analysis_id=analysis_id,
                    timestamp=frame_data['timestamp'],
                    frame_index=frame_data['frame_index']
                )

                # Insert all landmarks for this frame in batch
                insert_landmarks_batch(frame_data_id, frame_data['landmarks'])

            # Trigger audio analysis asynchronously if WAV file was created
            if wav_path:
                self.trigger_audio_analysis(video_id)

            print(f"Analysis saved to PostgreSQL with ID: {analysis_id}")

            return {
                'success': True,
                'analysis_id': analysis_id,
                'frames_processed': processed_count,
                'total_frames': frame_count,
                'duration': duration,
                'max_x': max_x,
                'max_y': max_y
            }

        except Exception as e:
            cap.release()
            print(f"Error processing video: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'pose'):
            self.pose.close()
