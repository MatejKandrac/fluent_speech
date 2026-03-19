import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from django.conf import settings
from typing import Optional, List, Dict, Any
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
                "SELECT id, filename, fps, created_at FROM recording WHERE id = %s",
                (recording_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
    finally:
        return_db_connection(conn)


def get_hip_landmarks_by_recording_id(recording_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve hip landmark data for a given recording.

    Returns a list of frames with hip landmarks (left_hip and right_hip).
    Each frame contains timestamp and landmark coordinates.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    fd.timestamp,
                    fd.frame_index,
                    l.type,
                    l.x,
                    l.y,
                    l.z,
                    l.visibility
                FROM frame_data fd
                LEFT JOIN landmark l ON fd.id = l.frame_data_id
                WHERE fd.recording_id = %s
                  AND l.type IN ('left_hip', 'right_hip')
                ORDER BY fd.frame_index, l.type
                """,
                (recording_id,)
            )
            results = cursor.fetchall()

            # Organize data by frame
            frames = {}
            for row in results:
                frame_idx = row['frame_index']
                if frame_idx not in frames:
                    frames[frame_idx] = {
                        'frame_index': frame_idx,
                        'timestamp': str(row['timestamp']),
                        'landmarks': {}
                    }

                if row['type']:
                    frames[frame_idx]['landmarks'][row['type']] = {
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'z': float(row['z']),
                        'visibility': float(row['visibility'])
                    }

            # Convert to sorted list
            return sorted(frames.values(), key=lambda x: x['frame_index'])

    finally:
        return_db_connection(conn)
