# Video Analysis Microservice - Setup Guide

This microservice uses Django, MediaPipe, and MongoDB to analyze videos and extract pose landmarks.

## Prerequisites

- Python 3.9 or higher
- MongoDB (running via Docker or locally)
- Video files accessible at the path specified in `.env`

## Installation Steps

### 1. Create Virtual Environment

```bash
cd video_analysis_ms
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

The `.env` file is already created. Verify the settings:

```env
DB_NAME=fluent
DB_HOST=localhost
DB_PORT=27017
DB_USERNAME=fluent
DB_PASSWORD=root

API_GATEWAY_URL=http://localhost:8000
VIDEO_STORAGE_PATH=D:\VideoData

DJANGO_SECRET_KEY=django-insecure-video-analysis-dev-key-2024
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Start the Service

```bash
python manage.py runserver 8001
```

The service will be available at `http://localhost:8001`

## API Endpoints

### Health Check
```
GET /api/health/
```

### Analyze Video
```
POST /api/analyze/video/{video_id}/
```
Processes the video and extracts pose landmarks at 0.2-second intervals.

**Example:**
```bash
curl -X POST http://localhost:8001/api/analyze/video/507f1f77bcf86cd799439011/
```

**Response:**
```json
{
    "success": true,
    "message": "Video analysis completed successfully",
    "analysis_id": "65abc123def456789012345",
    "frames_processed": 150,
    "total_frames": 300,
    "duration": 10.0
}
```

### Get Analysis Results
```
GET /api/analysis/{analysis_id}/
```

### Get All Analyses for a Video
```
GET /api/analysis/video/{video_id}/
```

### Delete Analysis
```
DELETE /api/analysis/{analysis_id}/delete/
```

## Data Structure

The analysis results are stored in MongoDB with the following structure:

```json
{
    "_id": "65abc123def456789012345",
    "video_id": "507f1f77bcf86cd799439011",
    "created_at": "2024-01-15T10:30:00.000000",
    "total_frames": 150,
    "max_x": 0.987,
    "max_y": 0.923,
    "data": [
        {
            "timestamp": "00:00:00.000000",
            "landmarks": {
                "nose": {
                    "x": 0.5,
                    "y": 0.3,
                    "z": -0.1,
                    "visibility": 0.99
                },
                "left_shoulder": {
                    "x": 0.4,
                    "y": 0.5,
                    "z": -0.2,
                    "visibility": 0.95
                },
                "right_shoulder": {
                    "x": 0.6,
                    "y": 0.5,
                    "z": -0.2,
                    "visibility": 0.96
                }
                // ... 33 landmarks total
            }
        },
        {
            "timestamp": "00:00:00.200000",
            "landmarks": {
                // ... landmarks for next frame
            }
        }
        // ... more frames
    ]
}
```

**Note:** The `max_x` and `max_y` fields contain the maximum x and y coordinate values across all landmarks in all frames, useful for normalization in downstream processing.

## Landmark Names

The service extracts 33 pose landmarks from MediaPipe:

- Face: nose, left/right eye (inner, center, outer), left/right ear, mouth (left, right)
- Upper body: left/right shoulder, left/right elbow, left/right wrist
- Hands: left/right pinky, left/right index, left/right thumb
- Lower body: left/right hip, left/right knee, left/right ankle
- Feet: left/right heel, left/right foot_index

## Configuration

### MediaPipe Settings

Edit `video_analysis_service/settings.py`:

```python
MEDIAPIPE_CONFIG = {
    'min_detection_confidence': 0.5,  # Confidence threshold for detection
    'min_tracking_confidence': 0.5,   # Confidence threshold for tracking
    'model_complexity': 1,             # 0, 1, or 2 (higher = more accurate but slower)
}
```

### Video Processing Settings

```python
VIDEO_PROCESSING_CONFIG = {
    'frame_interval': 0.2,          # Process frame every N seconds
    'max_video_duration': 600,      # Maximum video duration (10 minutes)
}
```

## Troubleshooting

### Import Error for MediaPipe
If you get import errors, try:
```bash
pip install --upgrade mediapipe opencv-python
```

### MongoDB Connection Error
Ensure MongoDB is running:
```bash
docker-compose up -d mongodb
```

### Video File Not Found
Check that:
1. The video exists in MongoDB's `videos` collection
2. The `filename` field in the video document is correct
3. The file exists at `VIDEO_STORAGE_PATH/{filename}`

### Debug Visualizations
- All processed frames are saved as PNG images in `debug_output/{video_id}/`
- Images are named `frame_0000.png`, `frame_0001.png`, etc.
- The `debug_output/` directory is in `.gitignore` and can be safely deleted

## Development

### Run Tests
```bash
python manage.py test
```

### Create Superuser (for Django admin)
```bash
python manage.py createsuperuser
```

### View Logs
The service prints detailed logs including:
- Video processing progress
- Frame processing count
- MediaPipe detection results
- MongoDB operations
