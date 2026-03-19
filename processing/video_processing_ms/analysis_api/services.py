import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import cv2
import mediapipe as mp
import requests
from django.conf import settings

from .db_connection import (
    get_video_by_id,
    update_recording_fps,
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

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        mp_config = settings.MEDIAPIPE_CONFIG
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=mp_config['min_detection_confidence'],
            min_tracking_confidence=mp_config['min_tracking_confidence'],
            model_complexity=mp_config['model_complexity']
        )

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
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            return None

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
        try:
            debug_dir = Path(settings.BASE_DIR) / 'debug_output' / video_id
            debug_dir.mkdir(parents=True, exist_ok=True)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = self.pose.process(rgb_frame)

            if results.pose_landmarks:
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

                output_path = debug_dir / f'frame_{processed_frame_index:04d}.png'
                cv2.imwrite(str(output_path), annotated_frame)

                return str(output_path)
            else:
                return None

        except Exception as e:
            print(f"Error saving visualization: {e}")
            return None

    def process_video(self, video_id: int) -> Dict[str, Any]:
        video_path = self.get_video_path(video_id)
        if not video_path:
            return {
                'success': False,
                'error': 'Video not found'
            }

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {
                'success': False,
                'error': 'Failed to open video file'
            }

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            print(f"Processing video: {video_path}")
            print(f"FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")

            frame_skip = int(fps * self.frame_interval)
            if frame_skip < 1:
                frame_skip = 1

            frames_per_second = fps / frame_skip
            print(f"Processing every {frame_skip} frames ({self.frame_interval}s interval)")
            print(f"This will process {frames_per_second:.2f} frames per second of video")

            update_recording_fps(video_id, frames_per_second)

            if duration > self.max_duration:
                cap.release()
                return {
                    'success': False,
                    'error': f'Video duration ({duration:.2f}s) exceeds maximum ({self.max_duration}s)'
                }

            frame_count = 0
            processed_count = 0
            frames_data = []

            while cap.isOpened():
                ret, frame = cap.read()

                if not ret:
                    break

                if frame_count % frame_skip == 0:
                    timestamp_seconds = frame_count / fps
                    timestamp = (datetime.min + timedelta(seconds=timestamp_seconds)).time().isoformat(
                        timespec='microseconds')

                    landmarks = self.extract_landmarks(frame)

                    if landmarks:
                        frames_data.append({
                            'timestamp': timestamp,
                            'frame_index': processed_count,
                            'landmarks': landmarks
                        })

                        if settings.DEBUG:
                            self.save_visualization(frame, str(video_id), processed_count)

                        processed_count += 1

                        if processed_count % 10 == 0:
                            print(f"Processed {processed_count} frames...")

                frame_count += 1

            cap.release()

            print(f"Video processing complete. Processed {processed_count} frames out of {frame_count} total frames")

            for frame_data in frames_data:
                frame_data_id = insert_frame_data(
                    recording_id=video_id,
                    timestamp=frame_data['timestamp'],
                    frame_index=frame_data['frame_index']
                )

                insert_landmarks_batch(frame_data_id, frame_data['landmarks'])

            print(f"Frame data saved to PostgreSQL for recording ID: {video_id}")

            return {
                'success': True,
                'recording_id': video_id,
                'frames_processed': processed_count,
                'total_frames': frame_count,
                'duration': duration
            }

        except Exception as e:
            cap.release()
            print(f"Error processing video: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def __del__(self):
        if hasattr(self, 'pose'):
            self.pose.close()
