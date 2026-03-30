# Volume Analysis Service

A microservice that analyzes volume levels in presentation audio to identify projection issues and find where a speaker's loudness behaviour changes.

## What This Service Does

- Detects sustained too-soft and too-loud segments relative to configurable dBFS thresholds
- Converts raw RMS energy to dBFS for perceptually meaningful comparisons
- Sends a 1-second-averaged dBFS time series to the segmentation service to find where volume level meaningfully shifts
- Saves a debug plot showing both RMS and dBFS over time

## How Volume Analysis Works

### RMS → dBFS

Raw RMS energy is extracted per frame and converted to dBFS (decibels relative to full scale):

```
dBFS = 20 * log10(RMS)
```

dBFS is clamped at `VOLUME_SILENCE_FLOOR_DBFS` to avoid log(0). Values closer to 0 are louder; typical speech sits in the -40 to -15 dBFS range.

### Frame Parameters

- Frame length: 2048 samples (~128ms at 16 kHz)
- Hop length: 800 samples (~50ms between frames, 20 frames/second)

### Too-Soft / Too-Loud Detection

Consecutive frames outside the acceptable dBFS range are grouped into violation segments. Segments shorter than `VOLUME_MIN_SEGMENT_MS` are discarded.

| Zone | Threshold | Meaning |
|------|-----------|---------|
| Silence | below `VOLUME_SILENCE_FLOOR_DBFS` | Not flagged — not speech |
| Too soft | `VOLUME_SILENCE_FLOOR_DBFS` to `VOLUME_TOO_SOFT_DBFS` | Audible but too quiet |
| Normal | `VOLUME_TOO_SOFT_DBFS` to `VOLUME_TOO_LOUD_DBFS` | Acceptable range |
| Too loud | above `VOLUME_TOO_LOUD_DBFS` | Clipping risk / uncomfortable |

## Processing Pipeline

1. Load `{stem}_processed.wav` from `VIDEO_STORAGE_PATH`
2. Extract RMS per frame → convert to dBFS
3. Detect too-soft and too-loud segments
4. Save debug plot to `debug/{recording_id}/volume.png`
5. Build 1-second-averaged dBFS series → call segmentation service
6. Return statistics + violation segments + segmentation result

## Segmentation Integration

Frames below `VOLUME_TOO_SOFT_DBFS` are excluded when computing each second's average — between-word gaps (which sit in the -40 to -55 dBFS range) would otherwise drag the mean down and produce false change points. Only frames where the speaker is actually projecting are averaged.

The `mean` method is used. `std`-based segmentation was evaluated but found to be insufficiently discriminative on typical speech recordings.

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
  "volume_mean_rms": 0.0712,
  "volume_min_rms": 0.0001,
  "volume_max_rms": 0.342,
  "volume_std_rms": 0.058,
  "dbfs_mean": -26.2,
  "dbfs_min": -60.0,
  "dbfs_max": -9.4,
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
# dBFS thresholds
VOLUME_TOO_SOFT_DBFS=-35.0          # Below this (but above silence) = too quiet
VOLUME_TOO_LOUD_DBFS=-10.0          # Above this = too loud
VOLUME_SILENCE_FLOOR_DBFS=-60.0     # Below this = silence, not flagged
VOLUME_MIN_SEGMENT_MS=1000          # Ignore violations shorter than this

# Segmentation
SEGMENTATION_SERVICE_URL=http://localhost:8010
VOLUME_SEGMENTATION_SENSITIVITY=0.2  # 0=fewer segments, 1=more granular
```

## Debug Output

`debug/{recording_id}/volume.png` — two subplots: RMS energy (top) and dBFS with threshold lines and shaded violation segments (bottom).

**What to look for:**
- Sustained region below the orange line → too-soft segment
- Sustained region above the red line → too-loud segment
- Deep dips to silence floor between words → normal speech rhythm, not violations

## Dependencies

- **librosa** — RMS feature extraction
- **matplotlib** — debug visualization
- **numpy** — numerical computations
- **requests** — calls segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL (recording metadata)
