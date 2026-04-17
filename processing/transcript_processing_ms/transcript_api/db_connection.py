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


def mark_transcript_processing_finished(recording_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE recording SET transcript_processing_finished = TRUE WHERE id = %s",
                (recording_id,)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_db_connection(conn)


def get_recording_by_id(recording_id: int) -> Optional[dict]:
    """Get recording by ID"""
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


def save_transcript_words(recording_id: int, segments: list) -> bool:
    """
    Save transcribed words with timestamps to the database.

    Args:
        recording_id: The ID of the recording
        segments: List of transcript segments containing word-level data

    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # First, delete any existing words for this recording
            cursor.execute(
                "DELETE FROM word WHERE recording_id = %s",
                (recording_id,)
            )

            # Extract words from all segments
            word_count = 0
            for segment in segments:
                if 'words' in segment and segment['words']:
                    for word_data in segment['words']:
                        # Insert each word with its timing and probability
                        cursor.execute(
                            """
                            INSERT INTO word (recording_id, start_time, end_time, word, probability)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                recording_id,
                                word_data.get('start', 0.0),
                                word_data.get('end', 0.0),
                                word_data.get('word', '').strip(),
                                word_data.get('probability', 0.0)
                            )
                        )
                        word_count += 1

            conn.commit()
            print(f"Saved {word_count} words to database for recording {recording_id}")
            return True

    except Exception as e:
        conn.rollback()
        print(f"Error saving transcript words to database: {e}")
        return False
    finally:
        return_db_connection(conn)


def get_transcript_words(recording_id: int) -> list:
    """
    Get all transcribed words for a recording from the database.

    Args:
        recording_id: The ID of the recording

    Returns:
        List of word dictionaries with start_time, end_time, word, and probability
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, start_time, end_time, word, probability
                FROM word
                WHERE recording_id = %s
                ORDER BY start_time
                """,
                (recording_id,)
            )
            results = cursor.fetchall()
            return [dict(row) for row in results] if results else []
    finally:
        return_db_connection(conn)
