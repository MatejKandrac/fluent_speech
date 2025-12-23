import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from django.conf import settings
from typing import Optional
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


def get_recording_by_id(recording_id: int) -> Optional[dict]:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, filename, created_at FROM recording WHERE id = %s",
                (recording_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
    finally:
        return_db_connection(conn)


def insert_audio_features_batch(recording_id: int, audio_features: list):
    """
    Insert audio features (pitch, volume) in batch.

    Args:
        recording_id: The recording ID
        audio_features: List of dicts with keys: timestamp, pitch_hz, volume_db, pitch_confidence
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            feature_values = [
                (recording_id, feature['timestamp'], feature['pitch_hz'],
                 feature['volume_db'], feature.get('pitch_confidence'))
                for feature in audio_features
            ]

            cursor.executemany(
                """
                INSERT INTO audio_features (recording_id, timestamp, pitch_hz, volume_db, pitch_confidence)
                VALUES (%s, %s, %s, %s, %s)
                """,
                feature_values
            )
            conn.commit()
            print(f"Inserted {len(feature_values)} audio feature records")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)


