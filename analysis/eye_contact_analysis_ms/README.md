# Eye Contact Analysis Service

A microservice that analyzes head pose and gaze direction in presentation videos to provide feedback on eye contact with the audience.

## What This Service Does

- Computes rotation-invariant yaw (left-right) and pitch (up-down) head angles from MediaPipe landmarks
- Detects when the presenter looks away from the audience zone, stares at one spot, or turns their back
- Builds a 2D gaze heatmap (yaw × pitch) showing time spent in each direction
- Sends a per-second "fraction of frames outside audience zone" series to the segmentation service

## Analysis Pipeline

### Step 1: Fetch Landmark Data
Retrieves facial and shoulder landmark data from the database (populated by `video_processing_ms`).

**Required landmarks:** nose, left_eye, right_eye, left_ear, right_ear, left_shoulder, right_shoulder

### Step 2: Calculate Head Angles

#### Yaw — rotation-invariant atan2 approach

The interaural axis (3D ear-to-ear vector) is decomposed into its image-plane magnitude and its depth component Δz:

```
yaw = atan2(Δz_ear, ear_image_dist)

where:
  Δz_ear        = right_ear.z - left_ear.z
  ear_image_dist = sqrt(Δx_ear² + Δy_ear²)
```

Using 2D Euclidean distance (not just Δx) makes yaw correct regardless of camera roll or portrait/landscape orientation. The result is bounded to (−90°, +90°) and monotonic across the full range — no calibration needed.

**Sign convention:** positive yaw = turning right (right ear moves away, Δz > 0).

#### Yaw smoothing

A median filter is applied to the Δz signal across a configurable window before recomputing yaw. This suppresses MediaPipe z-depth noise without the plateau artefacts that holding the last valid value produces.

#### Back-facing detection

If `nose.z − shoulder_center.z > BACK_FACING_THRESHOLD`, the presenter is facing away. Yaw and pitch are set to `null` for these frames and excluded from all downstream analysis.

#### Pitch — body-frame projection

The pitch is computed relative to the shoulder axis so it is invariant to camera roll:

```
1. shoulder_unit = (right_shoulder - left_shoulder) / |...|
2. body_up = rotate shoulder_unit 90° CCW → perpendicular, pointing toward head
3. nose_ear_vec = nose - ear_midpoint
4. nose_ear_vertical = dot(nose_ear_vec, body_up)
5. face_radius = inter_ear_distance / 2
6. pitch_raw = atan2(nose_ear_vertical, face_radius)
```

#### Per-video pitch normalization

The raw pitch has a systematic downward bias that varies per video: in MediaPipe image coordinates (y increases downward) the nose projects below the ears even when the presenter looks straight ahead. The offset depends on camera height, distance, and individual anatomy.

After all frames are computed, the **median pitch across the video is subtracted** from every frame. This maps the presenter's typical gaze direction to 0° automatically, without any manual calibration. Yaw does not need this — the atan2 construction is already zero-centred.

### Step 3: Build Heatmap

A 2D grid (yaw bins × pitch bins) accumulates time (in seconds) spent in each direction. The audience zone is overlaid as a green rectangle.

### Step 4: Detect Events

| Event | Condition |
|---|---|
| **Looking away** | yaw or pitch outside audience zone for ≥ `MIN_LOOKING_AWAY_DURATION` ms |
| **Staring** | yaw and pitch both within `STARING_ANGLE_THRESHOLD`° of a running average for ≥ `MIN_STARING_MS` ms |
| **Back-facing** | `facing_back = True` for ≥ `min_back_facing_duration` ms |

### Step 5: Segmentation

A per-second series (fraction of frames outside audience zone) is sent to `segmentation_ms` using the `mean` method to find where overall engagement with the audience shifts.

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Eye Contact
```
POST /api/v1/eye-contact/{recording_id}/analyze/
```

**Response:**
```json
{
  "success": true,
  "recording_id": 3,
  "statistics": {
    "total_duration": 29.87,
    "looking_at_audience_percentage": 84.82,
    "looking_away_percentage": 15.18,
    "back_facing_duration": 0.0,
    "avg_yaw": -2.15,
    "avg_pitch": 1.3,
    "yaw_range": 45.23,
    "pitch_range": 12.4,
    "num_looking_away_events": 3
  },
  "heatmap": {
    "yaw_bins": [-70, -65, ..., 70],
    "pitch_bins": [-30, -25, ..., 30],
    "duration_matrix": [[...], ...],
    "bin_size": { "yaw": 5, "pitch": 5 },
    "shape": { "n_yaw_bins": 28, "n_pitch_bins": 12 }
  },
  "looking_away_events": [
    {
      "start_timestamp": 8.2,
      "end_timestamp": 10.5,
      "duration_seconds": 2.3,
      "avg_yaw": -38.5,
      "avg_pitch": 1.2
    }
  ],
  "staring_events": [...],
  "back_facing_events": [...],
  "audience_zone_thresholds": {
    "yaw_min": -40, "yaw_max": 40,
    "pitch_min": -15, "pitch_max": 15
  },
  "segmentation": { ... }
}
```

## Configuration

```bash
# Heatmap range
YAW_MIN=-70            YAW_MAX=70            YAW_BIN_SIZE=5
PITCH_MIN=-30          PITCH_MAX=30          PITCH_BIN_SIZE=5

# Yaw smoothing (median window over Δz_ear)
YAW_SMOOTHING_WINDOW=5

# Audience zone
AUDIENCE_YAW_MIN=-40   AUDIENCE_YAW_MAX=40
AUDIENCE_PITCH_MIN=-15 AUDIENCE_PITCH_MAX=15

# Event detection
EYE_CONTACT_MIN_LOOKING_AWAY_DURATION=1000   # ms
STARING_ANGLE_THRESHOLD=10                    # degrees
MIN_STARING_MS=2000                           # ms

# Back-facing
BACK_FACING_THRESHOLD=0   # nose.z - shoulder_center.z threshold

# Pitch bias applied after normalization (leave at 0 — normalization handles offset)
PITCH_BIAS=0

# Segmentation
EYE_SEGMENTATION_SENSITIVITY=0.5
```

## Debug Output

`debug_output/{recording_id}/gaze_heatmap_{recording_id}.png` — five subplots:
1. Gaze heatmap (yaw × pitch, time in seconds)
2. Yaw over time (raw + smoothed, with audience zone lines)
3. Pitch over time (after median normalization, with audience zone lines)
4. Z-depth analysis (nose.z, shoulder.z, difference, back-facing threshold)
5. Ear Δz over time (the signal that drives yaw)

## Dependencies

- **matplotlib** — visualization
- **numpy** — heatmap binning
- **requests** — calls segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL
