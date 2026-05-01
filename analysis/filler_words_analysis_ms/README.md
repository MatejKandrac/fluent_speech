# Filler Words Analysis Service

A microservice that detects filler words and non-verbal fillers (uhh sounds) in speech, computes usage statistics, and identifies time zones where filler rate is significantly elevated.

## What This Service Does

- Reads pre-transcribed words from the database (no re-transcription)
- Detects Slovak and English filler words using word-boundary regex matching
- Detects non-verbal uhh/umm sounds by cross-referencing inter-word gaps with pitch stability from the pitch analysis service
- Computes usage statistics and per-minute rate
- Finds elevated-density time zones using **bottom-up segmentation** of binned filler counts
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

## Peak Zone Detection (Bottom-Up Segmentation)

Instead of PELT change-point detection (which finds regime shifts), the service uses a **bottom-up segmentation** approach to find time zones where filler density is elevated:

1. Divide the presentation into fixed-size bins (`FILLER_SEGMENTATION_BIN_SIZE` seconds each)
2. Compute fillers/minute in each bin
3. **Bottom-up merge:** start with each bin as its own segment; iteratively merge the pair of adjacent segments whose mean rates are most similar; stop when the cheapest remaining merge would join two segments differing by more than `FILLER_BOTTOM_UP_MERGE_K × std(all rates)`
4. **Post-filter:** segments whose mean rate exceeds `overall_rate × FILLER_PEAK_ZONE_MULTIPLIER` are returned as zones

This correctly handles both cases:
- **Uniform distribution** → all segment means ≈ overall mean → no zones flagged → `distribution: "even"`
- **Concentrated usage** → high-density segment(s) isolated → zones returned → `distribution: "concentrated"`

The distribution result feeds directly into `performance_ms` for the fluency score: uniform distribution is penalised more than concentrated (per research finding H2.1).

## Processing Pipeline

1. Fetch words from `word` table for the recording
2. Reconstruct segments (grouped into ~5s windows)
3. Detect filler words via regex on each word
4. Fetch pitch timeseries from `pitch_analysis_ms`
5. Detect uhh sounds in inter-word gaps
6. Merge all occurrences, compute statistics
7. Save pitch+uhh debug plot; save uhh WAV clips if any detected
8. Save cumulative timeline visualisation (in DEBUG mode)
9. Run bottom-up zone detection → save zone density plot
10. Return statistics + occurrences + peak_zones

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
  "peak_zones": {
    "distribution": "concentrated",
    "zones": [
      {
        "start": 10.0,
        "end": 20.0,
        "rate_per_min": 24.0,
        "overall_rate_per_min": 13.3,
        "peak_ratio": 1.8
      }
    ],
    "overall_rate_per_min": 13.3,
    "threshold_multiplier": 2.0
  },
  "message": "Filler words analysis completed successfully."
}
```

## Configuration

```bash
# Detection thresholds
HIGH_FILLER_THRESHOLD=5              # Fillers/minute above which is_high_usage=true
MIN_SPEECH_DURATION=8                # Minimum recording length for analysis (s)
FILLER_MIN_WORD_PROBABILITY=0.5      # Whisper word confidence threshold

# Uhh detection
UHH_PITCH_STD_THRESHOLD=5.0         # Max pitch std (Hz) for a gap to be classified as uhh
UHH_MIN_GAP_DURATION_MS=200         # Minimum gap length to consider
UHH_MIN_VOICED_DURATION_MS=200      # Minimum voiced content within gap

# Bottom-up zone detection
FILLER_SEGMENTATION_BIN_SIZE=10.0   # Seconds per bin (smaller = finer, min ~5s)
FILLER_BOTTOM_UP_MERGE_K=1.0        # Merge stops when cost > k × std(rates)
                                     #   lower (0.5) = more segments, stricter zones
                                     #   higher (2.0) = fewer, broader segments
FILLER_PEAK_ZONE_MULTIPLIER=2.0     # A segment is a zone if rate > multiplier × overall
                                     #   2.0 = strict (few false positives)
                                     #   1.5 = more sensitive
```

## Debug Output

`debug_output/{recording_id}/`:
- `pitch_uhh.png` — pitch over time with word spans (blue) and detected uhh gaps (orange)
- `uhh_1_{start}s.wav`, `uhh_2_{start}s.wav`, ... — audio clips of each detected uhh
- `filler_words_timeline_{recording_id}.png` — cumulative step chart (DEBUG mode only)
- `filler_zones.png` — bar chart of fillers/minute per bin, with segment boundaries, overall average, zone threshold, and zones highlighted in red

## Dependencies

- **matplotlib** — debug visualisations
- **numpy** — binning and statistics
- **soundfile** — saving uhh audio clips
- **requests** — calls pitch_analysis_ms
- **Django / DRF** — web framework
- **psycopg2** — PostgreSQL
