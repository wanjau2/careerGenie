"""Application settings and configuration."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False

    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    # Access token: 7 days (604800 seconds) - long enough for mobile apps
    # Can be overridden via JWT_ACCESS_TOKEN_EXPIRES env var
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 604800)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)  # Refresh token: 90 days
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # Database settings
    MONGODB_URI = os.getenv('MONGODB_URI')
    DB_NAME = os.getenv('DB_NAME', 'career_genie')

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}

    # CORS settings
    CORS_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # Subscription limits (2-tier system)
    FREE_SWIPE_LIMIT = 50
    PAID_SWIPE_LIMIT = -1  # Unlimited for paid users ($8.99/month)

    # Subscription pricing
    PAID_PLAN_PRICE = 8.99  # USD per month

    # Job matching
    MIN_MATCH_SCORE = 0.3  # Minimum 30% match to show job
    DEFAULT_JOB_RADIUS_MILES = 50

    # Security
    BCRYPT_LOG_ROUNDS = 12
    PASSWORD_MIN_LENGTH = 8

    # Email settings (for future use)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    # External APIs
    JOB_API_KEY = os.getenv('JOB_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # For AI features

    # DigitalOcean Spaces (optional)
    DO_SPACES_KEY = os.getenv('DO_SPACES_KEY')
    DO_SPACES_SECRET = os.getenv('DO_SPACES_SECRET')
    DO_SPACES_REGION = os.getenv('DO_SPACES_REGION', 'nyc3')
    DO_SPACES_BUCKET = os.getenv('DO_SPACES_BUCKET')
    DO_SPACES_CDN_URL = os.getenv('DO_SPACES_CDN_URL')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

    # Override with stricter settings
    BCRYPT_LOG_ROUNDS = 13


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    MONGODB_URI = 'mongodb://localhost:27017/career_genie_test'


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
