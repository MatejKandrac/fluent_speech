# Transcript Processing Microservice

A microservice for transcribing audio using OpenAI Whisper model. This service extracts text transcripts from processed audio files with word-level timestamps and language detection.

## Overview

This microservice handles the audio transcription logic that was previously part of the filler words analysis service. It uses OpenAI's Whisper model to:
- Transcribe audio to text with high accuracy
- Detect the spoken language automatically
- Provide word-level timestamps for detailed analysis
- Support multiple Whisper model sizes (tiny, base, small, medium, large)
- **Preserve filler words** (uhm, uh, etc.) by using suppress_tokens=[]

## Features

- **Multi-language Support**: Automatically detects the language being spoken
- **Word Timestamps**: Provides precise timing information for each word
- **Database Storage**: Automatically saves word-level transcripts with timestamps and probabilities to PostgreSQL
- **Configurable Models**: Choose from different Whisper model sizes based on accuracy/speed tradeoffs
- **Quality Controls**: Configurable thresholds for speech detection and transcription quality

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

**Response:**
```json
{
  "status": "healthy",
  "service": "transcript_processing"
}
```

### Process Transcript
```
POST /api/v1/transcript/<recording_id>/process/
```

**Parameters:**
- `recording_id` (path parameter): The ID of the recording to transcribe

**Response (Success):**
```json
{
  "success": true,
  "recording_id": 1,
  "duration": 120.5,
  "detected_language": "en",
  "text": "Full transcript text...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.5,
      "text": "First segment text",
      "words": [...]
    }
  ],
  "message": "Transcript processing completed successfully."
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error message describing the issue"
}
```

## Configuration

Configuration is handled through environment variables in `settings.py`:

### Whisper Model Configuration
- `WHISPER_MODEL`: Model size to use (default: `base`)
  - Options: `tiny`, `base`, `small`, `medium`, `large`
  - Larger models are more accurate but slower
- `WHISPER_WORD_TIMESTAMPS`: Enable word-level timestamps (default: `True`)
- `WHISPER_TEMPERATURE`: Sampling temperature (default: `0.0`)
- `WHISPER_NO_SPEECH_THRESHOLD`: Threshold for detecting silence (default: `0.2`)
- `WHISPER_LOGPROB_THRESHOLD`: Log probability threshold (default: `-1.0`)
- `WHISPER_COMPRESSION_RATIO_THRESHOLD`: Compression ratio threshold (default: `3.0`)
- `WHISPER_SUPPRESS_TOKENS`: Token IDs to suppress (default: empty string)
  - Empty string = no suppression (attempts to preserve filler words)
  - Can be set to comma-separated token IDs to suppress specific tokens

### Processing Configuration
- `MIN_AUDIO_DURATION`: Minimum audio length in seconds (default: `1.0`)
- `SAVE_TRANSCRIPT_TO_FILE`: Save transcripts to debug files (default: `True`)

### Database Configuration
- `DB_HOST`: PostgreSQL host (default: `localhost`)
- `DB_PORT`: PostgreSQL port (default: `5432`)
- `DB_NAME`: Database name (default: `fluent`)
- `DB_USERNAME`: Database user
- `DB_PASSWORD`: Database password

**Database Schema**: The service saves transcription data to the `word` table with the following structure:
- `id`: Primary key
- `recording_id`: Foreign key to recording table
- `start_time`: Word start timestamp in seconds
- `end_time`: Word end timestamp in seconds
- `word`: The transcribed word text
- `probability`: Confidence score from Whisper model

### Storage Configuration
- `VIDEO_STORAGE_PATH`: Path where processed audio files are stored (default: `D:/VideoData`)

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file

3. Run the service:
```bash
./run.sh
```

Or manually:
```bash
python manage.py runserver 8009
```

**Note:** Whisper models will be downloaded automatically on first use

### Docker

Build and run using Docker:
```bash
docker build -t transcript-processing-ms .
docker run -p 8009:8009 transcript-processing-ms
```

## Model Performance

Different Whisper models offer tradeoffs between speed and accuracy:

| Model  | Parameters | Speed    | Accuracy | Use Case |
|--------|-----------|----------|----------|----------|
| tiny   | 39M       | Fastest  | Good     | Real-time, low resources |
| base   | 74M       | Fast     | Better   | Recommended for most cases |
| small  | 244M      | Moderate | Great    | Higher accuracy needed |
| medium | 769M      | Slow     | Excellent| Production quality |
| large  | 1550M     | Slowest  | Best     | Maximum accuracy |

## Dependencies

- **Django**: Web framework
- **Django REST Framework**: API endpoints
- **openai-whisper**: Speech recognition model
- **librosa**: Audio processing and duration extraction
- **torch**: PyTorch backend for Whisper
- **psycopg2**: PostgreSQL database adapter
- **ffmpeg**: Audio format conversion (system dependency)

## Integration

This microservice is designed to work with:
- **Audio Processing MS**: Receives processed audio files
- **Filler Words Analysis MS**: Stores transcripts in database for filler word detection
- **API Gateway**: Routes requests from the mobile app

### Workflow
1. Audio Processing MS processes the raw audio file
2. Transcript Processing MS transcribes the audio and stores words in database
3. Filler Words Analysis MS reads words from database and analyzes filler word usage

**Note**: The transcript must be processed before running filler word analysis, as the filler words service reads directly from the database rather than calling this service's API.

## Error Handling

The service handles various error conditions:
- Recording not found in database
- Processed audio file missing
- Audio duration too short
- Transcription failures
- Invalid Whisper model configuration

## Future Enhancements

- [x] Store transcripts in database (completed)
- [ ] Add caching layer to avoid re-transcribing the same audio
- [ ] Support streaming transcription for real-time feedback
- [ ] Add support for custom vocabulary/domain-specific terms
- [ ] Implement aggregate confidence scoring per recording
- [ ] Add speaker diarization for multi-speaker recordings
- [ ] Add endpoint to retrieve stored transcript words from database

## Port

Default port: **8009**

Configurable via `TRANSCRIPT_PORT` environment variable.
