# FluentApiGateway

Central API Gateway for the Fluent presentation skills assistant. Built with Kotlin and Spring Boot.

## Purpose

The API Gateway is the single entry point for the Flutter mobile application. It is responsible for:
- Accepting video uploads from the mobile app and persisting files to the local file system
- Storing recording metadata in PostgreSQL
- Automatically triggering downstream microservices (Video Processing, Audio Processing) asynchronously after each upload
- Providing a delete endpoint for removing stored videos

It acts as the coordinator between the mobile frontend and the analysis microservice ecosystem.

## Algorithms / Libraries

| Library | Role |
|---|---|
| Spring Boot | HTTP server and application framework |
| Spring MVC | REST controller (`VideoUploadController`) |
| Spring Data JPA / Hibernate | ORM for PostgreSQL persistence |
| Spring Security | HTTP security configuration |
| `RestTemplate` | HTTP client for calling downstream microservices |
| Spring `@Async` | Non-blocking background threads for triggering analysis |
| PostgreSQL (JDBC) | Persistent storage for recording metadata |

### Post-Upload Async Pipeline

After a video is uploaded successfully:
1. File is saved to `VIDEO_STORAGE_PATH`
2. Recording metadata saved to PostgreSQL
3. `VideoAnalysisService` asynchronously calls `POST /api/v1/video/{id}/analyze/` (Video Processing MS)
4. `AudioAnalysisService` asynchronously calls `POST /api/v1/audio/{id}/analyze/` (Audio Processing MS)

Both calls use Spring `@Async` — the upload response returns immediately without waiting for analysis to finish.

## API Endpoints

### Upload Video
```
POST /api/v1/videos/upload
Content-Type: multipart/form-data

Body:
  video: <file>

Response:
{
  "id": 1,
  "filename": "abc123.mp4",
  "fileSize": 12345678,
  "uploadedAt": "2025-03-09T12:00:00"
}
```

### Delete Video
```
DELETE /api/v1/videos/{filename}
```

## Configurable Parameters

Set in `.env` (referenced by `application.properties`):

```env
# Server
API_GATEWAY_PORT=8000

# File storage
VIDEO_STORAGE_PATH=D:/VideoData

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fluent
DB_USERNAME=postgres
DB_PASSWORD=your_password

# Downstream microservice URLs
VIDEO_ANALYSIS_SERVICE_URL=http://localhost:8001
AUDIO_ANALYSIS_SERVICE_URL=http://localhost:8004
```

**File upload limits** (hardcoded in `application.properties`):
- Max file size: `500MB`
- Max request size: `500MB`

## Setup

```bash
cd FluentApiGateway
./gradlew bootRun
```

Service available at `http://localhost:8000`

## Technical Notes

- Framework: Kotlin + Spring Boot 3.x
- Database: PostgreSQL (shared with all microservices)
- Async executor: Configured in `AsyncConfiguration.kt`
- Security: Configured in `SecurityConfig.kt` (CORS and endpoint access rules)
- Error handling: Centralized in `CustomExceptionHandler.kt`
