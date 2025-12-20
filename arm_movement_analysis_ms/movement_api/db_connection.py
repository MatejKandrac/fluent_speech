import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from django.conf import settings
from typing import Optional, Dict, Any, List
import threading


ARM_LANDMARKS = [
    'left_shoulder', 'right_shoulder',    # Shoulder joints (arm origin)
    'left_elbow', 'right_elbow',          # Elbow joints (arm middle)
    'left_wrist', 'right_wrist',          # Wrist (arm endpoint)
    'left_hip', 'right_hip',              # Hip reference points for body position
]


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


def get_analysis_by_recording_id(recording_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT a.id, a.recording_id, a.total_frames, a.created_at
                FROM analysis a
                WHERE a.recording_id = %s
                ORDER BY a.created_at DESC
                LIMIT 1
                """,
                (recording_id,)
            )
            analysis = cursor.fetchone()

            if not analysis:
                return None

            analysis_id = analysis['id']

            cursor.execute(
                """
                SELECT fd.id as frame_id, fd.timestamp, fd.frame_index,
                       l.type, l.x, l.y, l.z, l.visibility
                FROM frame_data fd
                LEFT JOIN landmark l ON l.frame_data_id = fd.id
                WHERE fd.analysis_id = %s
                  AND l.type IN %s
                ORDER BY fd.frame_index, l.type
                """,
                (analysis_id, tuple(ARM_LANDMARKS))
            )
            rows = cursor.fetchall()

            frames = {}
            for row in rows:
                frame_idx = row['frame_index']

                if frame_idx not in frames:
                    frames[frame_idx] = {
                        'timestamp': row['timestamp'].isoformat(),
                        'landmarks': {}
                    }

                if row['type']:  # If landmark exists
                    frames[frame_idx]['landmarks'][row['type']] = {
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'z': float(row['z']),
                        'visibility': float(row['visibility'])
                    }

            result = {
                'recording_id': recording_id,
                'total_frames': analysis['total_frames'],
                'created_at': analysis['created_at'].isoformat(),
                'data': [frames[i] for i in sorted(frames.keys())]
            }

            return result

    finally:
        return_db_connection(conn)


def get_recording_exists(recording_id: int) -> bool:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM recording WHERE id = %s",
                (recording_id,)
            )
            return cursor.fetchone() is not None
    finally:
        return_db_connection(conn)


def get_landmark_types_for_analysis(analysis_id: int) -> List[str]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT l.type
                FROM landmark l
                JOIN frame_data fd ON fd.id = l.frame_data_id
                WHERE fd.analysis_id = %s
                ORDER BY l.type
                """,
                (analysis_id,)
            )
            return [row[0] for row in cursor.fetchall()]
    finally:
        return_db_connection(conn)
