# Video Processing Service

A microservice that extracts pose landmarks from presentation videos using MediaPipe Pose Detection.

## What This Service Does

This service processes video files to detect and extract human pose landmarks:
- Identifies 33 body keypoints (nose, eyes, shoulders, hips, etc.)
- Tracks body position and movement frame-by-frame
- Stores landmark data in database for downstream analysis
- Provides foundation for gesture, posture, and movement analysis

## How Pose Detection Works

### MediaPipe Pose
This service uses Google's MediaPipe Pose detection model.

**Why MediaPipe?**
- State-of-the-art accuracy for pose detection
- Real-time performance (60+ fps capable)
- Works in various conditions (lighting, angles, clothing)
- Pre-trained on millions of images
- Free and open-source

**Model capabilities:**
- Detects 33 3D landmarks on the human body
- Works with single-person videos (presentation scenario)
- Provides confidence scores for each detection
- Robust to partial occlusions

### 33 Pose Landmarks Detected

**Face:** nose, eyes (inner/outer), ears, mouth

**Torso:** shoulders, hips

**Arms:** elbows, wrists, hands (pinky, index, thumb)

**Legs:** knees, ankles, heels, feet

Each landmark provides:
- **X coordinate:** Horizontal position (0-1, normalized)
- **Y coordinate:** Vertical position (0-1, normalized)
- **Z coordinate:** Depth relative to hips (can be negative)
- **Visibility:** Confidence score (0-1, higher = more confident)

## Processing Pipeline

### Step 1: Get Video Path
Retrieves video file location from database.

**Input:** Recording ID
**Output:** Absolute path to video file

### Step 2: Initialize MediaPipe Pose
Configures the pose detection model.

**Configuration (set in `.env`):**
- `MIN_DETECTION_CONFIDENCE` (default: 0.5): Minimum confidence to detect a person
- `MIN_TRACKING_CONFIDENCE` (default: 0.5): Minimum confidence to track across frames
- `MODEL_COMPLEXITY` (0/1/2): Higher = more accurate but slower

### Step 3: Process Video Frames
Reads and analyzes video frame-by-frame.

**Frame selection:**
- `FRAME_INTERVAL`: Process every Nth frame (default: 1 = all frames)
- Example: FRAME_INTERVAL=2 processes every other frame (reduces processing time)

**Per-frame processing:**
1. Read frame from video
2. Convert BGR (OpenCV) to RGB (MediaPipe)
3. Run pose detection
4. Extract all 33 landmarks
5. Store in database with timestamp

### Step 4: Store Landmarks in Database
Saves frame data and landmarks to PostgreSQL.

**Database schema:**
```
frame_data:
  - recording_id
  - timestamp
  - frame_index

landmark:
  - frame_data_id
  - type (e.g., 'left_hip', 'right_wrist')
  - x, y, z (coordinates)
  - visibility (confidence)
```

**Batch insertion:**
- Processes all landmarks for a frame
- Inserts in batches for performance
- Uses database transactions for consistency

### Step 5: Return Results
Provides summary of processed video.

**Response includes:**
- Total frames processed
- Duration of video
- FPS (frames per second)
- Landmarks extracted per frame

## API Endpoints

### Health Check
```
GET /api/v1/health
```

### Analyze Video
```
POST /api/v1/video/{recording_id}/analyze/
```

**Parameters:**
- `recording_id` (int): Database ID of the recording

**Response:**
```json
{
  "success": true,
  "recording_id": 1,
  "total_frames": 900,
  "duration": 60.0,
  "fps": 15.0,
  "landmarks_per_frame": 33
}
```

## Configuration

Set in `.env` file:

```bash
# MediaPipe Configuration
MIN_DETECTION_CONFIDENCE=0.5  # Higher = fewer false positives
MIN_TRACKING_CONFIDENCE=0.5   # Higher = more stable tracking
MODEL_COMPLEXITY=1            # 0=fastest, 2=most accurate

# Video Processing
FRAME_INTERVAL=1              # Process every Nth frame
MAX_VIDEO_DURATION=600        # Maximum video length (seconds)

# Video storage path
VIDEO_STORAGE_PATH=D:/VideoData

# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fluent
DB_USERNAME=postgres
DB_PASSWORD=your_password
```

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `.env` file

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver 8001
```

The service will be available at `http://localhost:8001`

