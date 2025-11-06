"""
MongoDB connection and operations.
"""
from pymongo import MongoClient
from django.conf import settings
from typing import Optional, Dict, Any


class MongoDBConnection:
    """Singleton class for managing MongoDB connection."""

    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._connect()

    def _connect(self):
        """Establish connection to MongoDB."""
        config = settings.MONGODB_CONFIG

        # Build connection string
        if config['username'] and config['password']:
            connection_string = (
                f"mongodb://{config['username']}:{config['password']}"
                f"@{config['host']}:{config['port']}"
            )
        else:
            connection_string = f"mongodb://{config['host']}:{config['port']}"

        self._client = MongoClient(connection_string)
        self._db = self._client[config['database']]

    @property
    def db(self):
        """Get the database instance."""
        if self._client is None:
            self._connect()
        return self._db

    def get_collection(self, collection_name: str):
        """Get a specific collection."""
        return self.db[collection_name]

    def close(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None


def get_videos_collection():
    """Get the videos collection."""
    return MongoDBConnection().get_collection('videos')


def get_analysis_collection():
    """Get the analysis collection."""
    return MongoDBConnection().get_collection('analysis')
