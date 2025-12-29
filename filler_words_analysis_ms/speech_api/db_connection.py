import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from django.conf import settings
from typing import Optional, Dict, Any
import threading


class PostgreSQLConnection:
    _instance: Optional['PostgreSQLConnection'] = None
    _lock = threading.Lock()
    _pool: Optional[SimpleConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._create_pool()

    def _create_pool(self):
        config = settings.POSTGRES_CONFIG

        self._pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )

    def get_connection(self):
        if self._pool is None:
            self._create_pool()
        return self._pool.getconn()

    def return_connection(self, conn):
        if self._pool:
            self._pool.putconn(conn)

    def close_all(self):
        if self._pool:
            self._pool.closeall()
            self._pool = None


def get_db_connection():
    return PostgreSQLConnection().get_connection()


def return_db_connection(conn):
    PostgreSQLConnection().return_connection(conn)


def get_audio_file_path(recording_id: int) -> Optional[str]:
    """Get the path to the audio file for a recording"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT audio_file_path
                FROM recording
                WHERE id = %s
                """,
                (recording_id,)
            )
            result = cursor.fetchone()

            if result and result['audio_file_path']:
                return result['audio_file_path']
            return None

    finally:
        return_db_connection(conn)


def get_recording_metadata(recording_id: int) -> Optional[Dict[str, Any]]:
    """Get recording metadata including duration"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT r.id, r.audio_file_path, r.duration, r.created_at, r.name
                FROM recording r
                WHERE r.id = %s
                """,
                (recording_id,)
            )
            result = cursor.fetchone()

            if result:
                return {
                    'recording_id': result['id'],
                    'audio_file_path': result['audio_file_path'],
                    'duration': float(result['duration']) if result['duration'] else None,
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                    'name': result['name']
                }
            return None

    finally:
        return_db_connection(conn)
