# Segmentation Service

A stateless microservice that finds change points in any time series using the PELT algorithm. Other analysis services call it to identify where a speaker's behaviour meaningfully shifts during a presentation.

## What This Service Does

- Accepts an arbitrary `{time, value}` time series
- Runs PELT change point detection with one or more cost models
- Returns change point timestamps and per-segment statistics (mean, std, min, max)
- Saves a debug plot and JSON to `debug_output/{label}/` on every call

## Algorithm

### PELT (Pruned Exact Linear Time)

PELT finds the globally optimal set of change points by minimising a cost function plus a penalty for adding segments. It is exact (not approximate) and runs in linear time on average.

**Cost models available:**

| Method | ruptures model | What it detects |
|--------|---------------|-----------------|
| `mean` | `l2` | Shifts in the mean level of the signal |
| `std`  | `normal` | Shifts in variance/standard deviation (Gaussian log-likelihood) |

Trend detection is not yet implemented.

### Sensitivity → Penalty Mapping

The penalty controls how many change points PELT is allowed to place — higher penalty means fewer, more significant segments. Rather than exposing the raw penalty value, callers pass a `sensitivity` in `[0, 1]`:

```
sensitivity = 0.0  →  max_penalty  (very few change points, major transitions only)
sensitivity = 1.0  →  min_penalty  (many change points, fine-grained)
```

The mapping is logarithmic so that small changes in sensitivity near 0 have a large effect (coarse control) and changes near 1 have a smaller effect (fine control). Default bounds: min=1.0, max=500.0.

## How Callers Should Prepare Their Time Series

The segmentation service is generic — it knows nothing about pitch, volume, or filler words. Each calling service is responsible for preparing a meaningful signal:

- **Do not send raw frame-level data** if the signal is noisy. Pre-compute a windowed statistic (e.g. rolling std) so PELT sees semantically meaningful values rather than measurement noise.
- **Pitch service** sends windowed pitch std (variability over time) using `method=std` only — mean pitch is not used because octave errors distort it.
- Future services should follow the same pattern: decide which statistic represents the behaviour you want to segment, compute it over an appropriate window, then send it here.

**Series format:**
```json
[
  {"time": 0.65, "value": 4.12},
  {"time": 0.70, "value": 3.98},
  ...
]
```

- `time` — seconds from start of recording
- `value` — the pre-processed signal value at that time
- Minimum 4 points required

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Segment
```
POST /api/v1/segment/
```

**Request body:**
```json
{
  "series": [{"time": 0.65, "value": 4.12}, ...],
  "methods": ["std"],
  "sensitivity": 0.2,
  "label": "pitch_5"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series` | array | Yes | List of `{time, value}` objects |
| `methods` | array | No | Subset of `["mean", "std"]`. Defaults to both. |
| `sensitivity` | float | No | 0–1. Defaults to `SEGMENTATION_DEFAULT_SENSITIVITY`. |
| `label` | string | No | Used to name debug output files. Defaults to `"unknown"`. |

**Response:**
```json
{
  "success": true,
  "change_points": {
    "std": [13.1, 26.6, 38.0]
  },
  "segments": {
    "std": [
      {"start": 0.65, "end": 13.05, "mean": 4.21, "std": 1.83, "min": 0.85, "max": 8.94, "count": 95},
      {"start": 13.1,  "end": 26.6,  "mean": 2.18, "std": 0.91, "min": 0.72, "max": 4.10, "count": 110},
      ...
    ]
  },
  "penalty_used": 22.361,
  "sensitivity": 0.2
}
```

`change_points` contains one list per method — each value is the timestamp (seconds) of the **start** of a new segment.

## Debug Output

On every request the service writes two files to `debug_output/{label}/`:

- **`segmentation.json`** — full response as JSON
- **`segmentation.png`** — one subplot per method showing:
  - The input series in gray
  - Dashed vertical lines at each change point (colour-coded by method)
  - Alternating shaded regions per segment
  - µ and σ annotations at the top of each segment

Use the plot to judge whether the sensitivity is appropriate: too many change points → lower sensitivity, too few → raise it.

## Configuration

```bash
SEGMENTATION_MIN_PENALTY=1.0             # Lower bound on penalty (sensitivity=1)
SEGMENTATION_MAX_PENALTY=500.0           # Upper bound on penalty (sensitivity=0)
SEGMENTATION_DEFAULT_SENSITIVITY=0.5     # Used when caller omits sensitivity
SEGMENTATION_MIN_SEGMENT_SAMPLES=2       # Minimum samples per segment (ruptures min_size)
```

## Dependencies

- **ruptures** — PELT change point detection
- **matplotlib** — debug visualization
- **numpy** — numerical computations
- **Django / DRF** — web framework

## Adding a New Caller

1. Compute your windowed signal (e.g. rolling std over a 1–2 s window)
2. Format as `[{"time": ..., "value": ...}]`
3. POST to `/api/v1/segment/` with an appropriate `sensitivity` and a descriptive `label`
4. Check `debug_output/{label}/segmentation.png` to validate results
5. Add `SEGMENTATION_SERVICE_URL` to the calling service's settings
