# Pitch Analysis Service

A microservice that analyzes pitch (fundamental frequency) in presentation audio to provide feedback on vocal variety and monotony.

## What This Service Does

- Detects monotonous delivery (sustained low pitch variation)
- Measures pitch range and standard deviation across the recording
- Produces a windowed-std time series and sends it to the segmentation service to find where vocal engagement changes
- Saves a debug pitch plot for inspection

## How Pitch Analysis Works

### What is Pitch?
Pitch is the perceived fundamental frequency of the voice, measured in Hertz (Hz).

**Typical ranges:**
- Male voice: 85–180 Hz
- Female voice: 165–255 Hz

Variation matters more than absolute pitch — a speaker who stays at a constant frequency sounds monotonous regardless of whether it is 100 Hz or 200 Hz.

### The YIN Algorithm

This service uses the YIN algorithm via librosa (`librosa.yin`).

**How it works:**
1. Analyzes audio in small frames (1600 samples, ~100ms at 16 kHz)
2. Uses autocorrelation to find periodic patterns
3. Identifies the most likely fundamental frequency per frame
4. Returns a value for every frame, including unvoiced frames

**Known limitation — octave errors:**
YIN can occasionally lock onto the 2nd harmonic of the voice instead of the fundamental, producing a reading that is exactly 2× the true pitch. These spikes appear random and are a well-known property of the algorithm. A median filter (see below) removes most of them.

**Parameters:**
- Frame length: 1600 samples (~100ms at 16 kHz)
- Hop length: 800 samples (~50ms between frames, 20 frames/second)
- Frequency range: 50–300 Hz

### Median Filtering

After YIN extraction, a median filter is applied to the **raw pitch array** (before NaN masking). This removes isolated octave-error spikes while preserving real pitch transitions.

- Applied on raw YIN output so no NaN values interfere with the filter
- Kernel size is configurable via `PITCH_MEDIAN_FILTER_SIZE` (must be odd, default 5)
- A kernel of 5 removes single-frame and 2-frame spikes; increase to 7 or 9 for more aggressive smoothing

### Voiced Frame Detection

After filtering, frames are masked as unvoiced (NaN) when:
- RMS energy is below threshold (silence/noise) — `energy_threshold = 0.02`
- Pitch is below 70 Hz (sub-speech range)

A configurable grace period suppresses frames immediately after a voiced onset to avoid transient artefacts.

### Why Mean Pitch is Not Used for Engagement Analysis

The raw mean is heavily distorted by octave errors even after filtering — a single spike to 280 Hz pulls the mean significantly. Standard deviation of pitch within sliding windows is used instead, as it captures how much the voice is varying regardless of absolute level.

## Processing Pipeline

1. Load `{stem}_processed.wav` from `VIDEO_STORAGE_PATH`
2. Extract pitch with YIN → apply median filter → mask unvoiced frames as NaN
3. Save debug plot to `debug/{recording_id}/pitch.png`
4. Sliding-window std analysis → detect monotonous segments
5. Build windowed-std time series → call segmentation service
6. Return statistics + monotonous segments + segmentation result

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Pitch
```
POST /api/v1/pitch/{recording_id}/analyze/
```

**Response:**
```json
{
  "success": true,
  "recording_id": 5,
  "pitch_frames": 963,
  "voiced_frames": 573,
  "pitch_mean": 107.6,
  "pitch_min": 76.6,
  "pitch_max": 290.7,
  "pitch_std": 25.3,
  "monotonous_segments": [
    {
      "start_timestamp": 3.85,
      "end_timestamp": 21.25,
      "duration_seconds": 17.4,
      "std_dev": 6.07,
      "range": 25.77
    }
  ],
  "monotonous_segments_count": 1,
  "segmentation": {
    "success": true,
    "change_points": { "std": [13.1, 26.6] },
    "segments": { "std": [ ... ] },
    "penalty_used": 22.361,
    "sensitivity": 0.2
  }
}
```

### Get Pitch Timeseries
```
GET /api/v1/pitch/{recording_id}/timeseries/
```

Returns the per-frame pitch values with timestamps, used by the filler words service for uhh detection.

## Interpreting Monotonous Segments

| std_dev | Assessment |
|---------|-----------|
| < 6 Hz  | Monotonous — very flat delivery |
| 6–15 Hz | Acceptable variation |
| > 15 Hz | Good vocal variety |

Segments shorter than `MONOTONOUS_MIN_DURATION_MS` are discarded. Segments with a gap smaller than `MONOTONOUS_MERGE_GAP_MS` are merged.

## Segmentation Integration

The service sends a windowed-std time series (pitch variability over time) to `segmentation_ms` using the `std` method only. Mean-based segmentation is not used because the absolute pitch level is not a meaningful signal for engagement.

The segmentation result marks timestamps where the speaker's vocal engagement meaningfully changes — e.g. transitioning from a monotonous passage to varied speech.

## Configuration

```bash
# Pitch extraction
PITCH_GRACE_PERIOD_MS=100         # Suppress frames after voiced onset
PITCH_MEDIAN_FILTER_SIZE=5        # Odd integer; 5 removes 1-2 frame spikes

# Monotonous segment detection
MONOTONOUS_WINDOW_SIZE=30         # Frames per sliding window (~1.5s)
MONOTONOUS_STD_THRESHOLD=6.5      # Hz std below which a window is monotonous
MONOTONOUS_RANGE_THRESHOLD=20.0   # Hz range below which a window is monotonous
MONOTONOUS_MERGE_GAP_MS=500       # Merge segments closer than this
MONOTONOUS_MIN_DURATION_MS=1500   # Discard segments shorter than this

# Segmentation service
SEGMENTATION_SERVICE_URL=http://localhost:8010
PITCH_SEGMENTATION_SENSITIVITY=0.2  # 0=fewer segments, 1=more granular
```

## Debug Output

`debug/{recording_id}/pitch.png` — pitch over time with unvoiced regions shaded gray.

**What to look for:**
- Long flat stretches → monotonous delivery
- Isolated spikes → residual octave errors (increase `PITCH_MEDIAN_FILTER_SIZE`)
- Many NaN gaps → energy threshold may be too high

## Dependencies

- **librosa** — YIN pitch extraction, RMS energy
- **scipy** — median filter for spike removal
- **matplotlib** — debug visualization
- **numpy** — numerical computations
- **requests** — calls segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL (recording metadata)
