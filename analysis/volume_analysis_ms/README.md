# Volume Analysis Service

A microservice that analyzes volume levels in presentation audio to identify projection issues and find where a speaker's loudness behaviour changes.

## What This Service Does

- Detects sustained too-soft and too-loud segments using **adaptive thresholds** derived from each recording's own dynamic range
- Converts raw RMS energy to dBFS for perceptually meaningful comparisons
- Sends a 1-second-averaged dBFS time series to the segmentation service to find where volume level meaningfully shifts
- Saves a debug plot showing both RMS and dBFS over time

## How Volume Analysis Works

### RMS → dBFS

Raw RMS energy is extracted per frame and converted to dBFS (decibels relative to full scale):

```
dBFS = 20 * log10(RMS)
```

dBFS is clamped at `VOLUME_SILENCE_FLOOR_DBFS` to avoid log(0). Values closer to 0 are louder; typical speech sits in the −40 to −15 dBFS range.

### Frame Parameters

- Frame length: 2048 samples (~128 ms at 16 kHz)
- Hop length: 800 samples (~50 ms between frames, 20 frames/second)

### Adaptive Thresholds

Rather than fixed dBFS cutoffs, thresholds are derived from each recording's own voiced frames:

```
reference = 75th percentile dBFS of voiced frames (above silence floor)
too_soft  = reference − VOLUME_SOFT_MARGIN_DB
too_loud  = reference + VOLUME_LOUD_MARGIN_DB
```

This makes the service robust to different microphones, room acoustics, and recording distances — a quiet microphone recording is judged against its own baseline, not an absolute value.

### Too-Soft / Too-Loud Detection

Consecutive frames outside the acceptable dBFS range are grouped into violation segments. Segments shorter than `VOLUME_MIN_SEGMENT_MS` are discarded. Frames below `VOLUME_SILENCE_FLOOR_DBFS` are silence and never flagged.

## Processing Pipeline

1. Load `{stem}_processed.wav` from `VIDEO_STORAGE_PATH`
2. Extract RMS per frame → convert to dBFS
3. Compute adaptive thresholds from voiced frames
4. Detect too-soft and too-loud segments
5. Save debug plot to `debug_output/{recording_id}/volume.png`
6. Build 1-second-averaged dBFS series (voiced frames only) → call segmentation service
7. Return statistics + violation segments + segmentation result

## Segmentation Integration

Frames below `VOLUME_SILENCE_FLOOR_DBFS` are excluded when computing each second's average — between-word gaps would otherwise drag the mean down and produce false change points. Only frames where the speaker is actually projecting are averaged. The `mean` method is used.

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Volume
```
POST /api/v1/volume/{recording_id}/analyze/
```

**Response:**
```json
{
  "success": true,
  "recording_id": 5,
  "volume_frames": 963,
  "dbfs_mean": -26.2,
  "dbfs_min": -60.0,
  "dbfs_max": -9.4,
  "adaptive_too_soft_dbfs": -34.5,
  "adaptive_too_loud_dbfs": -14.5,
  "too_soft_segments": [],
  "too_soft_count": 0,
  "too_loud_segments": [],
  "too_loud_count": 0,
  "segmentation": {
    "success": true,
    "change_points": { "mean": [28.0, 41.0] },
    "segments": { "mean": [ ... ] },
    "penalty_used": 144.27,
    "sensitivity": 0.2
  }
}
```

## Configuration

```bash
# Adaptive threshold margins (applied to 75th-percentile voiced reference)
VOLUME_SOFT_MARGIN_DB=9.5           # too_soft = reference − this
VOLUME_LOUD_MARGIN_DB=4.0           # too_loud = reference + this

# Absolute bounds
VOLUME_SILENCE_FLOOR_DBFS=-60.0    # Below this = silence, not flagged
VOLUME_MIN_SEGMENT_MS=700           # Ignore violations shorter than this

# Segmentation
SEGMENTATION_SERVICE_URL=http://localhost:8010
VOLUME_SEGMENTATION_SENSITIVITY=0.2
```

## Debug Output

`debug_output/{recording_id}/volume.png` — two subplots: RMS energy (top) and dBFS with adaptive threshold lines and shaded violation segments (bottom).

**What to look for:**
- Sustained region below the soft threshold line → too-soft segment
- Sustained region above the loud threshold line → too-loud segment
- Deep dips to silence floor between words → normal speech rhythm, not violations

## Dependencies

- **librosa** — RMS feature extraction
- **matplotlib** — debug visualization
- **numpy** — numerical computations
- **requests** — calls segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL (recording metadata)
