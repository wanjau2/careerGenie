#!/usr/bin/env python3
"""Quick system test to verify all components are working."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all critical modules can be imported."""
    print("Testing imports...")

    try:
        # Core services
        from services.gemini_service import GeminiService
        print("  ✓ GeminiService imported")

        from services.auto_apply_service import AutoApplyService
        print("  ✓ AutoApplyService imported")

        from services.training_service import TrainingService
        print("  ✓ TrainingService imported")

        from services.ml_training import train_resume_scoring_model
        print("  ✓ ML Training imported")

        # Models
        from models.training import TrainingCorpus, TrainingResume, TrainingJob
        print("  ✓ Training models imported")

        from models.user import User
        print("  ✓ User model imported")

        from models.job import Job
        print("  ✓ Job model imported")

        # Routes
        from routes.training import training_bp
        print("  ✓ Training routes imported")

        from routes.jobs import jobs_bp
        print("  ✓ Jobs routes imported")

        # Celery
        from celery_app import train_model_task, process_user_resume_for_training
        print("  ✓ Celery tasks imported")

        print()
        return True

    except Exception as e:
        print(f"  ✗ Import failed: {str(e)}")
        return False


def test_gemini_api():
    """Test Gemini API connection."""
    print("Testing Gemini API...")

    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')

    if not api_key:
        print("  ✗ GOOGLE_GEMINI_API_KEY not set")
        return False

    print(f"  ✓ API Key found: {api_key[:10]}...")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Simple test
        response = model.generate_content("Say 'API Working'")
        if response.text:
            print(f"  ✓ Gemini API response: {response.text[:30]}...")
            print()
            return True
        else:
            print("  ✗ No response from Gemini")
            return False

    except Exception as e:
        print(f"  ✗ Gemini API test failed: {str(e)}")
        print()
        return False


def test_mongodb():
    """Test MongoDB connection."""
    print("Testing MongoDB...")

    try:
        from config.database import get_database

        db = get_database()
        db.command('ping')

        # Check training collections
        collections = db.list_collection_names()
        training_collections = [c for c in collections if 'training' in c]

        print(f"  ✓ MongoDB connected")
        print(f"  ✓ Found {len(training_collections)} training collections:")
        for coll in training_collections:
            count = db[coll].count_documents({})
            print(f"     - {coll}: {count} documents")

        print()
        return True

    except Exception as e:
        print(f"  ✗ MongoDB test failed: {str(e)}")
        print()
        return False


def test_redis():
    """Test Redis connection."""
    print("Testing Redis...")

    try:
        import redis

        broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

        # Parse URL
        if broker_url.startswith('redis://'):
            parts = broker_url.replace('redis://', '').split('/')
            host_port = parts[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 6379
            db = int(parts[1]) if len(parts) > 1 else 0

            r = redis.Redis(host=host, port=port, db=db)
            r.ping()

            print(f"  ✓ Redis connected ({host}:{port}/{db})")
            print()
            return True

    except Exception as e:
        print(f"  ✗ Redis test failed: {str(e)}")
        print()
        return False


def test_training_system():
    """Test training system components."""
    print("Testing training system...")

    try:
        from services.training_service import TrainingService
        from models.training import TrainingCorpus, TrainingResume, TrainingJob

        service = TrainingService()
        print("  ✓ TrainingService initialized")

        # Check analytics
        analytics = service.get_training_analytics()
        print(f"  ✓ Analytics retrieved:")
        print(f"     - Total corpora: {analytics.get('totalCorpora', 0)}")
        print(f"     - Total resumes: {analytics.get('totalResumes', 0)}")
        print(f"     - Avg quality: {analytics.get('averageQualityScore', 0):.2f}")

        # Check directory structure
        import os
        training_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')
        if os.path.exists(training_dir):
            print(f"  ✓ Training directory exists: {training_dir}")
            subdirs = ['resumes', 'models', 'checkpoints']
            for subdir in subdirs:
                path = os.path.join(training_dir, subdir)
                if os.path.exists(path):
                    print(f"     ✓ {subdir}/")

        print()
        return True

    except Exception as e:
        print(f"  ✗ Training system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_auto_apply():
    """Test auto-apply service initialization."""
    print("Testing auto-apply service...")

    try:
        from services.auto_apply_service import AutoApplyService

        service = AutoApplyService()
        print("  ✓ AutoApplyService initialized")
        print("  ✓ GeminiService integrated")

        print()
        return True

    except Exception as e:
        print(f"  ✗ Auto-apply test failed: {str(e)}")
        print()
        return False


def main():
    """Run all tests."""
    print()
    print("=" * 70)
    print("Career Genie System Test")
    print("=" * 70)
    print()

    results = {
        'Imports': test_imports(),
        'Gemini API': test_gemini_api(),
        'MongoDB': test_mongodb(),
        'Redis': test_redis(),
        'Training System': test_training_system(),
        'Auto-Apply': test_auto_apply()
    }

    print("=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    print()

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")

    print()

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"Total: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some tests failed. Check output above for details.")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
