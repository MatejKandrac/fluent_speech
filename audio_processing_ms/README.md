# Audio Processing Service

A microservice that extracts, normalizes, and prepares audio from presentation videos for downstream analysis.

## What This Service Does

This service processes video files to extract clean, normalized audio suitable for analysis by other microservices (pitch, volume, speech recognition, etc.).

## Processing Pipeline

The service processes audio in 5 steps:

### Step 1: Audio Extraction
Extracts raw audio from video files using FFmpeg.

**How it works:**
- Uses FFmpeg to extract audio track from video
- Converts to WAV format (PCM 16-bit mono)
- Sample rate: 22,050 Hz (configurable via `AUDIO_SAMPLE_RATE` env var)
- Single channel (mono) for consistency

**Output:** `{filename}.wav` saved to video storage directory

### Step 2: Load Audio
Loads the extracted WAV file using librosa.

**Why librosa?**
- Industry-standard audio processing library
- Handles various audio formats
- Provides high-quality resampling

### Step 3: Normalization
Normalizes audio amplitude to a consistent range.

**Why normalize?**
- Videos may have different recording volumes
- Ensures consistent loudness across recordings
- Prevents clipping and distortion in analysis
- Makes comparisons between recordings fair

**How it works:**
- Scales audio so the maximum amplitude is 1.0
- Preserves the relative dynamics within the audio
- Formula: `normalized = audio / max(abs(audio))`

### Step 4: Resampling
Resamples audio to a standard 16 kHz sample rate.

**Why 16 kHz?**
- Standard for speech processing and analysis
- Good balance between quality and file size
- Required sample rate for many speech analysis algorithms
- Reduces computational load for downstream processing

**How it works:**
- Uses high-quality librosa resampling
- Applies anti-aliasing filter to prevent artifacts
- Target: 16,000 Hz fixed

### Step 5: Noise Reduction
**TODO:** Apply noise reduction to remove background noise and improve audio quality.

**Planned features:**
- Remove background hum and static
- Reduce room echo
- Preserve speech clarity

### Step 6: Save Processed Audio
Saves the final processed audio for use by other microservices.

**Output:** `{filename}_processed.wav` saved to video storage directory

**Format:**
- WAV (PCM 16-bit)
- 16 kHz sample rate
- Mono channel
- Normalized amplitude

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Process Audio
```
POST /api/v1/audio/{recording_id}/process/
```

**Parameters:**
- `recording_id` (int): Database ID of the recording

**Response:**
```json
{
  "success": true,
  "recording_id": 1,
  "original_wav_path": "D:/VideoData/video.wav",
  "processed_wav_path": "D:/VideoData/video_processed.wav",
  "duration": 180.5,
  "sample_rate": 16000,
  "samples": 2888000
}
```

## Configuration

Set in `.env` file:

```bash
# Audio extraction sample rate (before resampling)
AUDIO_SAMPLE_RATE=22050

# Video storage path
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

3. Install FFmpeg:
   - Download from https://ffmpeg.org/download.html
   - Add to system PATH

4. Configure `.env` file

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the server:
```bash
python manage.py runserver 8004
```

The service will be available at `http://localhost:8004`

## Dependencies

- **FFmpeg**: Audio extraction from video
- **librosa**: Audio loading and resampling
- **soundfile**: Audio file I/O
- **Django**: Web framework
- **PostgreSQL**: Database for recording metadata

## Technical Notes

### Data Flow:
1. Video uploaded → Stored in VIDEO_STORAGE_PATH
2. Recording created in database
3. This service → Extract and process audio → Save processed WAV
4. Other services (pitch, volume) → Use processed WAV for analysis

### File Naming:
- Original video: `{filename}.mp4`
- Extracted audio: `{filename}.wav`
- Processed audio: `{filename}_processed.wav`

### Performance:
- Processing time: ~2-5 seconds per minute of video
- Typical 5-minute presentation: ~10-25 seconds

## Example Usage

```bash
# Process audio for recording ID 1
curl -X POST http://localhost:8004/api/v1/audio/1/process/
```

## Future Improvements

- Implement noise reduction (currently TODO)
- Add support for multiple audio tracks
- Automatic volume normalization per speaker
- Real-time audio processing
- Support for streaming audio
