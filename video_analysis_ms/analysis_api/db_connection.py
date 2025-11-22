"""
PostgreSQL connection and operations using psycopg2.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from django.conf import settings
from typing import Optional
import threading


class PostgreSQLConnection:
    """Singleton class for managing PostgreSQL connection pool."""

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
        """Create connection pool to PostgreSQL."""
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
        """Get a connection from the pool."""
        if self._pool is None:
            self._create_pool()
        return self._pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self._pool:
            self._pool.putconn(conn)

    def close_all(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None


def get_db_connection():
    """Get a database connection from the pool."""
    return PostgreSQLConnection().get_connection()


def return_db_connection(conn):
    """Return a database connection to the pool."""
    PostgreSQLConnection().return_connection(conn)


def get_video_by_id(video_id: int) -> Optional[dict]:
    """
    Get video record by ID.

    Args:
        video_id: The ID of the video recording

    Returns:
        Dictionary with video data or None if not found
    """
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


def insert_analysis(recording_id: int, total_frames: int, max_x: float, max_y: float) -> int:
    """
    Insert analysis record.

    Args:
        recording_id: Foreign key to recording table
        total_frames: Total number of frames analyzed
        max_x: Maximum x coordinate found
        max_y: Maximum y coordinate found

    Returns:
        ID of the inserted analysis record
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO analysis (recording_id, total_frames, max_x, max_y)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (recording_id, total_frames, max_x, max_y)
            )
            analysis_id = cursor.fetchone()[0]
            conn.commit()
            return analysis_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)


def insert_frame_data(analysis_id: int, timestamp: str, frame_index: int) -> int:
    """
    Insert frame data record.

    Args:
        analysis_id: Foreign key to analysis table
        timestamp: Timestamp of the frame (ISO time format)
        frame_index: Index of the frame

    Returns:
        ID of the inserted frame_data record
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO frame_data (analysis_id, timestamp, frame_index)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (analysis_id, timestamp, frame_index)
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
    """
    Insert multiple landmarks for a frame in a single transaction.

    Args:
        frame_data_id: Foreign key to frame_data table
        landmarks: Dictionary mapping landmark names to LandmarkData objects
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Prepare batch insert
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


def get_analysis_by_id(analysis_id: int) -> Optional[dict]:
    """
    Get analysis by ID with all related data.

    Args:
        analysis_id: The ID of the analysis

    Returns:
        Dictionary with complete analysis data or None if not found
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get analysis
            cursor.execute(
                """
                SELECT a.id, a.recording_id, a.total_frames, a.max_x, a.max_y,
                       a.created_at, r.filename
                FROM analysis a
                JOIN recording r ON a.recording_id = r.id
                WHERE a.id = %s
                """,
                (analysis_id,)
            )
            analysis = cursor.fetchone()

            if not analysis:
                return None

            # Get frame data with landmarks
            cursor.execute(
                """
                SELECT fd.id, fd.timestamp, fd.frame_index,
                       l.type, l.x, l.y, l.z, l.visibility
                FROM frame_data fd
                LEFT JOIN landmark l ON l.frame_data_id = fd.id
                WHERE fd.analysis_id = %s
                ORDER BY fd.frame_index, l.type
                """,
                (analysis_id,)
            )
            rows = cursor.fetchall()

            # Organize data
            frames = {}
            for row in rows:
                frame_idx = row['frame_index']
                if frame_idx not in frames:
                    frames[frame_idx] = {
                        'timestamp': str(row['timestamp']),
                        'landmarks': {}
                    }

                if row['type']:  # If landmark exists
                    frames[frame_idx]['landmarks'][row['type']] = {
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'z': float(row['z']),
                        'visibility': float(row['visibility'])
                    }

            # Build result
            result = dict(analysis)
            result['data'] = [frames[i] for i in sorted(frames.keys())]
            result['created_at'] = result['created_at'].isoformat()

            return result
    finally:
        return_db_connection(conn)


def get_analyses_by_recording_id(recording_id: int) -> list:
    """
    Get all analyses for a recording.

    Args:
        recording_id: The ID of the recording

    Returns:
        List of analysis summaries
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, recording_id, total_frames, max_x, max_y, created_at
                FROM analysis
                WHERE recording_id = %s
                ORDER BY created_at DESC
                """,
                (recording_id,)
            )
            analyses = cursor.fetchall()
            return [dict(a) for a in analyses]
    finally:
        return_db_connection(conn)


def delete_analysis_by_id(analysis_id: int) -> bool:
    """
    Delete an analysis by ID (cascade deletes frame_data and landmarks).

    Args:
        analysis_id: The ID of the analysis to delete

    Returns:
        True if deleted, False if not found
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM analysis WHERE id = %s",
                (analysis_id,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)