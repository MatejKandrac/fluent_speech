# Filler Words Analysis Microservice

This microservice analyzes speech recordings to detect and analyze filler words (e.g., "ehm", "um", "like", "teda") by reading transcripts from the database.

## Features

- **Word-Level Filler Detection**: Analyzes transcripts from database with precise word-level timestamps
- **Multi-Language Support**: Detects filler words in both Slovak and English
- **Statistical Analysis**: Calculates usage rates, most common fillers, and temporal patterns
- **Timeline Visualization**: Generates debug graphs showing filler word distribution over time
- **Probability-Based Detection**: Uses Whisper confidence scores for better accuracy

## Technologies

- **Django REST Framework**: API framework
- **PostgreSQL**: Database connection for reading transcript words
- **Matplotlib**: Visualization
- **NumPy**: Statistical calculations

## Architecture

This service reads transcribed words from the `word` table in the database (populated by the Transcript Processing MS) rather than performing its own transcription. This architecture:
- Avoids redundant transcription processing
- Enables faster analysis by reading pre-computed data
- Provides precise word-level timing information
- Preserves filler words that Whisper normally suppresses

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

### Database Configuration
- `DB_HOST`: PostgreSQL host (default: `localhost`)
- `DB_PORT`: PostgreSQL port (default: `5432`)
- `DB_NAME`: Database name (default: `fluent`)
- `DB_USERNAME`: Database user
- `DB_PASSWORD`: Database password

### Analysis Configuration
- `HIGH_FILLER_THRESHOLD`: Threshold for high usage (fillers per minute) - default: 5
- `MIN_SPEECH_DURATION`: Minimum speech duration for analysis (seconds) - default: 10

### Filler Word Lists
The service detects these filler words by default:
- **Slovak**: ehm, ehh, emm, hm, hmm, teda, jako, takže, vlastne, viete
- **English**: uh, um, hmm, like, you know, so, actually, basically, literally

## Prerequisites

**Important**: Before analyzing filler words, you must:
1. Process the audio file with Audio Processing MS
2. Transcribe the audio with Transcript Processing MS (port 8009)
   - This populates the `word` table with transcribed words
3. Then run filler word analysis

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
export VIDEO_STORAGE_PATH=/path/to/videos

# Run server
./run.sh
# Or manually:
python manage.py runserver 8008
```

## Docker

```bash
docker build -t filler-words-analysis .
docker run -p 8008:8008 filler-words-analysis
```

## Debug Output

When `DEBUG=True`, the service generates visualization graphs in `/debug_output/<recording_id>/`:

- `filler_words_timeline_<recording_id>.png`: Timeline showing filler word usage over time

## How It Works

1. **Read Transcript**: Fetches transcribed words from the `word` table for the given recording
2. **Reconstruct Segments**: Groups words into ~5 second segments for analysis
3. **Detect Fillers**: Uses regex with word boundaries to match filler words at word level
4. **Calculate Statistics**:
   - Total filler word count
   - Fillers per minute rate
   - Most common filler word
   - Language distribution (Slovak vs English)
   - High usage indicator
5. **Generate Visualization**: Creates timeline showing filler distribution (in DEBUG mode)

## Example Workflow

```bash
# 1. Upload and process video
POST /api/v1/videos/upload
POST /api/v1/audio/{recording_id}/process/

# 2. Transcribe audio (populates word table)
POST http://localhost:8009/api/v1/{recording_id}/transcribe/

# 3. Analyze filler words (reads from word table)
POST http://localhost:8008/api/v1/filler-words/{recording_id}/analyze/
```

## Port

Default port: **8008**

Configurable via `FILLER_WORDS_PORT` environment variable.
