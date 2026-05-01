# Hip Analysis Service

A microservice that detects excessive hip swaying in presentation videos by analyzing lateral movement patterns.

## What This Service Does

- Computes hip center position and hip distance per frame from MediaPipe landmarks
- Automatically selects the axis with higher variance (X for landscape video, Y for portrait)
- Detects **swaying segments**: time windows where the number of significant direction changes exceeds a threshold
- Sends a direction-change time series to the segmentation service to find where sway intensity shifts
- Saves debug plots of hip movement over time

## How Sway Detection Works

Sway is not measured as raw displacement magnitude but as **rhythmic direction reversal** — the pattern that characterizes nervous swaying:

1. **Velocity signal:** first derivative of the lateral hip center position
2. **Direction changes:** frames where velocity changes sign AND amplitude between successive extrema exceeds `MIN_HIP_AMPLITUDE_CHANGE` (filters out micro-jitter)
3. **Sliding window:** a window of `HIP_WINDOW_DURATION_MS` ms slides across the recording; a window is flagged as swaying if it contains ≥ `MIN_HIP_DIRECTION_CHANGES` significant direction changes
4. **Merging:** overlapping or adjacent flagged windows are merged into contiguous swaying segments

**Axis selection:** the service computes variance on both X (lateral) and Y (vertical) axes and uses whichever is higher. This makes detection work correctly regardless of whether the video was shot in landscape or portrait orientation.

## Processing Pipeline

1. Fetch hip landmarks from the database
2. Compute hip center (midpoint of left/right hip) and hip distance per frame
3. Select lateral axis (higher variance of X vs Y)
4. Detect direction changes with amplitude filtering
5. Apply sliding window to find swaying segments
6. Save debug plots
7. Send direction-change density series to segmentation service
8. Return statistics + swaying segments

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Hip Movement
```
POST /api/v1/hip/{recording_id}/analyze/
```

**Response:**
```json
{
  "success": true,
  "recording_id": 1,
  "statistics": {
    "total_frames": 500,
    "valid_frames": 485,
    "hip_sway": {
      "x_mean": 0.502, "x_std": 0.021, "x_range": 0.14,
      "y_mean": 0.701, "y_std": 0.009, "y_range": 0.06
    },
    "hip_distance": {
      "mean": 0.248, "std": 0.008, "min": 0.230, "max": 0.271
    }
  },
  "swaying_segments": [
    {
      "start_timestamp": 12.5,
      "end_timestamp": 24.0,
      "direction_changes": 9
    }
  ],
  "swaying_segments_count": 1,
  "segmentation": { ... }
}
```

## Configuration

```bash
# Sway detection
MIN_HIP_DIRECTION_CHANGES=3       # Direction changes per window to flag as swaying
MIN_HIP_AMPLITUDE_CHANGE=0.015    # Min amplitude (normalized coords) to count a reversal
HIP_WINDOW_DURATION_MS=4000       # Sliding window size in ms

# Segmentation
HIP_SEGMENTATION_BIN_SIZE=5.0
HIP_SEGMENTATION_SENSITIVITY=1
```

## Debug Output

`debug_output/{recording_id}/` — plots of hip center X/Y over time with swaying segments highlighted, and hip distance over time.

## Dependencies

- **matplotlib** — visualization
- **numpy** — signal processing
- **requests** — calls segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL
