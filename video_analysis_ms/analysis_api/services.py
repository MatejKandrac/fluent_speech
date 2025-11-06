"""
Video processing service using MediaPipe for landmark extraction.
"""
import cv2
import mediapipe as mp
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from django.conf import settings
from bson import ObjectId

from .models import VideoAnalysis, FrameAnalysis, LandmarkData
from .db_connection import get_videos_collection, get_analysis_collection


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

    def get_video_path(self, video_id: str) -> Optional[str]:
        """
        Get the file path for a video from MongoDB.

        Args:
            video_id: The MongoDB ObjectId of the video

        Returns:
            Full path to the video file, or None if not found
        """
        videos_collection = get_videos_collection()

        try:
            video_doc = videos_collection.find_one({'_id': ObjectId(video_id)})

            if not video_doc:
                print(f"Video with ID {video_id} not found in database")
                return None

            filename = video_doc.get('filename')
            if not filename:
                print(f"Video document {video_id} has no filename")
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

        Args:
            frame: OpenCV frame (BGR image)

        Returns:
            Dictionary mapping landmark names to LandmarkData objects,
            or None if no pose detected
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

        Args:
            frame: The video frame to annotate
            video_id: The video ID (for subdirectory)
            processed_frame_index: The index of the processed frame (0, 1, 2, ...)

        Returns:
            Path to saved image, or None if failed
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

    def process_video(self, video_id: str) -> Dict[str, Any]:
        """
        Process a video and extract pose landmarks at regular intervals.

        Args:
            video_id: The MongoDB ObjectId of the video to process

        Returns:
            Dictionary with success status and analysis results
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

            # Calculate frame skip interval
            frame_skip = int(fps * self.frame_interval)
            if frame_skip < 1:
                frame_skip = 1

            print(f"Processing every {frame_skip} frames ({self.frame_interval}s interval)")
            print(f"📸 Saving debug visualizations to debug_output/{video_id}/")

            # Create analysis object
            analysis = VideoAnalysis(video_id=video_id)

            frame_count = 0
            processed_count = 0
            max_x = 0.0
            max_y = 0.0

            while cap.isOpened():
                ret, frame = cap.read()

                if not ret:
                    break

                # Process frames at the specified interval
                if frame_count % frame_skip == 0:
                    # Calculate timestamp for this frame
                    timestamp_seconds = frame_count / fps
                    timestamp = (datetime.min + timedelta(seconds=timestamp_seconds)).time().isoformat()

                    # Extract landmarks
                    landmarks = self.extract_landmarks(frame)

                    if landmarks:
                        # Update max coordinates
                        for landmark in landmarks.values():
                            max_x = max(max_x, landmark.x)
                            max_y = max(max_y, landmark.y)

                        frame_analysis = FrameAnalysis(
                            timestamp=timestamp,
                            landmarks=landmarks
                        )
                        analysis.add_frame_analysis(frame_analysis)

                        # Save visualization for this processed frame
                        self.save_visualization(frame, video_id, processed_count)

                        processed_count += 1

                        if processed_count % 10 == 0:
                            print(f"Processed {processed_count} frames...")

                frame_count += 1

            cap.release()

            print(f"Video processing complete. Processed {processed_count} frames out of {frame_count} total frames")
            print(f"Max coordinates: x={max_x:.4f}, y={max_y:.4f}")

            # Set max coordinates on analysis
            analysis.max_x = max_x
            analysis.max_y = max_y

            # Save to MongoDB
            analysis_collection = get_analysis_collection()
            result = analysis_collection.insert_one(analysis.to_dict())
            analysis_id = str(result.inserted_id)

            print(f"Analysis saved to MongoDB with ID: {analysis_id}")

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
