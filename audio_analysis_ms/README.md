# Audio Analysis Microservice (audio_analysis_ms)

Microservice for analyzing audio files extracted from videos. This service processes WAV files and creates amplitude visualizations.

## Features

- Raw audio data loading without normalization or resampling
- Simple amplitude visualization
- Automatic WAV file path resolution from recording ID
- RESTful API endpoints
- Debug output with amplitude plots

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the service:
```bash
python manage.py runserver 0.0.0.0:8002
```

## API Endpoints

### POST /api/analyze/
Analyze audio from a recording and create amplitude visualization.

**Request Body:**
```json
{
    "recording_id": 123
}
```

**Response:**
```json
{
    "success": true,
    "analysis_id": 456,
    "duration": 10.5,
    "sample_rate": 22050,
    "samples": 231525
}
```

### GET /api/health/
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "audio-analysis-ms"
}
```

## Configuration

The service can be configured via environment variables:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`: PostgreSQL connection settings
- `VIDEO_STORAGE_PATH`: Path where video files and extracted audio are stored

## Integration

This service is designed to be called asynchronously by the video analysis service. After a video is processed and a WAV file is extracted, the video analysis service triggers audio analysis by making a POST request to `/api/analyze/` with only the `recording_id`.

The WAV file path is automatically derived from the video filename stored in the recording table (same filename with .wav extension).

## Debug Output

The service creates a debug output directory for each recording:
- Location: `debug_output/{recording_id}/`
- Files: `audio_amplitude.png` - Simple amplitude waveform plot
