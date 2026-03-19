# Arm Movement Analysis Service

A microservice that analyzes arm movements in presentation videos to provide feedback on gesture usage and movement patterns.

## What This Service Does

This service takes pose landmark data from videos and analyzes wrist movements to:
- Detect if the presenter is using gestures appropriately
- Identify periods of excessive or no movement
- Segment the presentation based on behavior changes

## Analysis Pipeline

The service processes data in 6 steps:

### Step 1: Fetch Data
Retrieves pose landmark data from the database for a given recording ID.

### Step 2: Normalize Landmarks
Makes the data body-position and body-size independent.

**Why normalization?**
- Person standing close to camera vs. far away → same shoulder width should = same scale
- Person on left side of frame vs. center → same relative arm position

**How it works:**
1. Calculate body center (midpoint between hips)
2. Calculate body scale (distance between shoulders)
3. Transform each landmark: `normalized = (original - center) / scale`

**Result:** All coordinates become relative to the person's body, making comparisons fair.

### Step 3: Calculate Kinematics
Computes velocity and acceleration for wrist movements.

**Velocity:** How fast is the wrist moving?
- Formula: 3D Euclidean distance between consecutive frames
- Low velocity ≈ 0 → not gesturing (boring)
- High velocity → active gesturing or fidgeting

**Acceleration:** How suddenly does movement change?
- Formula: Change in velocity between frames
- Low acceleration → smooth, controlled gestures (professional)
- High acceleration → jerky, nervous movements (unprofessional)

### Step 4: Generate Visualization
Creates a graph showing velocity and acceleration over time for both wrists.

**Output:** PNG file saved to `debug_output/{recording_id}/wrist_kinematics_recording_{recording_id}.png`

### Step 5: Detect Anomalies
Finds problematic movement patterns.

**No Movement Periods:**
- Velocity stays below threshold for consecutive frames
- Indicates: Static, boring presentation without gestures

**Excessive Movement Periods:**
- Velocity stays above threshold for consecutive frames
- Indicates: Too much movement, fidgeting, nervousness

**Configuration:** Thresholds are set in `.env`:
- `NO_MOVEMENT_VELOCITY_THRESHOLD=0.01`
- `EXCESSIVE_MOVEMENT_VELOCITY_THRESHOLD=0.15`
- `MIN_CONSECUTIVE_FRAMES=5`

### Step 6: Segment by Behavior Changes
Identifies when the presenter changes their movement patterns.

#### Method 1: Average Change Segmentation
Detects **sudden** changes in movement intensity.

**How it works:**
1. Use sliding window to calculate average velocity
2. Compare consecutive windows
3. If change > threshold → create segment

**Detects:**
- Presenter stops using gestures suddenly
- Presenter starts gesturing more
- Presenter switches hands

**Example:** You're presenting calmly (low velocity), then you get excited and start gesturing wildly (high velocity) → segment detected

#### Method 2: Trend Change Segmentation
Detects **gradual** changes in movement patterns.

**How it works:**
1. Use sliding window to calculate trend (linear regression slope)
2. Detect when trend reverses or changes significantly
3. Mark segmentation points

**Trend types:**
- Positive trend → becoming more animated over time
- Negative trend → becoming less animated (getting tired?)
- Near-zero trend → stable gesture pattern

**Detects:**
- Presenter gradually increases gestures (building excitement)
- Presenter gradually decreases gestures (losing energy)
- Presenter switches presentation style mid-way

**Example:** You start presentation static, gradually increase gestures for 30 seconds (positive trend), then maintain that level (trend flattens) → 2 segments detected

#### Cascade Effect Prevention
When a big movement happens (like making a large circle), the sliding window would normally detect it multiple times in a row. To prevent this:

1. Group segments that are too close together (within `MIN_SEGMENT_GAP` frames)
2. Keep only the most significant one (largest `change_magnitude`)

**Configuration:** Set in `.env`:
- `SEGMENTATION_WINDOW_SIZE=15` → how many frames to analyze at once
- `AVERAGE_CHANGE_THRESHOLD=0.08` → minimum change to create segment
- `TREND_CHANGE_THRESHOLD=0.008` → minimum trend change to create segment
- `MIN_SEGMENT_GAP=20` → minimum frames between segments

## API Response Structure

