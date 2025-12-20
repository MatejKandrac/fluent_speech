from datetime import datetime
from typing import List, Dict, Any


class LandmarkData:
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

    def __init__(self, video_id: str, data: List[FrameAnalysis] = None):
        self.video_id = video_id
        self.data = data or []
        self.created_at = datetime.utcnow()

    def add_frame_analysis(self, frame_analysis: FrameAnalysis):
        self.data.append(frame_analysis)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'video_id': self.video_id,
            'data': [frame.to_dict() for frame in self.data],
            'created_at': self.created_at.isoformat(),
            'total_frames': len(self.data)
        }
