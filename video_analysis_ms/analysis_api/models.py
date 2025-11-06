"""
Models for video analysis data stored in MongoDB.
Note: These are not Django ORM models, but data classes for MongoDB documents.
"""
from datetime import datetime
from typing import List, Dict, Any


class LandmarkData:
    """Represents a single landmark with x, y, z coordinates and visibility."""

    def __init__(self, x: float, y: float, z: float, visibility: float):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

    def to_dict(self) -> Dict[str, float]:
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'visibility': self.visibility
        }


class FrameAnalysis:
    """Represents the analysis data for a single frame."""

    def __init__(self, timestamp: str, landmarks: Dict[str, LandmarkData]):
        self.timestamp = timestamp
        self.landmarks = landmarks

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'landmarks': {
                name: landmark.to_dict()
                for name, landmark in self.landmarks.items()
            }
        }


class VideoAnalysis:
    """Represents the complete analysis document for a video."""

    def __init__(self, video_id: str, data: List[FrameAnalysis] = None):
        self.video_id = video_id
        self.data = data or []
        self.created_at = datetime.utcnow()
        self.max_x = 0.0
        self.max_y = 0.0

    def add_frame_analysis(self, frame_analysis: FrameAnalysis):
        """Add analysis data for a single frame."""
        self.data.append(frame_analysis)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'video_id': self.video_id,
            'data': [frame.to_dict() for frame in self.data],
            'created_at': self.created_at.isoformat(),
            'total_frames': len(self.data),
            'max_x': self.max_x,
            'max_y': self.max_y
        }
