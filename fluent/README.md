# Fluent - Mobile App

Flutter mobile application for recording and analyzing presentation skills.

## Purpose

The Fluent app is the user-facing interface for the presentation skills assistant. It allows users to:
- Record video presentations using the device camera
- See real-time pose and face landmark overlays during recording (on-device ML)
- Upload recorded videos to the API Gateway for backend analysis
- Browse past recordings stored locally
- (Planned) View analysis feedback and visualizations returned from the backend

The app is designed to be used in a practice/training context where a user records themselves giving a presentation and receives automated feedback.

## Algorithms / Libraries

| Library | Role |
|---|---|
| `google_mlkit_pose_detection` | On-device real-time pose landmark detection (33 body keypoints) |
| `google_mlkit_face_detection` | On-device real-time face landmark detection |
| `camera` | Camera preview and video recording |
| `flutter_native_video_trimmer` | Video trimming before upload |
| `dio` / `retrofit` | HTTP client for uploading videos to the API Gateway |
| `flutter_riverpod` | State management |
| `get_it` | Dependency injection |
| `sqflite` | Local SQLite database for storing recording metadata |
| `video_player` | Playback of recorded videos |

### On-Device vs. Server-Side Processing

- **On-device (real-time):** Pose and face landmark detection via Google ML Kit runs during recording for live visual feedback only
- **Server-side (post-recording):** The uploaded video is re-processed by `video_processing_ms` using MediaPipe for accurate landmark extraction used in analysis

## Configurable Parameters

The app has no `settings.py`, but the backend URL is configurable at build/run time:

```bash
flutter run --dart-define=SERVER_URL=http://<your-machine-ip>:8000
```

Replace `<your-machine-ip>` with the local IP address of the machine running the API Gateway.

## Setup

```bash
cd fluent
flutter pub get
flutter run --dart-define=SERVER_URL=http://10.0.0.1:8000
```

## Local Storage

Recording metadata is stored in local SQLite:

```sql
CREATE TABLE video_records (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  mongo_id   TEXT NOT NULL,
  name       TEXT NOT NULL,
  filename   TEXT NOT NULL,
  created_at TEXT NOT NULL
)
```

## Dependencies

See `pubspec.yaml` for the full dependency list. Key dependencies:
- Flutter SDK
- `google_mlkit_pose_detection: ^0.14.0`
- `google_mlkit_face_detection: ^0.13.1`
- `camera: ^0.11.2`
- `flutter_riverpod: ^3.0.0`
- `dio: ^5.8.0`
- `sqflite: ^2.4.1`

## Technical Notes

- Minimum Android API level required for ML Kit: 21+
- Camera permissions must be granted at runtime
- The `SERVER_URL` must point to a machine on the same local network as the device
