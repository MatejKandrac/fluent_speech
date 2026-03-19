# TODO — Missing and Incomplete Features

This file documents features that are not yet implemented, partially implemented, or have known TODOs in the codebase.
Items are grouped by category. Each item includes a suggested implementation approach.

---

## 1. Audio Processing — Noise Reduction

**Service:** `audio_processing_ms`
**Status:** `# TODO` comment in `services.py` (Step 5 of pipeline is a stub)
**Impact:** Recordings made in noisy environments will produce lower-quality audio, degrading pitch, volume, and transcription accuracy.

### Suggested Solution
Use the [`noisereduce`](https://github.com/timsainb/noisereduce) library, which implements spectral gating noise reduction.

```python
import noisereduce as nr

# Use the first 0.5s of audio as a noise profile (assumes silence at start)
noise_sample = audio[:int(0.5 * sample_rate)]
reduced = nr.reduce_noise(y=audio, sr=sample_rate, y_noise=noise_sample)
```

An alternative is `speechbrain` for deep-learning-based enhancement if quality is more critical than speed.

---

## 2. Pitch Analysis — Database Persistence

**Service:** `pitch_analysis_ms`
**Status:** `# TODO` comment in `services.py` (Step 5 is a stub)
**Impact:** Pitch statistics are only returned in the HTTP response and are lost afterwards. Cannot be retrieved, compared over time, or included in a final feedback report.

### Suggested Solution
Create a `PitchResult` Django model and save it after analysis:

```python
# models.py
class PitchResult(models.Model):
    recording = models.OneToOneField(Recording, on_delete=models.CASCADE)
    pitch_mean = models.FloatField()
    pitch_min = models.FloatField()
    pitch_max = models.FloatField()
    pitch_std = models.FloatField()
    pitch_frames = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

Also add a `GET /api/v1/pitch/{recording_id}/` retrieval endpoint for use by a future aggregation layer.

---

## 3. Volume Analysis — Database Persistence

**Service:** `volume_analysis_ms`
**Status:** `# TODO` comment in `services.py` (Step 5 is a stub)
**Impact:** Same as pitch — volume statistics are ephemeral and cannot be retrieved or aggregated later.

### Suggested Solution
Same pattern as pitch:

```python
# models.py
class VolumeResult(models.Model):
    recording = models.OneToOneField(Recording, on_delete=models.CASCADE)
    volume_mean = models.FloatField()
    volume_min = models.FloatField()
    volume_max = models.FloatField()
    volume_std = models.FloatField()
    volume_frames = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

Add a `GET /api/v1/volume/{recording_id}/` retrieval endpoint.

---

## 4. API Gateway — Full Analysis Pipeline Orchestration

**Service:** `FluentApiGateway`
**Status:** Only `VideoAnalysisService` and `AudioAnalysisService` are triggered after upload. No other analysis services are triggered automatically.
**Impact:** After a video is uploaded, the following analyses are **never automatically started**:
- Arm movement analysis (`arm_movement_analysis_ms`)
- Eye contact analysis (`eye_contact_analysis_ms`)
- Hip analysis (`hip_analysis_ms`)
- Pitch analysis (`pitch_analysis_ms`)
- Volume analysis (`volume_analysis_ms`)
- Filler words analysis (`filler_words_analysis_ms`)

Currently, each of these must be triggered manually via their individual HTTP endpoints.

### Suggested Solution

The challenge is that these analyses have dependencies:
- **Arm / Eye / Hip** depend on video processing completing first
- **Pitch / Volume** depend on audio processing completing first
- **Filler words** depend on transcription completing first (which depends on audio processing)

**Option A — Polling / Callback in each analysis service**
After `video_processing_ms` finishes, it calls back to the gateway or directly triggers dependent services.

**Option B — Add a dedicated orchestration endpoint in the API Gateway**
Add `POST /api/v1/recordings/{id}/analyze-all/` that sequentially triggers all services with appropriate wait logic.

**Option C — Async chain: each service triggers the next**
After video processing completes, it calls arm/eye/hip services. After audio processing, it calls pitch/volume. After transcription, it calls filler words. This is already partially in place (audio triggers transcription via `AUTO_TRIGGER_TRANSCRIPTION`).

Option C is the lowest-effort approach given the existing pattern.

---

## 5. Unified Feedback Report / Aggregation

**Service:** Missing entirely
**Status:** Not implemented
**Impact:** There is no single endpoint that collates results from all 7 analysis services into a structured feedback report. The Flutter app has no way to show a complete picture of the presentation analysis.

### Suggested Solution

Add a `GET /api/v1/recordings/{id}/report/` endpoint to the API Gateway that:
1. Queries each analysis service (or reads their DB results) for the given `recording_id`
2. Computes a normalized score per category (e.g. 0–100)
3. Returns a unified JSON structure:

```json
{
  "recording_id": 1,
  "overall_score": 72,
  "categories": {
    "eye_contact": {
      "score": 85,
      "looking_at_audience_pct": 84.8,
      "feedback": "Good eye contact. Try to scan wider."
    },
    "arm_movement": {
      "score": 60,
      "avg_velocity": 0.19,
      "feedback": "Some periods without gestures detected."
    },
    "pitch": {
      "score": 45,
      "pitch_std": 8.2,
      "feedback": "Speech sounds monotone. Vary your intonation more."
    },
    "volume": { ... },
    "filler_words": { ... },
    "hip_stability": { ... }
  }
}
```

The scoring thresholds should be configurable and informed by the experimental results from the thesis.

---

## 6. Flutter App — Analysis Results Display Screen

**Service:** `fluent` (mobile app)
**Status:** The app records and uploads video, but has no screen to display analysis results
**Impact:** Users cannot see any feedback — the core purpose of the thesis is not visible to the user.

### Suggested Solution

Add an "Analysis Results" screen in Flutter that:
1. Fetches the report from `GET /api/v1/recordings/{id}/report/` (see item 5)
2. Displays per-category scores with visual indicators (e.g. progress bars, color coding)
3. Shows the debug visualization images (plots) returned or stored by each microservice
4. Optionally shows a timeline view combining all analyses

The screen can be navigated to from the recording history list after analysis is complete.

---

## 7. Transcript Retrieval Endpoint

**Service:** `transcript_processing_ms`
**Status:** Words are stored in the `word` table in PostgreSQL, but there is no GET endpoint to retrieve them
**Impact:** The Flutter app or other services cannot fetch the full transcript text for display or further processing.

### Suggested Solution

Add:
```
GET /api/v1/transcript/{recording_id}/
```

Response:
```json
{
  "recording_id": 1,
  "detected_language": "sk",
  "words": [
    { "word": "hello", "start_time": 0.5, "end_time": 0.9, "probability": 0.98 }
  ],
  "full_text": "hello world..."
}
```

This would also allow the mobile app to display the full transcript alongside timestamps.

---

## 8. Docker Compose — Missing Dependencies and Port Conflict

**File:** `docker-compose.yml`
**Status:** Two minor issues

### Issue A — Missing `depends_on` for `filler_words` and `transcript_service`
`filler_words` and `transcript_service` containers do not have a `depends_on: timescaledb` condition, meaning they may start before the database is ready.

**Fix:** Add to both services:
```yaml
depends_on:
  timescaledb:
    condition: service_healthy
```

### Issue B — Port variable reuse for `filler_words`
The `filler_words` service maps `${EYE_CONTACT_PORT}:8008`, which reuses the eye contact port environment variable instead of its own.

**Fix:** Define `FILLER_WORDS_PORT=8008` in `.env` and update the mapping:
```yaml
ports:
  - '${FILLER_WORDS_PORT}:8008'
```

---

## 9. Authentication / Authorization

**Service:** `FluentApiGateway`
**Status:** `SecurityConfig.kt` exists but API endpoints appear to be open (no user authentication)
**Impact:** Any client on the network can upload/delete videos and trigger analysis

### Suggested Solution

For a diploma thesis context, a simple approach is sufficient:
- **API Key header**: Require `X-API-Key` header on all requests, validated in `SecurityConfig`
- **Or JWT**: Issue a token per user session from a login endpoint

Given the single-user mobile app context, an API key stored in the Flutter app's `--dart-define` at build time would be the simplest approach.

---

## 10. Missing `.env.example` File

**Status:** No example environment file exists at the project root
**Impact:** New developers setting up the project must guess or read code to find required environment variables

### Suggested Solution

Create `.env.example` at the root with all required variables and placeholder values:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fluent
DB_USERNAME=postgres
DB_PASSWORD=changeme

# API Gateway
API_GATEWAY_PORT=8000
VIDEO_STORAGE_PATH=/path/to/video/storage

# Microservice URLs
VIDEO_ANALYSIS_SERVICE_URL=http://localhost:8001
AUDIO_ANALYSIS_SERVICE_URL=http://localhost:8004
TRANSCRIPT_SERVICE_URL=http://localhost:8009

# Analysis service ports (for docker-compose)
VIDEO_ANALYSIS_PORT=8001
ARM_MOVEMENT_PORT=8002
EYE_CONTACT_PORT=8003
AUDIO_ANALYSIS_PORT=8004
PITCH_ANALYSIS_PORT=8005
VOLUME_ANALYSIS_PORT=8006
HIP_ANALYSIS_PORT=8007
FILLER_WORDS_PORT=8008
TRANSCRIPT_SERVICE_PORT=8009

# MediaPipe (video_processing_ms)
MIN_DETECTION_CONFIDENCE=0.5
MIN_TRACKING_CONFIDENCE=0.5
MODEL_COMPLEXITY=1
FRAME_INTERVAL=1
MAX_VIDEO_DURATION=600

# Whisper (transcript_processing_ms)
WHISPER_MODEL=base

# Audio processing
AUTO_TRIGGER_TRANSCRIPTION=True
```
