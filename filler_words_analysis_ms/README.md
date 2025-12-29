# Filler Words Analysis Microservice

This microservice analyzes speech recordings to detect and analyze filler words (e.g., "ehm", "um", "like", "teda").

## Features

- **Speech-to-Text Transcription**: Uses OpenAI Whisper to transcribe audio
- **Filler Word Detection**: Detects filler words in both Slovak and English
- **Statistical Analysis**: Calculates usage rates, most common fillers, and patterns
- **Timeline Visualization**: Generates debug graphs showing filler word usage over time

## Technologies

- **Django REST Framework**: API framework
- **OpenAI Whisper**: Speech-to-text transcription
- **PostgreSQL**: Database connection
- **Matplotlib**: Visualization

## API Endpoints

### Health Check
```
GET /api/health/
```

### Analyze Filler Words
```
POST /api/analyze-filler-words/<recording_id>/
```

Response:
```json
{
  "success": true,
  "recording_id": 1,
  "duration": 120.5,
  "detected_language": "sk",
  "statistics": {
    "total_filler_words": 25,
    "fillers_per_minute": 12.45,
    "most_common_filler": {
      "word": "ehm",
      "count": 10
    },
    "slovak_fillers_count": 20,
    "english_fillers_count": 5,
    "is_high_usage": true
  }
}
```

## Configuration

Environment variables in `settings.py`:

- `WHISPER_MODEL`: Whisper model size (tiny, base, small, medium, large) - default: "base"
- `HIGH_FILLER_THRESHOLD`: Threshold for high usage (fillers per minute) - default: 5
- `MIN_SPEECH_DURATION`: Minimum speech duration for analysis (seconds) - default: 10

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DEBUG=True
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=fluent
export DB_USERNAME=postgres
export DB_PASSWORD=your_password

# Run server
python manage.py runserver 8007
```

## Docker

```bash
docker build -t filler-words-analysis .
docker run -p 8007:8007 filler-words-analysis
```

## Debug Output

When `DEBUG=True`, the service generates visualization graphs in `/debug_output/<recording_id>/`:

- `filler_words_timeline_<recording_id>.png`: Timeline showing filler word usage over time
