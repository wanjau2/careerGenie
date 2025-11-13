"""Database configuration and connection management."""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from datetime import datetime


class Database:
    """MongoDB database connection manager."""

    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        """Singleton pattern to ensure only one database connection."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def connect(self):
        """Establish connection to MongoDB."""
        if self._client is None:
            try:
                connection_string = os.getenv('MONGODB_URI')
                if not connection_string:
                    raise ValueError("MONGODB_URI environment variable not set")

                self._client = MongoClient(
                    connection_string,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )

                # Test the connection
                self._client.admin.command('ping')

                # Get database name from URI or use default
                db_name = os.getenv('DB_NAME', 'career_genie')
                self._db = self._client[db_name]

                print(f"✓ Connected to MongoDB database: {db_name}")

            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                print(f"✗ Failed to connect to MongoDB: {e}")
                raise
            except Exception as e:
                print(f"✗ Unexpected error connecting to MongoDB: {e}")
                raise

        return self._db

    def get_db(self):
        """Get database instance."""
        if self._db is None:
            return self.connect()
        return self._db

    def close(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("✓ MongoDB connection closed")


# Global database instance
db_manager = Database()


def get_database():
    """Helper function to get database instance."""
    return db_manager.get_db()


def get_collection(collection_name):
    """Helper function to get a specific collection."""
    db = get_database()
    return db[collection_name]


# Collection helpers
def get_users_collection():
    """Get users collection."""
    return get_collection('users')


def get_jobs_collection():
    """Get jobs collection."""
    return get_collection('jobs')


def get_swipes_collection():
    """Get swipes collection."""
    return get_collection('swipes')


def get_applications_collection():
    """Get applications collection."""
    return get_collection('applications')


def get_courses_collection():
    """Get courses collection."""
    return get_collection('courses')


def get_training_corpora_collection():
    """Get training corpora collection."""
    return get_collection('training_corpora')


def get_training_resumes_collection():
    """Get training resumes collection."""
    return get_collection('training_resumes')


def get_training_jobs_collection():
    """Get training jobs collection."""
    return get_collection('training_jobs')


def get_training_collection():
    """Get general training collection."""
    return get_collection('training')


def init_database():
    """Initialize database with indexes and constraints."""
    db = get_database()

    try:
        # Users collection indexes
        users = get_users_collection()
        users.create_index('email', unique=True)
        users.create_index('createdAt')

        # Jobs collection indexes
        jobs = get_jobs_collection()
        jobs.create_index('isActive')
        jobs.create_index('postedAt')
        jobs.create_index([('location.city', 1), ('location.state', 1)])
        jobs.create_index([('salary.min', 1), ('salary.max', 1)])
        jobs.create_index('company.name')

        # Swipes collection indexes
        swipes = get_swipes_collection()
        swipes.create_index([('userId', 1), ('jobId', 1)], unique=True)
        swipes.create_index('userId')
        swipes.create_index('timestamp')

        # Applications collection indexes
        applications = get_applications_collection()
        applications.create_index([('userId', 1), ('jobId', 1)])
        applications.create_index('userId')
        applications.create_index('status')
        applications.create_index('appliedAt')

        # Training corpora collection indexes
        training_corpora = get_training_corpora_collection()
        training_corpora.create_index('category')
        training_corpora.create_index('uploadedBy')
        training_corpora.create_index('createdAt')

        # Training resumes collection indexes
        training_resumes = get_training_resumes_collection()
        training_resumes.create_index('corpusId')
        training_resumes.create_index('qualityScore')
        training_resumes.create_index('uploadedAt')
        training_resumes.create_index([('filename', 'text'), ('parsedData.raw_text', 'text')])

        # Training jobs collection indexes
        training_jobs = get_training_jobs_collection()
        training_jobs.create_index('status')
        training_jobs.create_index('startedBy')
        training_jobs.create_index('startedAt')
        training_jobs.create_index('completedAt')

        print("✓ Database indexes created successfully")

    except Exception as e:
        print(f"✗ Error creating indexes: {e}")
        raise
