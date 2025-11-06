# Video Analysis Microservice

Django-based microservice for analyzing videos using MediaPipe to extract pose landmarks.

## Features

- Extract pose landmarks from videos using MediaPipe
- Process videos at configurable frame intervals
- Store analysis results in MongoDB
- RESTful API for triggering video analysis

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
python manage.py runserver 8001
```

## API Endpoints

### POST /api/analyze/video/{video_id}
Analyzes a video and extracts pose landmarks.

**Parameters:**
- `video_id` (path): The MongoDB ID of the video to analyze

**Response:**
```json
{
    "success": true,
    "message": "Video analysis completed successfully",
    "analysis_id": "abc123...",
    "frames_processed": 150,
    "total_frames": 300,
    "duration": 10.0,
    "max_x": 0.987,
    "max_y": 0.923
}
```

**Note:** Debug visualizations are saved for all processed frames in `debug_output/{video_id}/frame_XXXX.png`.
