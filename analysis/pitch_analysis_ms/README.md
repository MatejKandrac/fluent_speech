# Pitch Analysis Service

A microservice that analyzes pitch (fundamental frequency) in presentation audio to provide feedback on vocal variety and monotony.

## What This Service Does

This service analyzes the pitch of a speaker's voice to identify:
- Monotone delivery (lack of pitch variation)
- Pitch range (how much the speaker varies their tone)
- Average pitch and speaking patterns
- Pitch trends over time

## How Pitch Analysis Works

### What is Pitch?
Pitch is the perceived fundamental frequency of the voice, measured in Hertz (Hz).

**Typical ranges:**
- Male voice: 85-180 Hz
- Female voice: 165-255 Hz
- Variation is more important than absolute pitch for engagement

### The YIN Algorithm
This service uses the YIN algorithm via librosa for pitch detection.

**Why YIN?**
- Robust to noise and harmonics
- Accurate for human speech
- Industry-standard algorithm
- Handles varying voice qualities

**How it works:**
1. Analyzes audio in small frames (1600 samples)
2. Uses autocorrelation to find periodic patterns
3. Identifies the most likely fundamental frequency
4. Returns 0 Hz for unvoiced segments (silence, consonants)

**Parameters:**
- Frame length: 1600 samples (~100ms at 16kHz)
- Hop length: 800 samples (~50ms between frames)
- Frequency range: 50-300 Hz (captures human speech)

## Processing Pipeline

### Step 1: Load Processed Audio
Loads the preprocessed audio file created by audio_processing_ms.

**Input:** `{filename}_processed.wav`
- 16 kHz sample rate
- Mono channel
- Normalized amplitude

### Step 2: Extract Pitch
Applies YIN algorithm to extract pitch values.

**Output:** Array of pitch values (Hz) for each frame

**Interpretation:**
- 0 Hz: Unvoiced (silence, consonants, noise)
- 50-300 Hz: Voiced speech with detected pitch

### Step 3: Generate Visualization
Creates a plot showing pitch over time.

**Plot features:**
- Time (seconds) on X-axis
- Frequency (Hz) on Y-axis
- Mean pitch displayed in title
- Y-axis limited to 0-400 Hz for clarity

**Output:** `debug/{recording_id}/pitch.png`

### Step 4: Calculate Statistics
Computes summary statistics for the entire recording.

**Metrics:**
- Mean pitch: Average pitch across all voiced frames
- Min/Max pitch: Pitch range
- Standard deviation: Measure of pitch variation

### Step 5: Save to Database
**TODO:** Store pitch data for long-term analysis and feedback generation.

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Pitch
```
POST /api/v1/pitch/{recording_id}/analyze/
```

**Parameters:**
- `recording_id` (int): Database ID of the recording

**Response:**
```json
{
  "success": true,
  "recording_id": 1,
  "pitch_frames": 3600,
  "pitch_mean": 142.5,
  "pitch_min": 85.2,
  "pitch_max": 220.8,
  "pitch_std": 28.3
}
```

## Interpreting Results

### Good Pitch Variation:
- **Standard deviation:** 20-40 Hz
- **Range:** 80+ Hz difference between min and max
- Shows vocal variety and engagement
- Keeps audience interested

### Monotone Speech:
- **Standard deviation:** <15 Hz
- **Range:** <50 Hz
- Sounds robotic and unengaging
- Audience may lose interest

### Excessive Variation:
- **Standard deviation:** >50 Hz
- **Range:** >150 Hz
- May sound overly dramatic or nervous
- Can be distracting

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
python manage.py runserver 8005
```

The service will be available at `http://localhost:8005`

## Dependencies

- **librosa**: Audio analysis and YIN pitch detection
- **matplotlib**: Visualization
- **numpy**: Numerical computations
- **Django**: Web framework
- **PostgreSQL**: Database for recording metadata

## Technical Notes

### Data Flow:
1. audio_processing_ms → Creates `_processed.wav` file
2. This service → Loads processed audio → Extracts pitch → Returns statistics
3. Future: Stores pitch data in database for feedback generation

### Frame Rate:
- 50ms between frames (hop_length = 800 samples / 16000 Hz)
- 20 frames per second
- 5-minute presentation = ~6,000 frames

### Performance:
- Processing time: ~1-3 seconds per minute of audio
- Typical 5-minute presentation: ~5-15 seconds

## Debug Output

Visualizations are saved to: `debug/{recording_id}/pitch.png`

**What to look for:**
- Flat lines → Monotone delivery
- Varied patterns → Good vocal variety
- Many zeros → Lots of silence or noise

## Example Usage

```bash
# Analyze pitch for recording ID 1
curl -X POST http://localhost:8005/api/v1/pitch/1/analyze/
```

## Future Improvements

- Store pitch data in database (currently TODO)
- Detect pitch patterns (rising, falling, emphasis)
- Compare against "ideal" presentation patterns
- Real-time pitch feedback
- Identify pitch-based emotions (excitement, nervousness)
- Segment by pitch patterns
