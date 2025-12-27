# Volume Analysis Service

A microservice that analyzes volume levels in presentation audio to provide feedback on speaking dynamics and voice projection.

## What This Service Does

This service analyzes the volume (loudness) of a speaker's voice to identify:
- Consistent volume levels
- Dynamic range (how much volume varies)
- Quiet or loud sections
- Volume trends over time

## How Volume Analysis Works

### What is RMS Energy?
RMS (Root Mean Square) Energy is a measure of the power/loudness of an audio signal.

**Why RMS instead of amplitude?**
- Better represents perceived loudness
- Smooths out rapid fluctuations
- Standard metric in audio engineering
- Correlates with how humans perceive volume

**RMS calculation:**
```
RMS = sqrt(mean(signal^2))
```

### Frame-Based Analysis
Audio is analyzed in overlapping frames for smooth tracking.

**Parameters:**
- Frame length: 2048 samples (~128ms at 16kHz)
- Hop length: 800 samples (~50ms between frames)
- Result: 20 volume measurements per second

## Processing Pipeline

### Step 1: Load Processed Audio
Loads the preprocessed audio file created by audio_processing_ms.

**Input:** `{filename}_processed.wav`
- 16 kHz sample rate
- Mono channel
- Normalized amplitude (peak = 1.0)

### Step 2: Extract Volume (RMS Energy)
Calculates RMS energy for each frame using librosa.

**Output:** Array of RMS values for each frame

**Interpretation:**
- High RMS: Loud speaking, good projection
- Low RMS: Quiet speaking, poor projection
- Variation: Dynamic, engaging delivery

### Step 3: Generate Visualization
Creates a plot showing volume over time.

**Plot features:**
- Time (seconds) on X-axis
- RMS Energy on Y-axis
- Mean RMS displayed in title
- Shows volume dynamics clearly

**Output:** `debug/{recording_id}/volume.png`

### Step 4: Calculate Statistics
Computes summary statistics for the entire recording.

**Metrics:**
- Mean RMS: Average volume level
- Min/Max RMS: Volume range
- Standard deviation: Measure of volume variation

### Step 5: Save to Database
**TODO:** Store volume data for long-term analysis and feedback generation.

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Volume
```
POST /api/v1/volume/{recording_id}/analyze/
```

**Parameters:**
- `recording_id` (int): Database ID of the recording

**Response:**
```json
{
  "success": true,
  "recording_id": 1,
  "volume_frames": 3600,
  "volume_mean": 0.125,
  "volume_min": 0.008,
  "volume_max": 0.456,
  "volume_std": 0.082
}
```

## Interpreting Results

### Good Volume Dynamics:
- **Standard deviation:** 0.05-0.15 (normalized audio)
- **Range:** Clear difference between quiet and loud sections
- Shows emphasis on important points
- Keeps audience engaged

### Monotonous Volume:
- **Standard deviation:** <0.03
- **Range:** Very small (min ≈ max)
- Sounds flat and unengaging
- No emphasis or variation
- Audience may tune out

### Excessive Variation:
- **Standard deviation:** >0.20
- **Range:** Very large
- May indicate inconsistent microphone distance
- Could be jarring for audience
- Might have audio quality issues

### Too Quiet Overall:
- **Mean RMS:** <0.05
- Indicates poor voice projection
- Audience struggles to hear
- May seem unconfident

### Too Loud Overall:
- **Mean RMS:** >0.30
- May be distorted or clipping
- Can be uncomfortable for audience
- Check for microphone placement issues

## Configuration

Set in `.env` file:

```bash
# Video storage path (where processed audio is stored)
VIDEO_STORAGE_PATH=D:/VideoData

# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fluent
DB_USERNAME=postgres
DB_PASSWORD=your_password
```

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `.env` file

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver 8006
```

The service will be available at `http://localhost:8006`

## Dependencies

- **librosa**: Audio analysis and RMS feature extraction
- **matplotlib**: Visualization
- **numpy**: Numerical computations
- **Django**: Web framework
- **PostgreSQL**: Database for recording metadata

## Technical Notes

### Data Flow:
1. audio_processing_ms → Creates normalized `_processed.wav` file
2. This service → Loads processed audio → Extracts RMS → Returns statistics
3. Future: Stores volume data in database for feedback generation

### Normalization Impact:
Since the audio is normalized (max amplitude = 1.0):
- RMS values are relative to the loudest point
- Focus is on variation, not absolute loudness
- Comparisons between recordings are more meaningful

### Frame Rate:
- 50ms between frames (hop_length = 800 samples / 16000 Hz)
- 20 frames per second
- 5-minute presentation = ~6,000 frames

### Performance:
- Processing time: ~1-2 seconds per minute of audio
- Typical 5-minute presentation: ~5-10 seconds

## Debug Output

Visualizations are saved to: `debug/{recording_id}/volume.png`

**What to look for:**
- Flat lines → No volume variation (monotonous)
- Peaks and valleys → Good dynamics and emphasis
- Consistent level → Steady voice projection
- Gradual changes → Natural speaking patterns

## Example Usage

```bash
# Analyze volume for recording ID 1
curl -X POST http://localhost:8006/api/v1/volume/1/analyze/
```

## Common Use Cases

### Detecting Volume Issues:
1. **No variation** → Suggest adding emphasis to key points
2. **Too quiet** → Suggest speaking up or adjusting microphone
3. **Erratic volume** → Suggest maintaining consistent mic distance
4. **Gradual decrease** → Speaker may be getting tired

### Combining with Pitch Analysis:
- High pitch + high volume = Excitement/emphasis
- Low pitch + high volume = Authority/confidence
- High pitch + low volume = Uncertainty/nervousness
- Low pitch + low volume = Ending/conclusion

## Future Improvements

- Store volume data in database (currently TODO)
- Detect silence vs. speech automatically
- Identify volume-based emphasis patterns
- Compare against "ideal" presentation patterns
- Real-time volume feedback
- Detect microphone issues
- Segment by volume patterns