## Dependencies

- **OpenCV (cv2)**: Video reading and frame processing
- **MediaPipe**: Pose detection and landmark extraction
- **Django**: Web framework
- **PostgreSQL**: Database for landmark storage
- **requests**: HTTP client for service communication

## Technical Notes

### Data Flow:
1. Video uploaded → Stored in VIDEO_STORAGE_PATH → Recording created in database
2. This service → Reads video → Extracts landmarks → Stores in database
3. Other services → Query landmarks from database → Perform specific analyses

### Performance:
- **Speed:** ~30-60 fps on modern CPU (model_complexity=1)
- **Optimization:** Increase FRAME_INTERVAL to process fewer frames
- **Example:** 5-minute video at 30fps = 9,000 frames
  - FRAME_INTERVAL=1: Process all 9,000 frames (~3-5 minutes)
  - FRAME_INTERVAL=2: Process 4,500 frames (~1.5-2.5 minutes)

### Coordinate System:
- **X, Y:** Normalized to frame size (0.0 to 1.0)
- **Z:** Depth relative to hips (negative = behind, positive = in front)
- **Visibility:** 0.0 (not visible) to 1.0 (very confident)

### Error Handling:
- If no person detected in frame → Skips frame (no landmarks stored)
- If partial detection → Stores only visible landmarks
- If video too long → Stops at MAX_VIDEO_DURATION

## Debug Output

Debug visualizations saved to: `debug_output/{recording_id}/`

**Visualizations may include:**
- Pose skeleton overlay on video frames
- Landmark positions over time
- Detection confidence plots

## Example Usage

```bash
# Analyze video for recording ID 1
curl -X POST http://localhost:8001/api/v1/video/1/analyze/
```

## Landmark Types

Full list of 33 landmarks tracked:

**Head/Face (11 landmarks):**
- nose, left_eye_inner, left_eye, left_eye_outer
- right_eye_inner, right_eye, right_eye_outer
- left_ear, right_ear, mouth_left, mouth_right

**Upper Body (10 landmarks):**
- left_shoulder, right_shoulder
- left_elbow, right_elbow
- left_wrist, right_wrist
- left_pinky, right_pinky
- left_index, right_index
- left_thumb, right_thumb

**Lower Body (12 landmarks):**
- left_hip, right_hip
- left_knee, right_knee
- left_ankle, right_ankle
- left_heel, right_heel
- left_foot_index, right_foot_index

## Downstream Services

This service provides data for:
- **arm_movement_analysis_ms:** Analyzes wrist/elbow kinematics
- **eye_contact_analysis_ms:** Analyzes head pose and gaze direction
- **hip_analysis_ms:** Analyzes hip positioning and body stability
- Future services: Posture analysis, gesture recognition, etc.

## Performance Tuning

### For faster processing:
- Increase `FRAME_INTERVAL` (process fewer frames)
- Decrease `MODEL_COMPLEXITY` to 0
- Lower `MIN_DETECTION_CONFIDENCE` if missing detections

### For better accuracy:
- Set `FRAME_INTERVAL=1` (process all frames)
- Increase `MODEL_COMPLEXITY` to 2
- Increase `MIN_DETECTION_CONFIDENCE` to 0.7+
- Ensure good video quality and lighting

## Common Issues

### No landmarks detected:
- Check video quality and lighting
- Lower MIN_DETECTION_CONFIDENCE
- Ensure person is fully visible in frame
- Verify MODEL_COMPLEXITY is appropriate

### Slow processing:
- Increase FRAME_INTERVAL
- Decrease MODEL_COMPLEXITY
- Check system resources (CPU usage)

### Jittery tracking:
- Increase MIN_TRACKING_CONFIDENCE
- Process more frames (lower FRAME_INTERVAL)
- Improve video quality

## Future Improvements

- Multi-person detection support
- Real-time processing for live presentations
- Skeleton visualization overlay export
- Automatic video quality assessment
- GPU acceleration for faster processing
- Smart frame selection (skip static frames)
