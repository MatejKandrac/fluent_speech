# Arm Movement Analysis Service

A microservice that analyzes arm movements in presentation videos to provide feedback on gesture usage and movement patterns.

## What This Service Does

- Normalizes wrist landmark positions relative to body size and position
- Computes per-frame wrist velocity and acceleration
- Detects **no-movement periods** (bilateral — both wrists below threshold simultaneously)
- Detects **excessive movement periods** (per-hand, using adaptive Z-score thresholding)
- Sends a 1-second-averaged velocity series to the segmentation service to find where gesture behaviour changes
- Saves a debug visualization of wrist velocity over time

## Analysis Pipeline

### Step 1: Fetch Data
Retrieves pose landmark data from the database for a given recording ID.

### Step 2: Normalize Landmarks
Makes kinematics body-position and body-size independent.

**How it works:**
1. Calculate body center (midpoint between hips)
2. Calculate body scale (distance between shoulders)
3. Transform each landmark: `normalized = (original - center) / scale`

**Result:** All coordinates become relative to the person's body — a presenter close to the camera and one far away produce comparable velocity values.

### Step 3: Calculate Kinematics

**Velocity:** 3D Euclidean distance between consecutive normalized wrist positions.

**Acceleration:** Absolute change in velocity between consecutive frames.

### Step 4: Detect Anomalies

#### No-Movement Detection (bilateral)
A frame is counted as "still" only when **all visible wrists** have smoothed velocity below `NO_MOVEMENT_VELOCITY_THRESHOLD` simultaneously. A single active hand breaks the streak.

This avoids false positives when the presenter gestures with one hand while the other rests.

#### Excessive Movement Detection (per-hand, adaptive Z-score)
An adaptive threshold is computed per recording from the smoothed velocity distribution:

```
excessive_threshold = velocity_mean + Z_SCORE_K × velocity_std
```

Detection is applied to a **rolling-average** of velocity so that single-frame spikes (e.g. a quick tap) are ignored. Nearby events from the same hand are merged to consolidate back-and-forth swings into one period.

### Step 5: Visualize
Saves two-subplot PNG: raw wrist velocity (both wrists) and rolling-average trend, with no-movement (gray) and excessive movement (red) regions shaded.

### Step 6: Segment via PELT
A per-second series (average max-wrist velocity per second) is sent to `segmentation_ms` using the `std` method to find timestamps where gesture behaviour meaningfully changes.

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Arm Movements
```
POST /api/v1/analyze/arm-movements/{recording_id}/
```

**Response:**
```json
{
  "success": true,
  "recording_id": 3,
  "total_frames": 450,
  "normalized_frames_count": 448,
  "visualization_path": "debug_output/3/wrist_kinematics_recording_3.png",
  "statistics": {
    "left_wrist": {
      "avg_velocity": 0.032,
      "max_velocity": 0.38,
      "avg_acceleration": 0.021,
      "max_acceleration": 0.29
    },
    "right_wrist": { "..." }
  },
  "anomalies": {
    "no_movement_periods": [
      {
        "start_timestamp": 4.2,
        "end_timestamp": 12.0,
        "duration_frames": 118
      }
    ],
    "excessive_movement_periods": [
      {
        "wrist": "right",
        "start_timestamp": 22.5,
        "end_timestamp": 24.1,
        "duration_frames": 24
      }
    ],
    "thresholds": {
      "no_movement_velocity_threshold": 0.01,
      "excessive_movement_velocity_threshold": 0.127,
      "excessive_z_score_k": 3.0,
      "velocity_mean": 0.032,
      "velocity_std": 0.031
    }
  },
  "segmentation": {
    "success": true,
    "change_points": { "std": [18.0, 37.0] },
    "segments": { "std": [ "..." ] },
    "penalty_used": 10.0,
    "sensitivity": 0.5
  }
}
```

## Configuration

```bash
# No-movement detection
NO_MOVEMENT_VELOCITY_THRESHOLD=0.01        # Smoothed velocity below which a wrist is "still"
MIN_CONSECUTIVE_DURATION_MS=1000           # Min streak duration to flag as no-movement period

# Excessive movement detection (adaptive Z-score)
EXCESSIVE_Z_SCORE_K=3.0                   # Multiplier: threshold = mean + k * std
EXCESSIVE_ROLLING_WINDOW=15               # Frames in rolling average before detection
EXCESSIVE_MERGE_GAP_MS=500                # Merge nearby excessive events within this gap
EXCESSIVE_MIN_DURATION_MS=1000            # Discard events shorter than this

# Segmentation
SEGMENTATION_SERVICE_URL=http://localhost:8010
ARM_SEGMENTATION_SENSITIVITY=0.5
```

## Dependencies

- **matplotlib** — visualization
- **numpy / math** — numerical computations
- **requests** — calls segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL
