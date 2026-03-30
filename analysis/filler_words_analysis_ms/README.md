# Filler Words Analysis Service

A microservice that detects filler words and non-verbal fillers (uhh sounds) in speech, computes usage statistics, and identifies where usage rate shifts during the presentation.

## What This Service Does

- Reads pre-transcribed words from the database (no re-transcription)
- Detects Slovak and English filler words using word-boundary regex matching
- Detects non-verbal uhh/umm sounds by cross-referencing inter-word gaps with pitch stability from the pitch analysis service
- Computes usage statistics and per-minute rate
- Sends a binned count time series to the segmentation service to find where filler word rate changes
- Saves debug visualisations and uhh audio clips

## How Detection Works

### Word-Level Filler Detection

Words are fetched from the `word` table (populated by `transcript_processing_ms`). For each word, trailing `.` and `,` are stripped before matching — Whisper sometimes appends punctuation to words.

Matching uses `\b` word boundaries to avoid partial matches (e.g. "so" won't match "something").

### Uhh Detection via Pitch Cross-Reference

Inter-word gaps (silence between consecutive words) are inspected using the pitch timeseries from `pitch_analysis_ms`. A gap is classified as an uhh if:

1. Gap duration ≥ `UHH_MIN_GAP_DURATION_MS`
2. The gap contains voiced pitch frames for at least `UHH_MIN_VOICED_DURATION_MS`
3. The pitch std within the gap is below `UHH_PITCH_STD_THRESHOLD` — sustained, flat pitch indicates a held vowel sound rather than silence

This catches sounds like "eeeh" or "umm" that Whisper transcribes as silence gaps.

### Punctuation Stripping

Words loaded from the DB have trailing `.` and `,` stripped at match time only — the database values are preserved unchanged.

## Processing Pipeline

1. Fetch words from `word` table for the recording
2. Reconstruct segments (grouped into ~5s windows)
3. Detect filler words via regex on each word
4. Fetch pitch timeseries from `pitch_analysis_ms`
5. Detect uhh sounds in inter-word gaps
6. Merge all occurrences, compute statistics
7. Save pitch+uhh debug plot; save uhh WAV clips if any detected
8. Save cumulative timeline visualisation (in DEBUG mode)
9. Bin occurrences into `FILLER_SEGMENTATION_BIN_SIZE`-second windows → call segmentation service
10. Return statistics + occurrences + segmentation result

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Filler Words
```
POST /api/v1/filler-words/{recording_id}/analyze/
```

**Prerequisites:** audio must be processed and transcribed first.

**Response:**
```json
{
  "success": true,
  "recording_id": 8,
  "duration": 31.54,
  "detected_language": "unknown",
  "statistics": {
    "total_filler_words": 7,
    "fillers_per_minute": 13.32,
    "most_common_filler": { "word": "ehm", "count": 4 },
    "slovak_fillers_count": 7,
    "english_fillers_count": 0,
    "filler_word_distribution": { "tak": 2, "no": 1, "ehm": 4 },
    "is_high_usage": true
  },
  "filler_occurrences": [ ... ],
  "total_filler_occurrences": 7,
  "uhh_occurrences_count": 0,
  "segmentation": {
    "success": true,
    "change_points": { "mean": [20.0] },
    "segments": { "mean": [ ... ] },
    "penalty_used": 22.361,
    "sensitivity": 0.5
  },
  "message": "Filler words analysis completed successfully."
}
```

## Segmentation Integration

Filler word occurrences are binned into `FILLER_SEGMENTATION_BIN_SIZE`-second windows (default 10s). The count per bin is the time series value — no further pre-processing needed since this is already a coarse, noise-free signal. Only the `mean` method is used to find where the usage rate shifts.

Empty bins are excluded from the series (except t=0 as an anchor) to avoid PELT treating zero-count gaps as change points.

**Bin size tuning:** for short recordings (30–60s), 10s bins give 3–6 points, which is the minimum useful range. Lower to 5s (`FILLER_SEGMENTATION_BIN_SIZE=5.0`) for finer granularity.

## Debug Output

`debug_output/{recording_id}/`:
- `pitch_uhh.png` — pitch over time with word spans (blue) and detected uhh gaps (orange)
- `uhh_1_{start}s.wav`, `uhh_2_{start}s.wav`, ... — audio clips of each detected uhh (always saved when detections exist)
- `filler_words_timeline_{recording_id}.png` — cumulative step chart of filler word count over time (DEBUG mode only)

`segmentation_ms/debug_output/filler_{recording_id}/segmentation.png` — PELT segmentation of the binned count series.

## Configuration

```bash
# Detection thresholds
HIGH_FILLER_THRESHOLD=5              # Fillers/minute above which is_high_usage=true
MIN_SPEECH_DURATION=10               # Minimum recording length for analysis (s)

# Uhh detection
UHH_PITCH_STD_THRESHOLD=15.0        # Max pitch std (Hz) for a gap to be classified as uhh
UHH_MIN_GAP_DURATION_MS=400         # Minimum gap length to consider
UHH_MIN_VOICED_DURATION_MS=200      # Minimum voiced content within gap

# Segmentation
SEGMENTATION_SERVICE_URL=http://localhost:8010
FILLER_SEGMENTATION_BIN_SIZE=10.0   # Seconds per bin
FILLER_SEGMENTATION_SENSITIVITY=0.5 # 0=fewer segments, 1=more granular
```

## Dependencies

- **matplotlib** — debug visualisations
- **numpy** — binning and statistics
- **soundfile** — saving uhh audio clips
- **requests** — calls pitch_analysis_ms and segmentation_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL
