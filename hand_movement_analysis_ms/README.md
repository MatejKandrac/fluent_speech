# Hand Movement Analysis Microservice

Django-based microservice for analyzing hand movements from video analysis data using change point detection.

## Features

- Analyzes hand movements (left and right wrist) from video landmarks
- Calculates velocity and acceleration between frames
- Uses change point detection (ruptures library) to find sudden movement changes
- Identifies fast movements and sudden slowdowns
- Returns timestamped segments with movement characteristics

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure your settings

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver 8002
```

The service will be available at `http://localhost:8002`

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Hand Movements
```
POST /api/v1/analyze/hand-movements/{video_id}/
```

Analyzes hand movements from the video analysis data stored in MongoDB.

**Parameters:**
- `video_id` (path): The MongoDB ID of the video

**Example:**
```bash
curl -X POST http://localhost:8002/api/v1/analyze/hand-movements/507f1f77bcf86cd799439011/
```

**Response:**
```json
{
    "success": true,
    "video_id": "507f1f77bcf86cd799439011",
    "total_frames": 150,
    "left_hand": {
        "hand": "left",
        "total_segments": 5,
        "fast_movement_segments": 2,
        "segments": [
            {
                "start_index": 25,
                "end_index": 35,
                "timestamp": "00:00:05.200000",
                "mean_acceleration": 3.45,
                "max_acceleration": 5.67,
                "std_acceleration": 1.23,
                "type": "fast_movement",
                "importance": "high"
            },
            ...
        ]
    },
    "right_hand": {
        "hand": "right",
        "total_segments": 6,
        "fast_movement_segments": 3,
        "segments": [...]
    }
}
```

## Algorithm

### 1. Hand Position Extraction
- Extracts left_wrist and right_wrist landmarks from video analysis
- Uses (x, y, z) coordinates for 3D position tracking

### 2. Velocity Calculation
- Calculates displacement between consecutive frames
- Computes velocity magnitude: `v = ||position[t] - position[t-1]||`

### 3. Acceleration Calculation
- Calculates change in velocity: `a = v[t] - v[t-1]`

### 4. Change Point Detection
- Uses ruptures library (Pelt algorithm with RBF kernel)
- Detects points where acceleration patterns change significantly
- Configurable penalty parameter controls sensitivity

### 5. Segment Classification
- **Fast Movement**: High mean or max acceleration (> threshold)
- **Slow Movement**: Low mean acceleration (< threshold * 0.3)
- **Normal Movement**: Between slow and fast

### 6. Importance Ranking
- Segments sorted by importance (fast movements first)
- Within same importance, sorted by max acceleration

## Configuration

Edit `hand_movement_service/settings.py`:

```python
MOVEMENT_ANALYSIS_CONFIG = {
    'acceleration_threshold': 2.0,  # Threshold for significant acceleration
    'min_segment_length': 3,        # Minimum frames in a segment
    'change_point_penalty': 3,      # Penalty for change point detection (lower = more sensitive)
}
```

## Dependencies

- **ruptures**: Change point detection library
- **numpy**: Numerical computations
- **scipy**: Scientific computing (if needed for additional analysis)
- **pymongo**: MongoDB connection
- **Django** + **djangorestframework**: Web framework

## How It Works

1. Service receives video ID
2. Fetches video analysis from MongoDB `analysis` collection
3. Extracts wrist positions for both hands
4. Calculates velocity → acceleration
5. Runs change point detection on acceleration signal
6. Classifies segments and ranks by importance
7. Returns timestamped segments

## Example Use Cases

- **Speech Therapy**: Identify rapid hand gestures during speech
- **Movement Analysis**: Detect sudden hand movements indicating emphasis
- **Gesture Recognition**: Find key gesture points for further analysis
- **Video Summarization**: Highlight important movement moments

## Troubleshooting

### No Analysis Found
- Ensure video analysis microservice has processed the video first
- Check MongoDB `analysis` collection for the video_id

### Insufficient Data
- Minimum 3 frames with hand landmark data required
- Ensure MediaPipe detected hands in the video

### No Change Points Detected
- Try lowering `change_point_penalty` for more sensitivity
- Check if hand movements are actually present in video
