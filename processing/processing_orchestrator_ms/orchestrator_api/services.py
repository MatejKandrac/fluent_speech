import threading
import uuid
from pathlib import Path
from typing import Dict, Any

import psycopg2
import requests
from django.conf import settings


class ProcessingOrchestratorService:

    def upload_video(self, file) -> Dict[str, Any]:
        content_type = getattr(file, 'content_type', '') or ''
        if not content_type.startswith('video/'):
            return {'success': False, 'error': 'File must be a video'}

        ext = file.name.rsplit('.', 1)[-1] if file.name and '.' in file.name else 'mp4'
        unique_filename = f"{uuid.uuid4()}.{ext}"

        storage_path = Path(settings.VIDEO_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)
        dest = storage_path / unique_filename

        with open(dest, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        recording_id = self._create_recording(unique_filename)

        threading.Thread(target=self._trigger_video_processing, args=(recording_id,), daemon=True).start()
        threading.Thread(target=self._trigger_audio_processing, args=(recording_id,), daemon=True).start()

        return {
            'success': True,
            'recording_id': recording_id,
            'filename': unique_filename,
        }

    def get_processing_status(self, recording_id: int) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT video_processing_finished, audio_processing_finished, transcript_processing_finished "
                    "FROM recording WHERE id = %s",
                    (recording_id,)
                )
                row = cur.fetchone()
                if not row:
                    return {'success': False, 'error': f'Recording {recording_id} not found'}
                return {
                    'success': True,
                    'recording_id': recording_id,
                    'video_processing_finished': row[0],
                    'audio_processing_finished': row[1],
                    'transcript_processing_finished': row[2],
                }
        finally:
            conn.close()

    def _create_recording(self, filename: str) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO recording (filename) VALUES (%s) RETURNING id",
                    (filename,)
                )
                recording_id = cur.fetchone()[0]
                conn.commit()
                return recording_id
        finally:
            conn.close()

    def _trigger_video_processing(self, recording_id: int):
        url = f"{settings.PROCESSING_SERVICES['video_processing']}/api/v1/video/{recording_id}/analyze/"
        try:
            resp = requests.post(url, timeout=600)
            if resp.ok:
                print(f"[INFO] Video processing completed for recording {recording_id}")
            else:
                print(f"[ERROR] Video processing failed for recording {recording_id}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[ERROR] Error triggering video processing for recording {recording_id}: {e}")

    def _trigger_audio_processing(self, recording_id: int):
        url = f"{settings.PROCESSING_SERVICES['audio_processing']}/api/v1/audio/{recording_id}/analyze/"
        try:
            resp = requests.post(url, timeout=300)
            if resp.ok:
                print(f"[INFO] Audio processing completed for recording {recording_id}")
            else:
                print(f"[ERROR] Audio processing failed for recording {recording_id}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[ERROR] Error triggering audio processing for recording {recording_id}: {e}")

    def _get_connection(self):
        cfg = settings.POSTGRES_CONFIG
        return psycopg2.connect(
            host=cfg['host'],
            port=cfg['port'],
            dbname=cfg['database'],
            user=cfg['user'],
            password=cfg['password'],
        )
