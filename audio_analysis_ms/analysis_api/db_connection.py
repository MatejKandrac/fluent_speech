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


def get_recording_by_id(recording_id: int) -> Optional[dict]:
    """
    Get recording by ID.

    Args:
        recording_id: The ID of the recording

    Returns:
        Dictionary with recording data or None if not found
    """
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


def get_analysis_by_recording_id(recording_id: int) -> Optional[dict]:
    """
    Get analysis record by recording ID.

    Args:
        recording_id: The ID of the recording

    Returns:
        Dictionary with analysis data or None if not found
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, recording_id, total_frames FROM analysis WHERE recording_id = %s ORDER BY created_at DESC LIMIT 1",
                (recording_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
    finally:
        return_db_connection(conn)


