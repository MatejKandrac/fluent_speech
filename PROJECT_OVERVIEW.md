# Fluent Speech - Project Overview

Multi-platform application for video recording and speech therapy analysis using pose detection and landmark extraction.

## Architecture

The project consists of five main components:

### 1. Flutter Mobile App (`fluent/`)
- **Technology:** Flutter/Dart
- **Purpose:** Record videos with pose/face detection, upload to backend
- **Features:**
  - Real-time pose and face landmark detection using Google ML Kit
  - Video recording with calibration
  - Video upload to API Gateway
  - Local SQLite storage for video metadata

### 2. API Gateway (`FluentApiGateway/`)
- **Technology:** Kotlin + Spring Boot
- **Port:** 8000
- **Purpose:** Central API for video management and authentication
- **Features:**
  - Video upload endpoint with multipart support (up to 500MB)
  - Video storage to file system
  - MongoDB integration for video metadata
  - Automatic triggering of video analysis
  - RESTful API with security configuration

### 3. Video Analysis Microservice (`video_analysis_ms/`)
- **Technology:** Python + Django + MediaPipe
- **Port:** 8001
- **Purpose:** Analyze videos and extract pose landmarks
- **Features:**
  - MediaPipe pose detection (33 landmarks)
  - Frame-by-frame analysis at configurable intervals (default: 0.2s)
  - MongoDB storage for analysis results
  - Debug visualizations with skeleton overlay
  - RESTful API for video analysis

### 4. Hand Movement Analysis Microservice (`hand_movement_analysis_ms/`)
- **Technology:** Python + Django + ruptures
- **Port:** 8002
- **Purpose:** Analyze hand movements and detect significant changes
- **Features:**
  - Hand movement acceleration analysis
  - Change point detection using ruptures library
  - Identifies fast movements and sudden slowdowns
  - Segments classification by importance
  - RESTful API for movement analysis

### 5. Database (MongoDB)
- **Technology:** MongoDB (Docker container)
- **Port:** 27017
- **Collections:**
  - `videos` - Video metadata and file references
  - `analysis` - Pose landmark analysis results

## Quick Start

### 1. Start MongoDB

```bash
docker-compose up -d mongodb
```

### 2. Start API Gateway

```bash
cd FluentApiGateway
./gradlew bootRun
```

Service will be available at `http://localhost:8000`

### 3. Start Video Analysis Microservice

**Windows:**
```bash
cd video_analysis_ms
setup.bat        # First time only
run.bat          # Start the service
```

**Linux/Mac:**
```bash
cd video_analysis_ms
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

Service will be available at `http://localhost:8001`

### 4. Start Hand Movement Analysis Microservice (Optional)

**Windows:**
```bash
cd hand_movement_analysis_ms
setup.bat        # First time only
run.bat          # Start the service
```

**Linux/Mac:**
```bash
cd hand_movement_analysis_ms
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8002
```

Service will be available at `http://localhost:8002`

### 5. Run Flutter App

```bash
cd fluent
flutter pub get
flutter run --dart-define=SERVER_URL=http://10.232.87.136:8000
```

Replace the IP address with your machine's IP address.

## Workflow

1. **Record Video** (Flutter App)
   - User opens the Flutter app
   - Selects exercise mode (face/pose detection)
   - Records video with real-time landmark visualization
   - Enters a name for the recording

2. **Upload Video** (Flutter → API Gateway)
   - Video is uploaded to API Gateway at `/api/v1/videos/upload`
   - API Gateway saves video to file system
   - Video metadata is stored in MongoDB `videos` collection
   - **API Gateway automatically triggers video analysis** (async, non-blocking)
   - Response includes video ID and filename
   - Flutter app saves metadata to local SQLite

3. **Analyze Video** (Automatic - API Gateway → Video Analysis MS)
   - API Gateway makes async POST request to `/api/v1/analyze/video/{video_id}/`
   - Video Analysis service fetches video from file system
   - Processes video frame by frame (every 0.2 seconds)
   - Extracts 33 pose landmarks using MediaPipe
   - Saves debug visualizations to `debug_output/{video_id}/`
   - Stores analysis results in MongoDB `analysis` collection with max_x and max_y coordinates

4. **Retrieve Results**
   - Get analysis: GET `/api/analysis/{analysis_id}/`
   - Get all analyses for a video: GET `/api/analysis/video/{video_id}/`

