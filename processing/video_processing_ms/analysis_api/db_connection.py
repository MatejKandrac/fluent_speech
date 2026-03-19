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


def get_video_by_id(video_id: int) -> Optional[dict]:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, filename, created_at FROM recording WHERE id = %s",
                (video_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
    finally:
        return_db_connection(conn)


def update_recording_fps(recording_id: int, fps: float):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE recording SET fps = %s WHERE id = %s",
                (fps, recording_id)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)


def insert_frame_data(recording_id: int, timestamp: str, frame_index: int) -> int:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO frame_data (recording_id, timestamp, frame_index)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (recording_id, timestamp, frame_index)
            )
            frame_data_id = cursor.fetchone()[0]
            conn.commit()
            return frame_data_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)


def insert_landmarks_batch(frame_data_id: int, landmarks: dict):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            landmark_values = [
                (frame_data_id, name, lm.x, lm.y, lm.z, lm.visibility)
                for name, lm in landmarks.items()
            ]

            cursor.executemany(
                """
                INSERT INTO landmark (frame_data_id, type, x, y, z, visibility)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                landmark_values
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)


