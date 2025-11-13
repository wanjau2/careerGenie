#!/usr/bin/env python3
"""Setup script for initializing the training system."""
import os
import sys
from pathlib import Path


def create_directories():
    """Create required directory structure for training system."""
    print("Creating training directory structure...")

    base_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')
    directories = [
        base_dir,
        os.path.join(base_dir, 'resumes'),
        os.path.join(base_dir, 'models'),
        os.path.join(base_dir, 'checkpoints')
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}")

    print()


def check_dependencies():
    """Check if required packages are installed."""
    print("Checking dependencies...")

    required_packages = {
        'flask': 'Flask web framework',
        'pymongo': 'MongoDB driver',
        'sklearn': 'Scikit-learn for ML',
        'numpy': 'NumPy for numerical computing',
        'pandas': 'Pandas for data manipulation',
        'joblib': 'Joblib for model persistence',
        'celery': 'Celery for background tasks',
        'redis': 'Redis client'
    }

    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package}: {description}")
        except ImportError:
            print(f"  ✗ {package}: {description} - MISSING")
            missing.append(package)

    print()

    if missing:
        print("⚠️  Missing dependencies detected!")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment variables...")

    required_vars = {
        'MONGODB_URI': 'MongoDB connection string',
        'JWT_SECRET_KEY': 'JWT secret key',
        'CELERY_BROKER_URL': 'Celery broker URL (optional, defaults to redis://localhost:6379/0)',
        'CELERY_RESULT_BACKEND': 'Celery result backend (optional, defaults to redis://localhost:6379/0)'
    }

    from dotenv import load_dotenv
    load_dotenv()

    missing = []
    optional_missing = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Don't print sensitive values
            masked_value = value[:10] + '...' if len(value) > 10 else '***'
            print(f"  ✓ {var}: {masked_value}")
        else:
            if var in ['CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND']:
                print(f"  ⚠️  {var}: Not set (will use default)")
                optional_missing.append(var)
            else:
                print(f"  ✗ {var}: {description} - MISSING")
                missing.append(var)

    print()

    if missing:
        print("⚠️  Required environment variables missing!")
        print("Create a .env file with these variables.")
        return False

    if optional_missing:
        print("ℹ️  Optional variables not set - using defaults")
        print("For production, set these in .env:")
        for var in optional_missing:
            print(f"  - {var}")
        print()

    return True


def test_database_connection():
    """Test MongoDB connection."""
    print("Testing database connection...")

    try:
        from config.database import get_database

        db = get_database()
        db.command('ping')
        print("  ✓ MongoDB connection successful")
        print()
        return True

    except Exception as e:
        print(f"  ✗ MongoDB connection failed: {str(e)}")
        print()
        return False


def test_redis_connection():
    """Test Redis connection."""
    print("Testing Redis connection...")

    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv()

        broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

        # Parse Redis URL
        if broker_url.startswith('redis://'):
            # Simple parsing for redis://host:port/db
            parts = broker_url.replace('redis://', '').split('/')
            host_port = parts[0].split(':')
            host = host_port[0] if host_port else 'localhost'
            port = int(host_port[1]) if len(host_port) > 1 else 6379
            db = int(parts[1]) if len(parts) > 1 else 0

            r = redis.Redis(host=host, port=port, db=db)
            r.ping()
            print(f"  ✓ Redis connection successful ({host}:{port}/{db})")
            print()
            return True
        else:
            print("  ⚠️  Non-standard Redis URL, skipping test")
            print()
            return True

    except redis.ConnectionError:
        print("  ✗ Redis connection failed")
        print("  Start Redis with: redis-server")
        print("  Or using Docker: docker run -d -p 6379:6379 redis:latest")
        print()
        return False
    except Exception as e:
        print(f"  ⚠️  Could not test Redis: {str(e)}")
        print()
        return True  # Don't fail setup for this


def initialize_database_indexes():
    """Initialize database indexes for training collections."""
    print("Initializing database indexes...")

    try:
        from config.database import init_database

        init_database()
        print("  ✓ Database indexes created successfully")
        print()
        return True

    except Exception as e:
        print(f"  ✗ Failed to create indexes: {str(e)}")
        print()
        return False


def print_next_steps():
    """Print next steps for user."""
    print("=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("1. Start Redis (if not already running):")
    print("   redis-server")
    print("   OR: docker run -d -p 6379:6379 redis:latest")
    print()
    print("2. Start Celery worker:")
    print("   celery -A celery_app worker --loglevel=info")
    print()
    print("3. Start Celery beat scheduler (optional, for auto-training):")
    print("   celery -A celery_app beat --loglevel=info")
    print()
    print("4. Start Flask application:")
    print("   python app.py")
    print()
    print("5. Test the training API:")
    print("   curl http://localhost:8000/api/training/analytics \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN'")
    print()
    print("Documentation: See TRAINING_SYSTEM.md for detailed usage")
    print()


def main():
    """Main setup function."""
    print()
    print("=" * 70)
    print("Career Genie Training System Setup")
    print("=" * 70)
    print()

    # Run setup steps
    steps = [
        ("Create Directories", create_directories),
        ("Check Dependencies", check_dependencies),
        ("Check Environment", check_environment),
        ("Test Database", test_database_connection),
        ("Test Redis", test_redis_connection),
        ("Initialize Indexes", initialize_database_indexes)
    ]

    failed_steps = []

    for step_name, step_func in steps:
        try:
            success = step_func()
            if not success:
                failed_steps.append(step_name)
        except Exception as e:
            print(f"  ✗ Error in {step_name}: {str(e)}")
            print()
            failed_steps.append(step_name)

    if failed_steps:
        print("=" * 70)
        print("Setup completed with warnings:")
        print("=" * 70)
        print()
        print("Failed steps:")
        for step in failed_steps:
            print(f"  - {step}")
        print()
        print("Please resolve these issues before using the training system.")
        print()
        return 1

    print_next_steps()
    return 0


if __name__ == '__main__':
    sys.exit(main())
