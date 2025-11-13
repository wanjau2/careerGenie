"""Script to import resumes from CSV files (Kaggle datasets)."""
import os
import sys
import csv
import zipfile
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from services.resume_parser import ResumeParser
from models.training import TrainingCorpus, TrainingResume


def import_from_csv(csv_path, user_id, corpus_name=None, max_resumes=None):
    """
    Import resumes from a CSV file.

    Args:
        csv_path: Path to the CSV file
        user_id: User ID for ownership
        corpus_name: Optional name for the corpus
        max_resumes: Maximum number of resumes to import

    Returns:
        Dictionary with import results
    """
    print(f"\n{'='*70}")
    print(f"Importing resumes from CSV: {csv_path}")
    print(f"{'='*70}\n")

    if not os.path.exists(csv_path):
        print(f"❌ Error: File not found: {csv_path}")
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
        # Read CSV file
        print("📖 Reading CSV file...")

        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Try to detect the structure
            sample = f.read(1024)
            f.seek(0)

            # Use csv.Sniffer to detect delimiter
            try:
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(f, dialect=dialect)
            except:
                reader = csv.DictReader(f)

            rows = list(reader)

        print(f"✅ Found {len(rows)} resume entries\n")

        if not rows:
            print("❌ No data found in CSV")
            return None

        # Show column names
        print(f"📊 Columns found: {', '.join(rows[0].keys())}\n")

        # Determine which column contains resume text
        text_columns = ['Resume', 'resume', 'Resume_str', 'resume_str', 'text', 'Text', 'content', 'Content', 'resume_text']
        category_columns = ['Category', 'category', 'job_category', 'Job_Category', 'field', 'Field']

        resume_col = None
        category_col = None

        for col in rows[0].keys():
            if col in text_columns or 'resume' in col.lower():
                resume_col = col
            if col in category_columns or 'category' in col.lower():
                category_col = col

        if not resume_col:
            print("❌ Could not identify resume text column. Available columns:")
            for col in rows[0].keys():
                print(f"   - {col}")
            return None

        print(f"✅ Using '{resume_col}' as resume text column")
        if category_col:
            print(f"✅ Using '{category_col}' as category column")
        print()

        # Limit if specified
        if max_resumes:
            rows = rows[:max_resumes]
            print(f"📋 Limiting to {max_resumes} resumes\n")

        # Process each resume
        print("🚀 Processing resumes...\n")
        for idx, row in enumerate(rows, 1):
            try:
                resume_text = row.get(resume_col, '').strip()
                category = row.get(category_col, 'general') if category_col else 'general'

                if not resume_text or len(resume_text) < 50:
                    print(f"[{idx}/{len(rows)}] ⚠️  Skipping (too short)")
                    failed_files.append({
                        'index': idx,
                        'error': 'Resume text too short'
                    })
                    continue

                print(f"[{idx}/{len(rows)}] Processing {category}...", end=' ')

                # Parse resume
                parsed = resume_parser.parse_resume_text(resume_text)

                # Check for parsing errors
                if 'error' in parsed:
                    print(f"❌ {parsed['error']}")
                    failed_files.append({
                        'index': idx,
                        'error': parsed['error']
                    })
                    continue

                # Calculate quality score
                quality_score = calculate_quality_score(parsed)

                # Save as text file
                filename = f"resume_{idx:04d}_{category.replace(' ', '_')}.txt"
                file_path = os.path.join(corpus_path, filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(resume_text)

                # Create training resume record
                training_resume = {
                    'corpusId': corpus_id,
                    'filename': filename,
                    'filePath': file_path,
                    'parsedData': parsed,
                    'qualityScore': quality_score,
                    'category': category,
                    'uploadedAt': datetime.utcnow(),
                    'source': 'kaggle_csv',
                    'sourceFile': os.path.basename(csv_path),
                    'csvRowIndex': idx
                }

                # Save to database
                resume_id = TrainingResume.create(training_resume)

                uploaded_files.append({
                    'filename': filename,
                    'resumeId': str(resume_id),
                    'qualityScore': quality_score,
                    'category': category
                })

                print(f"✅ Score: {quality_score:.2f}")

                # Progress indicator
                if idx % 100 == 0:
                    print(f"\n   Progress: {idx}/{len(rows)} ({idx/len(rows)*100:.1f}%)\n")

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failed_files.append({
                    'index': idx,
                    'error': str(e)
                })

        # Create corpus record
        if not corpus_name:
            corpus_name = f"Kaggle CSV - {os.path.basename(csv_path)}"

        corpus_data = {
            '_id': ObjectId(corpus_id),
            'name': corpus_name,
            'description': f"Imported from {os.path.basename(csv_path)} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            'category': 'mixed',
            'uploadedBy': ObjectId(user_id),
            'filesCount': len(uploaded_files),
            'totalResumes': len(uploaded_files),
            'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
            'source': 'kaggle_csv',
            'sourceFile': os.path.basename(csv_path),
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
            print(f"  High (≥0.7):      {high_quality:4d} resumes ({high_quality/len(uploaded_files)*100:5.1f}%)")
            print(f"  Medium (0.4-0.7): {medium_quality:4d} resumes ({medium_quality/len(uploaded_files)*100:5.1f}%)")
            print(f"  Low (<0.4):       {low_quality:4d} resumes ({low_quality/len(uploaded_files)*100:5.1f}%)")

        # Show categories
        if uploaded_files:
            categories = {}
            for f in uploaded_files:
                cat = f['category']
                categories[cat] = categories.get(cat, 0) + 1

            print(f"\nCategories Found ({len(categories)} total):")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:15]:
                print(f"  {cat:25s}: {count:4d} resumes")

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
        print(f"\n❌ Error processing CSV file: {str(e)}")
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
    """Main function to import CSV files."""
    import argparse

    parser = argparse.ArgumentParser(description='Import resumes from CSV files')
    parser.add_argument('csv_file', help='Path to CSV file (or ZIP containing CSV)')
    parser.add_argument('--user-id', help='User ID (defaults to new ObjectId)', default=None)
    parser.add_argument('--corpus-name', help='Custom corpus name', default=None)
    parser.add_argument('--max-resumes', type=int, help='Maximum resumes to import', default=None)

    args = parser.parse_args()

    # Use provided user_id or create a new one
    user_id = args.user_id or str(ObjectId())

    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "Resume Import from CSV" + " "*26 + "║")
    print("╚" + "="*68 + "╝")

    print(f"\n👤 User ID: {user_id}")

    csv_path = args.csv_file

    # Check if it's a ZIP file
    if csv_path.endswith('.zip'):
        print(f"📦 Extracting CSV from ZIP file...")

        # Extract to temp location
        temp_dir = 'temp_extract'
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(csv_path, 'r') as zip_file:
            zip_file.extractall(temp_dir)

        # Find CSV file
        csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]

        if not csv_files:
            print("❌ No CSV file found in ZIP")
            return

        csv_path = os.path.join(temp_dir, csv_files[0])
        print(f"✅ Found CSV: {csv_files[0]}\n")

    # Import the CSV
    result = import_from_csv(csv_path, user_id, args.corpus_name, args.max_resumes)

    if result:
        print("\n🎉 Import complete! You can now use this corpus for training.")
        print(f"\nTo start training:")
        print(f"  POST /api/training/jobs/start")
        print(f"  {{ \"corpusIds\": [\"{result['corpus_id']}\"] }}\n")
    else:
        print("\n❌ Import failed. Please check the errors above.\n")


if __name__ == "__main__":
    main()
