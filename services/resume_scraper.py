"""Resume scraper service for collecting training data from public sources."""
import os
import logging
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import zipfile
import io
from bson import ObjectId

from models.training import TrainingCorpus, TrainingResume
from services.resume_parser import ResumeParser

logger = logging.getLogger(__name__)


class ResumeScraper:
    """Service for scraping and downloading resume samples from public datasets."""

    def __init__(self):
        """Initialize resume scraper."""
        self.resume_parser = ResumeParser()
        self.training_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Ensure training directories exist
        os.makedirs(os.path.join(self.training_dir, 'scraped'), exist_ok=True)

    def download_huggingface_dataset(
        self,
        user_id: str,
        dataset_name: str = "opensporks/resumes",
        max_resumes: int = 100
    ) -> Dict:
        """
        Download resume dataset from Hugging Face.

        Args:
            user_id: User ID importing the resumes
            dataset_name: Hugging Face dataset name
            max_resumes: Maximum number of resumes to download

        Returns:
            Dictionary with import results
        """
        try:
            from datasets import load_dataset

            logger.info(f"Loading Hugging Face dataset: {dataset_name}")

            # Create corpus directory
            corpus_id = str(ObjectId())
            corpus_path = os.path.join(self.training_dir, 'scraped', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            # Load dataset
            dataset = load_dataset(dataset_name, split='train')

            if max_resumes:
                dataset = dataset.select(range(min(max_resumes, len(dataset))))

            uploaded_files = []
            failed_files = []

            # Process each resume
            for idx, item in enumerate(dataset):
                try:
                    # Extract resume text
                    resume_text = item.get('resume_str', '') or item.get('text', '')
                    category = item.get('category', 'general')

                    if not resume_text:
                        logger.warning(f"Empty resume text at index {idx}")
                        continue

                    # Save as text file
                    filename = f"resume_{idx:04d}_{category}.txt"
                    file_path = os.path.join(corpus_path, filename)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(resume_text)

                    # Parse resume
                    parsed = self.resume_parser.parse_resume_text(resume_text)

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(parsed)

                    # Create training resume record
                    training_resume = {
                        'corpusId': corpus_id,
                        'filename': filename,
                        'filePath': file_path,
                        'parsedData': parsed,
                        'qualityScore': quality_score,
                        'category': category,
                        'uploadedAt': datetime.utcnow(),
                        'source': 'huggingface',
                        'sourceDataset': dataset_name
                    }

                    # Save to database
                    resume_id = TrainingResume.create(training_resume)

                    uploaded_files.append({
                        'filename': filename,
                        'resumeId': str(resume_id),
                        'qualityScore': quality_score,
                        'category': category
                    })

                    logger.info(f"Imported resume {idx + 1}/{len(dataset)}")

                    # Small delay to avoid overwhelming the system
                    if idx % 10 == 0:
                        time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error processing resume {idx}: {str(e)}")
                    failed_files.append({
                        'index': idx,
                        'error': str(e)
                    })

            # Create corpus record
            corpus_data = {
                '_id': ObjectId(corpus_id),
                'name': f"Hugging Face - {dataset_name}",
                'description': f"Downloaded from Hugging Face on {datetime.utcnow().strftime('%Y-%m-%d')}",
                'category': 'mixed',
                'uploadedBy': ObjectId(user_id),
                'filesCount': len(uploaded_files),
                'totalResumes': len(uploaded_files),
                'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
                'source': 'huggingface',
                'sourceDataset': dataset_name,
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }

            TrainingCorpus.create(corpus_data)

            return {
                'success': True,
                'corpus_id': corpus_id,
                'corpus': corpus_data,
                'files_uploaded': len(uploaded_files),
                'files_failed': len(failed_files),
                'uploaded_files': uploaded_files,
                'failed_files': failed_files
            }

        except ImportError:
            return {
                'success': False,
                'error': 'datasets library not installed. Run: pip install datasets'
            }
        except Exception as e:
            logger.error(f"Error downloading Hugging Face dataset: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_from_kaggle(
        self,
        user_id: str,
        dataset_name: str = "snehaanbhawal/resume-dataset",
        max_resumes: Optional[int] = 100
    ) -> Dict:
        """
        Download resume dataset from Kaggle.

        Args:
            user_id: User ID importing the resumes
            dataset_name: Kaggle dataset name
            max_resumes: Maximum number of resumes to download (None for all)

        Returns:
            Dictionary with import results
        """
        try:
            import kaggle

            logger.info(f"Downloading Kaggle dataset: {dataset_name}")

            # Create corpus directory
            corpus_id = str(ObjectId())
            corpus_path = os.path.join(self.training_dir, 'scraped', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            # Download dataset
            kaggle.api.dataset_download_files(
                dataset_name,
                path=corpus_path,
                unzip=True
            )

            # Find all PDF and DOCX files
            resume_files = []
            for ext in ['*.pdf', '*.docx', '*.doc', '*.txt']:
                resume_files.extend(Path(corpus_path).rglob(ext))

            if max_resumes:
                resume_files = resume_files[:max_resumes]

            uploaded_files = []
            failed_files = []

            # Process each resume
            for idx, file_path in enumerate(resume_files):
                try:
                    # Parse resume
                    parsed = self.resume_parser.parse_resume(str(file_path))

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(parsed)

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
                        'source': 'kaggle',
                        'sourceDataset': dataset_name
                    }

                    # Save to database
                    resume_id = TrainingResume.create(training_resume)

                    uploaded_files.append({
                        'filename': file_path.name,
                        'resumeId': str(resume_id),
                        'qualityScore': quality_score,
                        'category': category
                    })

                    logger.info(f"Imported resume {idx + 1}/{len(resume_files)}: {file_path.name}")

                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {str(e)}")
                    failed_files.append({
                        'filename': file_path.name,
                        'error': str(e)
                    })

            # Create corpus record
            corpus_data = {
                '_id': ObjectId(corpus_id),
                'name': f"Kaggle - {dataset_name}",
                'description': f"Downloaded from Kaggle on {datetime.utcnow().strftime('%Y-%m-%d')}",
                'category': 'mixed',
                'uploadedBy': ObjectId(user_id),
                'filesCount': len(uploaded_files),
                'totalResumes': len(uploaded_files),
                'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
                'source': 'kaggle',
                'sourceDataset': dataset_name,
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }

            TrainingCorpus.create(corpus_data)

            return {
                'success': True,
                'corpus_id': corpus_id,
                'corpus': corpus_data,
                'files_uploaded': len(uploaded_files),
                'files_failed': len(failed_files),
                'uploaded_files': uploaded_files,
                'failed_files': failed_files
            }

        except ImportError:
            return {
                'success': False,
                'error': 'kaggle library not installed. Run: pip install kaggle'
            }
        except Exception as e:
            logger.error(f"Error downloading Kaggle dataset: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_from_url(
        self,
        user_id: str,
        url: str,
        corpus_name: str = "URL Import",
        is_zip: bool = False
    ) -> Dict:
        """
        Download resumes from a direct URL.

        Args:
            user_id: User ID importing the resumes
            url: URL to download from
            corpus_name: Name for the corpus
            is_zip: Whether the URL points to a ZIP file

        Returns:
            Dictionary with import results
        """
        try:
            logger.info(f"Downloading from URL: {url}")

            # Create corpus directory
            corpus_id = str(ObjectId())
            corpus_path = os.path.join(self.training_dir, 'scraped', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            # Download file
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            uploaded_files = []
            failed_files = []

            if is_zip:
                # Handle ZIP file
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                    # Extract all files
                    zip_file.extractall(corpus_path)

                    # Find all resume files
                    resume_files = []
                    for ext in ['*.pdf', '*.docx', '*.doc', '*.txt']:
                        resume_files.extend(Path(corpus_path).rglob(ext))

                    # Process each resume
                    for file_path in resume_files:
                        try:
                            parsed = self.resume_parser.parse_resume(str(file_path))
                            quality_score = self._calculate_quality_score(parsed)

                            training_resume = {
                                'corpusId': corpus_id,
                                'filename': file_path.name,
                                'filePath': str(file_path),
                                'parsedData': parsed,
                                'qualityScore': quality_score,
                                'uploadedAt': datetime.utcnow(),
                                'source': 'url',
                                'sourceUrl': url
                            }

                            resume_id = TrainingResume.create(training_resume)

                            uploaded_files.append({
                                'filename': file_path.name,
                                'resumeId': str(resume_id),
                                'qualityScore': quality_score
                            })

                        except Exception as e:
                            logger.error(f"Error processing {file_path.name}: {str(e)}")
                            failed_files.append({
                                'filename': file_path.name,
                                'error': str(e)
                            })
            else:
                # Handle single file
                filename = url.split('/')[-1]
                if '?' in filename:
                    filename = filename.split('?')[0]

                file_path = os.path.join(corpus_path, filename)

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                try:
                    parsed = self.resume_parser.parse_resume(file_path)
                    quality_score = self._calculate_quality_score(parsed)

                    training_resume = {
                        'corpusId': corpus_id,
                        'filename': filename,
                        'filePath': file_path,
                        'parsedData': parsed,
                        'qualityScore': quality_score,
                        'uploadedAt': datetime.utcnow(),
                        'source': 'url',
                        'sourceUrl': url
                    }

                    resume_id = TrainingResume.create(training_resume)

                    uploaded_files.append({
                        'filename': filename,
                        'resumeId': str(resume_id),
                        'qualityScore': quality_score
                    })

                except Exception as e:
                    failed_files.append({
                        'filename': filename,
                        'error': str(e)
                    })

            # Create corpus record
            corpus_data = {
                '_id': ObjectId(corpus_id),
                'name': corpus_name,
                'description': f"Downloaded from {url} on {datetime.utcnow().strftime('%Y-%m-%d')}",
                'category': 'general',
                'uploadedBy': ObjectId(user_id),
                'filesCount': len(uploaded_files),
                'totalResumes': len(uploaded_files),
                'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
                'source': 'url',
                'sourceUrl': url,
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }

            TrainingCorpus.create(corpus_data)

            return {
                'success': True,
                'corpus_id': corpus_id,
                'corpus': corpus_data,
                'files_uploaded': len(uploaded_files),
                'files_failed': len(failed_files),
                'uploaded_files': uploaded_files,
                'failed_files': failed_files
            }

        except Exception as e:
            logger.error(f"Error downloading from URL: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_quality_score(self, parsed_data: Dict) -> float:
        """
        Calculate quality score for a resume.

        Args:
            parsed_data: Parsed resume data

        Returns:
            Quality score between 0 and 1
        """
        score = 0.0
        max_score = 10.0

        # Contact information (1 point)
        if parsed_data.get('contact'):
            score += 1.0

        # Experience (3 points)
        experience = parsed_data.get('experience', [])
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
        text_length = len(parsed_data.get('raw_text', ''))
        if text_length > 200:
            score += 1.0
        if text_length > 500:
            score += 1.0

        return round(score / max_score, 2)
