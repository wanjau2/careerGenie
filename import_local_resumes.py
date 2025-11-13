"""Script to import resumes from local ZIP files."""
import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from services.resume_parser import ResumeParser
from models.training import TrainingCorpus, TrainingResume


def import_from_zip(zip_path, user_id, corpus_name=None):
    """
    Import resumes from a local ZIP file.

    Args:
        zip_path: Path to the ZIP file
        user_id: User ID for ownership
        corpus_name: Optional name for the corpus

    Returns:
        Dictionary with import results
    """
    print(f"\n{'='*70}")
    print(f"Importing resumes from: {zip_path}")
    print(f"{'='*70}\n")

    if not os.path.exists(zip_path):
        print(f"❌ Error: File not found: {zip_path}")
        return None

    # Initialize parser
    resume_parser = ResumeParser()
    training_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')

    # Create corpus directory
    corpus_id = str(ObjectId())
    corpus_path = os.path.join(training_dir, 'scraped', corpus_id)
    os.makedirs(corpus_path, exist_ok=True)

    uploaded_files = []
    failed_files = []

    try:
        # Extract ZIP file
        print("📦 Extracting ZIP file...")
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            zip_file.extractall(corpus_path)

        print("✅ Extraction complete!\n")

        # Find all resume files
        print("🔍 Searching for resume files...")
        resume_files = []
        for ext in ['*.pdf', '*.docx', '*.doc', '*.txt']:
            resume_files.extend(Path(corpus_path).rglob(ext))

        print(f"📄 Found {len(resume_files)} resume files\n")

        if not resume_files:
            print("❌ No resume files found in ZIP")
            return None

        # Process each resume
        print("🚀 Processing resumes...\n")
        for idx, file_path in enumerate(resume_files, 1):
            try:
                print(f"[{idx}/{len(resume_files)}] Processing: {file_path.name}...", end=' ')

                # Parse resume
                if file_path.suffix.lower() == '.txt':
                    # Handle text files
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    parsed = resume_parser.parse_resume_text(text)
                else:
                    # Handle PDF/DOCX
                    parsed = resume_parser.parse_resume(str(file_path))

                # Check for parsing errors
                if 'error' in parsed:
                    print(f"❌ Parse error: {parsed['error']}")
                    failed_files.append({
                        'filename': file_path.name,
                        'error': parsed['error']
                    })
                    continue

                # Calculate quality score
                quality_score = calculate_quality_score(parsed)

                # Determine category from folder structure
                category = file_path.parent.name if file_path.parent.name != corpus_id else 'general'

                # Create training resume record
                training_resume = {
                    'corpusId': corpus_id,
                    'filename': file_path.name,
                    'filePath': str(file_path),
                    'parsedData': parsed,
                    'qualityScore': quality_score,
                    'category': category,
                    'uploadedAt': datetime.utcnow(),
                    'source': 'local_zip',
                    'sourceFile': os.path.basename(zip_path)
                }

                # Save to database
                resume_id = TrainingResume.create(training_resume)

                uploaded_files.append({
                    'filename': file_path.name,
                    'resumeId': str(resume_id),
                    'qualityScore': quality_score,
                    'category': category
                })

                print(f"✅ Score: {quality_score:.2f}")

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failed_files.append({
                    'filename': file_path.name,
                    'error': str(e)
                })

        # Create corpus record
        if not corpus_name:
            corpus_name = f"Kaggle Import - {os.path.basename(zip_path)}"

        corpus_data = {
            '_id': ObjectId(corpus_id),
            'name': corpus_name,
            'description': f"Imported from {os.path.basename(zip_path)} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            'category': 'mixed',
            'uploadedBy': ObjectId(user_id),
            'filesCount': len(uploaded_files),
            'totalResumes': len(uploaded_files),
            'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
            'source': 'local_zip',
            'sourceFile': os.path.basename(zip_path),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }

        TrainingCorpus.create(corpus_data)

        # Print summary
        print(f"\n{'='*70}")
        print("IMPORT SUMMARY")
        print(f"{'='*70}")
        print(f"✅ Successfully imported: {len(uploaded_files)} resumes")
        print(f"❌ Failed: {len(failed_files)} resumes")
        print(f"📊 Average quality score: {corpus_data['averageQualityScore']:.2f}")
        print(f"🆔 Corpus ID: {corpus_id}")
        print(f"{'='*70}\n")

        # Show quality distribution
        if uploaded_files:
            high_quality = sum(1 for f in uploaded_files if f['qualityScore'] >= 0.7)
            medium_quality = sum(1 for f in uploaded_files if 0.4 <= f['qualityScore'] < 0.7)
            low_quality = sum(1 for f in uploaded_files if f['qualityScore'] < 0.4)

            print("Quality Distribution:")
            print(f"  High (≥0.7):   {high_quality} resumes ({high_quality/len(uploaded_files)*100:.1f}%)")
            print(f"  Medium (0.4-0.7): {medium_quality} resumes ({medium_quality/len(uploaded_files)*100:.1f}%)")
            print(f"  Low (<0.4):    {low_quality} resumes ({low_quality/len(uploaded_files)*100:.1f}%)")

        # Show categories
        if uploaded_files:
            categories = {}
            for f in uploaded_files:
                cat = f['category']
                categories[cat] = categories.get(cat, 0) + 1

            print("\nCategories Found:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {cat}: {count} resumes")

        # Show failed files if any
        if failed_files:
            print(f"\n❌ Failed Files ({len(failed_files)}):")
            for f in failed_files[:10]:  # Show first 10
                print(f"  - {f['filename']}: {f['error']}")
            if len(failed_files) > 10:
                print(f"  ... and {len(failed_files) - 10} more")

        print()

        return {
            'success': True,
            'corpus_id': corpus_id,
            'files_uploaded': len(uploaded_files),
            'files_failed': len(failed_files),
            'uploaded_files': uploaded_files,
            'failed_files': failed_files,
            'corpus': corpus_data
        }

    except Exception as e:
        print(f"\n❌ Error processing ZIP file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def calculate_quality_score(parsed_data):
    """Calculate quality score for a resume."""
    score = 0.0
    max_score = 10.0

    # Contact information (1 point)
    if parsed_data.get('contactInfo'):
        score += 1.0

    # Experience (3 points)
    experience = parsed_data.get('workExperience', [])
    if len(experience) > 0:
        score += 1.0
    if len(experience) >= 2:
        score += 1.0
    if len(experience) >= 3:
        score += 1.0

    # Education (2 points)
    education = parsed_data.get('education', [])
    if len(education) > 0:
        score += 1.5
    if len(education) >= 2:
        score += 0.5

    # Skills (2 points)
    skills = parsed_data.get('skills', [])
    if len(skills) >= 3:
        score += 1.0
    if len(skills) >= 6:
        score += 1.0

    # Length/completeness (2 points)
    text_length = len(parsed_data.get('raw_text', '') or parsed_data.get('rawText', ''))
    if text_length > 200:
        score += 1.0
    if text_length > 500:
        score += 1.0

    return round(score / max_score, 2)


def main():
    """Main function to import multiple ZIP files."""
    import argparse

    parser = argparse.ArgumentParser(description='Import resumes from local ZIP files')
    parser.add_argument('zip_files', nargs='+', help='Path(s) to ZIP file(s)')
    parser.add_argument('--user-id', help='User ID (defaults to new ObjectId)', default=None)
    parser.add_argument('--corpus-name', help='Custom corpus name', default=None)

    args = parser.parse_args()

    # Use provided user_id or create a new one
    user_id = args.user_id or str(ObjectId())

    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*18 + "Resume Import from ZIP Files" + " "*22 + "║")
    print("╚" + "="*68 + "╝")

    print(f"\n📋 Files to import: {len(args.zip_files)}")
    print(f"👤 User ID: {user_id}\n")

    total_uploaded = 0
    total_failed = 0
    corpus_ids = []

    for zip_file in args.zip_files:
        result = import_from_zip(zip_file, user_id, args.corpus_name)

        if result:
            total_uploaded += result['files_uploaded']
            total_failed += result['files_failed']
            corpus_ids.append(result['corpus_id'])

    # Final summary
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*24 + "FINAL SUMMARY" + " "*31 + "║")
    print("╚" + "="*68 + "╝\n")
    print(f"📦 ZIP files processed: {len(args.zip_files)}")
    print(f"✅ Total resumes imported: {total_uploaded}")
    print(f"❌ Total failed: {total_failed}")
    print(f"🗂️  Corpus IDs created: {len(corpus_ids)}")

    if corpus_ids:
        print("\nCorpus IDs:")
        for cid in corpus_ids:
            print(f"  - {cid}")

    print("\n🎉 Import complete! You can now use these corpora for training.\n")


if __name__ == "__main__":
    main()