```json
{
  "success": true,
  "recording_id": 3,
  "total_frames": 110,
  "normalized_frames_count": 110,
  "visualization_path": "path/to/graph.png",

  "statistics": {
    "left_wrist": {
      "avg_velocity": 0.19,
      "max_velocity": 1.27,
      "avg_acceleration": 0.15,
      "max_acceleration": 1.01
    },
    "right_wrist": { ... }
  },

  "anomalies": {
    "no_movement_periods": [
      {
        "wrist": "left",
        "start_timestamp": "00:00:01.000",
        "end_timestamp": "00:00:03.000",
        "duration_frames": 30
      }
    ],
    "excessive_movement_periods": [ ... ],
    "thresholds": { ... }
  },

  "segmentation": {
    "average_change": {
      "left_wrist_segments": [
        {
          "frame_index": 28,
          "timestamp": "00:00:01.877",
          "average_before": 0.11,
          "average_after": 0.17,
          "change_magnitude": 0.06,
          "change_type": "increase"
        }
      ],
      "right_wrist_segments": [ ... ]
    },
    "trend_change": {
      "left_wrist_trend_changes": [
        {
          "frame_index": 20,
          "timestamp": "00:00:01.340",
          "trend_before": 0.006,
          "trend_after": -0.006,
          "change_magnitude": 0.012,
          "change_type": "reversal"
        }
      ],
      "right_wrist_trend_changes": [ ... ]
    }
  }
}
```

## Understanding the Results

### Good Presentation Pattern:
- **Velocity:** Moderate, consistent values with occasional peaks
- **Acceleration:** Low baseline with controlled peaks for emphasis
- **Anomalies:** Few or no periods of no movement/excessive movement
- **Segmentation:** 2-5 segments for a typical presentation (intro, main points, conclusion)

### Poor Presentation Pattern:
- **Velocity:** Flat line near 0 (no gestures) OR constantly high (too distracting)
- **Acceleration:** Frequent high spikes (jerky, nervous)
- **Anomalies:** Many periods of no movement or excessive movement
- **Segmentation:** Too many segments (inconsistent behavior) OR no segments (static throughout)

## Configuration Guide

All parameters can be tuned in `.env`:

```bash
# Anomaly Detection
NO_MOVEMENT_VELOCITY_THRESHOLD=0.01       # Lower = more strict
EXCESSIVE_MOVEMENT_VELOCITY_THRESHOLD=0.15 # Higher = more lenient
MIN_CONSECUTIVE_FRAMES=5                   # Minimum duration to flag

# Segmentation
SEGMENTATION_WINDOW_SIZE=15                # Larger = more stable detection
AVERAGE_CHANGE_THRESHOLD=0.08              # Higher = fewer segments
TREND_CHANGE_THRESHOLD=0.008               # Higher = fewer segments
MIN_SEGMENT_GAP=20                         # Prevents cascade detections
```

### Tuning Tips:

**Getting too many segments?**
- Increase `AVERAGE_CHANGE_THRESHOLD` and `TREND_CHANGE_THRESHOLD`
- Increase `MIN_SEGMENT_GAP`
- Increase `SEGMENTATION_WINDOW_SIZE`

**Not detecting changes?**
- Decrease `AVERAGE_CHANGE_THRESHOLD` and `TREND_CHANGE_THRESHOLD`
- Decrease `SEGMENTATION_WINDOW_SIZE`

**Too many anomaly detections?**
- Increase thresholds (make them more lenient)
- Increase `MIN_CONSECUTIVE_FRAMES` (require longer periods)

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

3. Configure `.env` file (see Configuration Guide above)

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

### Analyze Arm Movements
```
POST /api/v1/analyze/arm-movements/{recording_id}/
```

**Example:**
```bash
curl -X POST http://localhost:8002/api/v1/analyze/arm-movements/3/
```

## Example Usage

```python
from movement_api.services import ArmMovementAnalysisService

service = ArmMovementAnalysisService()
result = service.analyze_arm_movements(recording_id=3)

if result['success']:
    print(f"Found {len(result['anomalies']['no_movement_periods'])} no-movement periods")
    print(f"Left wrist average velocity: {result['statistics']['left_wrist']['avg_velocity']:.4f}")
    print(f"Segmented into {len(result['segmentation']['average_change']['left_wrist_segments'])} segments")
else:
    print(f"Error: {result['error']}")
```

## Technical Notes

### Data Flow:
1. Video → Pose Detection (video_analysis_ms) → Landmarks stored in PostgreSQL
2. Landmarks → This service → Movement analysis
3. Analysis results → Returned to client

### Dependencies:
- **matplotlib**: Graph generation
- **Django**: Web framework
- **PostgreSQL**: Database (via TimescaleDB)
- **numpy/math**: Mathematical calculations

### Performance:
- Processes ~100 frames in <1 second
- Typical presentation (5 minutes at 15 fps) = ~4500 frames ≈ 3-5 seconds processing time

## Future Improvements

Potential enhancements:
- Analyze elbow angles for gesture quality
- Detect specific gesture types (pointing, waving, etc.)
- Compare against "ideal" presenter patterns
- Real-time feedback during presentation
- Gesture symmetry analysis (using both hands vs. one hand)
