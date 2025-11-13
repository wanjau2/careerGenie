"""Test script for resume scraping functionality."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from services.resume_scraper import ResumeScraper
from bson import ObjectId


def test_huggingface_scraper():
    """Test Hugging Face dataset scraping."""
    print("\n" + "=" * 70)
    print("TEST: Hugging Face Dataset Scraping")
    print("=" * 70)

    try:
        scraper = ResumeScraper()

        print("\nDownloading resumes from Hugging Face...")
        print("Dataset: opensporks/resumes")
        print("Max resumes: 10 (for testing)")

        # Use a test user ID
        test_user_id = str(ObjectId())

        result = scraper.download_huggingface_dataset(
            user_id=test_user_id,
            dataset_name="opensporks/resumes",
            max_resumes=10  # Small number for testing
        )

        if result['success']:
            print("\n✅ SUCCESS!")
            print(f"   Corpus ID: {result['corpus_id']}")
            print(f"   Files Uploaded: {result['files_uploaded']}")
            print(f"   Files Failed: {result['files_failed']}")
            print(f"   Average Quality Score: {result['corpus']['averageQualityScore']:.2f}")

            if result['uploaded_files']:
                print(f"\n   Sample uploaded files:")
                for file_info in result['uploaded_files'][:5]:
                    print(f"     - {file_info['filename']} (Score: {file_info['qualityScore']:.2f})")

            return True
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_scraping_info():
    """Print information about available scraping options."""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "Resume Scraping System" + " " * 28 + "║")
    print("╚" + "=" * 68 + "╝")

    print("\n📚 Available Public Dataset Sources:")
    print("\n1. Hugging Face - opensporks/resumes")
    print("   • 2400+ resumes in text format")
    print("   • Multiple categories (HR, IT, Finance, etc.)")
    print("   • Free access, no authentication required")

    print("\n2. Kaggle - snehaanbhawal/resume-dataset")
    print("   • PDF and text format resumes")
    print("   • Requires Kaggle API credentials")
    print("   • High-quality samples")

    print("\n3. Direct URL Download")
    print("   • Download from any public URL")
    print("   • Supports ZIP files")
    print("   • Custom corpus naming")

    print("\n" + "=" * 70)
    print("🔧 Setup Requirements:")
    print("=" * 70)

    print("\nFor Hugging Face:")
    print("   pip install datasets")

    print("\nFor Kaggle:")
    print("   1. pip install kaggle")
    print("   2. Create Kaggle API credentials at https://www.kaggle.com/account")
    print("   3. Download kaggle.json and place in ~/.kaggle/")

    print("\n" + "=" * 70)


def main():
    """Run scraper tests."""
    print_scraping_info()

    print("\n\n🚀 Starting Tests...")

    # Test Hugging Face scraper
    hf_result = test_huggingface_scraper()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if hf_result:
        print("✅ Hugging Face scraping: PASSED")
        print("\n🎉 Scraping system is working correctly!")
        print("\nYou can now quickly build a training corpus by scraping public datasets.")
        print("\n💡 API Endpoints:")
        print("   POST /api/training/scrape/huggingface")
        print("   POST /api/training/scrape/kaggle")
        print("   POST /api/training/scrape/url")
    else:
        print("❌ Hugging Face scraping: FAILED")
        print("\n⚠️  Please install required dependencies:")
        print("   pip install datasets")

    print()


if __name__ == "__main__":
    main()