5. **Analyze Hand Movements** (Optional - Manual Trigger)
   - Call POST `/api/v1/analyze/hand-movements/{video_id}/` on Hand Movement service
   - Service fetches pose data from MongoDB `analysis` collection
   - Calculates hand velocity and acceleration
   - Uses change point detection to find movement segments
   - Returns timestamped segments with fast movements highlighted

## Data Structures

### Video Document (MongoDB - `videos` collection)
```json
{
    "_id": "507f1f77bcf86cd799439011",
    "filename": "abc123-def456.mp4",
    "createdAt": "2024-01-15T10:30:00Z"
}
```

### Video Record (Flutter - SQLite)
```sql
CREATE TABLE video_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mongo_id TEXT NOT NULL,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL
)
```

### Analysis Document (MongoDB - `analysis` collection)
```json
{
    "_id": "65abc123def456789012345",
    "video_id": "507f1f77bcf86cd799439011",
    "created_at": "2024-01-15T10:30:00.000000",
    "total_frames": 150,
    "data": [
        {
            "timestamp": "00:00:00.000000",
            "landmarks": {
                "nose": {"x": 0.5, "y": 0.3, "z": -0.1, "visibility": 0.99},
                "left_shoulder": {"x": 0.4, "y": 0.5, "z": -0.2, "visibility": 0.95},
                "right_shoulder": {"x": 0.6, "y": 0.5, "z": -0.2, "visibility": 0.96}
                // ... 30 more landmarks
            }
        }
        // ... more frames
    ]
}
```

## Environment Configuration

### Root `.env`
```env
DB_USERNAME=fluent
DB_PASSWORD=root
DB_NAME=fluent
DB_HOST=localhost
DB_PORT=27017

API_GW_PORT=8000
API_GW_VIDEO_STORAGE=D:\VideoData

VIDEO_ANALYSIS_SERVICE_URL=http://localhost:8001
```

### Video Analysis `.env` (`video_analysis_ms/.env`)
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

## API Endpoints

### API Gateway (Port 8000)

#### Upload Video
```
POST /api/v1/videos/upload
Content-Type: multipart/form-data

Body:
  video: <file>

Response:
{
    "success": true,
    "message": "Video uploaded successfully",
    "id": "507f1f77bcf86cd799439011",
    "filename": "abc123-def456.mp4",
    "fileSize": 12345678,
    "uploadedAt": "2024-01-15T10:30:00"
}
```

#### Delete Video
```
DELETE /api/v1/videos/{filename}
```

### Video Analysis Service (Port 8001)

#### Health Check
```
GET /api/v1/health/
```

#### Analyze Video
```
POST /api/v1/analyze/video/{video_id}/

Response:
{
    "success": true,
    "message": "Video analysis completed successfully",
    "analysis_id": "65abc123def456789012345",
    "frames_processed": 150,
    "total_frames": 300,
    "duration": 10.0,
    "max_x": 0.987,
    "max_y": 0.923
}
```

#### Get Analysis
```
GET /api/analysis/{analysis_id}/
```

#### Get Video Analyses
```
GET /api/analysis/video/{video_id}/
```

#### Delete Analysis
```
DELETE /api/analysis/{analysis_id}/delete/
```

### Hand Movement Analysis Service (Port 8002)

#### Health Check
```
GET /api/v1/health/
```

#### Analyze Hand Movements
```
POST /api/v1/analyze/hand-movements/{video_id}/

Response:
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
            }
        ]
    },
    "right_hand": { ... }
}
```

## Development Tools

### Test Video Analysis API
```bash
cd video_analysis_ms
python test_api.py <video_id>
```

### Test HTTP Requests
Use the `requests.http` file in the root directory with your IDE's HTTP client.

## Troubleshooting

### Video Upload Issues
- Check multipart boundary is specified in Content-Type header
- Verify file path uses forward slashes in `.http` files
- Ensure video file exists and is accessible

### Video Analysis Issues
- Check MongoDB is running: `docker ps`
- Verify video file exists at `VIDEO_STORAGE_PATH`
- Check service logs for MediaPipe errors
- Ensure Python dependencies are installed correctly

### Flutter App Issues
- Verify SERVER_URL is set correctly in run configuration
- Check network connectivity to API Gateway
- Ensure camera permissions are granted on device

## Technologies Used

- **Frontend:** Flutter 3.9.0, Dart
- **Backend:** Kotlin, Spring Boot, Django 5.1
- **ML/CV:** MediaPipe 0.10.20, OpenCV 4.10, Google ML Kit
- **Database:** MongoDB, SQLite (Flutter)
- **Infrastructure:** Docker, Gradle

## License

This is a diploma thesis project.
