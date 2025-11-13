"""Training service for progressive model improvement."""
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from bson import ObjectId

from models.training import TrainingCorpus, TrainingJob, TrainingResume
from services.resume_parser import ResumeParser
from config.database import get_training_collection, get_users_collection

logger = logging.getLogger(__name__)


class TrainingService:
    """Service for managing training data and progressive learning."""

    def __init__(self):
        """Initialize training service."""
        self.training_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')
        self.resume_parser = ResumeParser()

        # Ensure training directories exist
        os.makedirs(os.path.join(self.training_dir, 'resumes'), exist_ok=True)
        os.makedirs(os.path.join(self.training_dir, 'models'), exist_ok=True)
        os.makedirs(os.path.join(self.training_dir, 'checkpoints'), exist_ok=True)

    def upload_corpus(
        self,
        user_id: str,
        files: List,
        corpus_name: str,
        description: str = '',
        category: str = 'general'
    ) -> Dict:
        """
        Upload multiple resumes to create a training corpus.

        Args:
            user_id: ID of user uploading
            files: List of file uploads
            corpus_name: Name for this corpus
            description: Optional description
            category: Category (success, failed, general)

        Returns:
            Dictionary with corpus ID and upload results
        """
        try:
            uploaded_files = []
            failed_files = []

            # Create corpus directory
            corpus_id = str(ObjectId())
            corpus_path = os.path.join(self.training_dir, 'resumes', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            # Process each file
            for file in files:
                try:
                    if file.filename == '':
                        continue

                    filename = secure_filename(file.filename)
                    if not filename.lower().endswith(('.pdf', '.docx', '.doc')):
                        failed_files.append({
                            'filename': filename,
                            'error': 'Invalid file type'
                        })
                        continue

                    # Save file
                    file_path = os.path.join(corpus_path, filename)
                    file.save(file_path)

                    # Parse resume
                    parsed = self.resume_parser.parse_resume(file_path)

                    # Create training resume record
                    training_resume = {
                        'corpusId': corpus_id,
                        'filename': filename,
                        'filePath': file_path,
                        'parsedData': parsed,
                        'qualityScore': self._calculate_quality_score(parsed),
                        'uploadedAt': datetime.utcnow()
                    }

                    # Save to database
                    resume_id = TrainingResume.create(training_resume)

                    uploaded_files.append({
                        'filename': filename,
                        'resumeId': str(resume_id),
                        'qualityScore': training_resume['qualityScore']
                    })

                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    failed_files.append({
                        'filename': file.filename,
                        'error': str(e)
                    })

            # Create corpus record
            corpus_data = {
                '_id': ObjectId(corpus_id),
                'name': corpus_name,
                'description': description,
                'category': category,
                'uploadedBy': ObjectId(user_id),
                'filesCount': len(uploaded_files),
                'totalResumes': len(uploaded_files),
                'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }

            corpus = TrainingCorpus.create(corpus_data)

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
            logger.error(f"Error uploading corpus: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_corpus(self, corpus_id: str, user_id: str) -> Dict:
        """
        Delete a training corpus and its files.

        Args:
            corpus_id: Corpus ID to delete
            user_id: User requesting deletion

        Returns:
            Dictionary with success status
        """
        try:
            import shutil

            # Get corpus
            corpus = TrainingCorpus.find_by_id(corpus_id)
            if not corpus:
                return {'success': False, 'error': 'Corpus not found'}

            # Delete corpus directory
            corpus_path = os.path.join(self.training_dir, 'resumes', corpus_id)
            if os.path.exists(corpus_path):
                shutil.rmtree(corpus_path)

            # Delete database records
            TrainingResume.delete_by_corpus(corpus_id)
            TrainingCorpus.delete(corpus_id)

            return {'success': True}

        except Exception as e:
            logger.error(f"Error deleting corpus: {str(e)}")
            return {'success': False, 'error': str(e)}

    def start_training_job(
        self,
        user_id: str,
        corpus_ids: Optional[List[str]] = None,
        model_type: str = 'resume_scoring',
        hyperparameters: Dict = None
    ) -> Dict:
        """
        Start a new training job.

        Args:
            user_id: User starting the job
            corpus_ids: List of corpus IDs to train on (None = all)
            model_type: Type of model to train
            hyperparameters: Custom hyperparameters

        Returns:
            Dictionary with job ID and details
        """
        try:
            # Get training data
            if corpus_ids:
                resumes = TrainingResume.get_by_corpora(corpus_ids)
            else:
                resumes = TrainingResume.get_all()

            if not resumes or len(resumes) < 10:
                return {
                    'success': False,
                    'error': 'Insufficient training data (minimum 10 resumes required)'
                }

            # Create training job
            job_data = {
                'modelType': model_type,
                'corpusIds': corpus_ids or [],
                'resumeCount': len(resumes),
                'status': 'pending',
                'progress': 0,
                'startedBy': ObjectId(user_id),
                'startedAt': datetime.utcnow(),
                'hyperparameters': hyperparameters or {},
                'metrics': {}
            }

            job_id = TrainingJob.create(job_data)

            # Queue training job (will be processed by background worker)
            self._queue_training_job(str(job_id), resumes, hyperparameters)

            job_data['_id'] = job_id

            return {
                'success': True,
                'job_id': str(job_id),
                'job': job_data
            }

        except Exception as e:
            logger.error(f"Error starting training job: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_training_analytics(self) -> Dict:
        """
        Get training analytics and model performance metrics.

        Returns:
            Dictionary with analytics data
        """
        try:
            # Get corpus stats
            total_corpora = TrainingCorpus.get_count()
            total_resumes = TrainingResume.get_count()

            # Get category breakdown
            categories = TrainingCorpus.get_category_breakdown()

            # Get recent training jobs
            recent_jobs = TrainingJob.get_recent(limit=10)

            # Get average quality scores
            avg_quality = TrainingResume.get_average_quality_score()

            # Get model performance (from latest completed job)
            latest_model = TrainingJob.get_latest_completed()
            model_performance = latest_model.get('metrics', {}) if latest_model else {}

            return {
                'totalCorpora': total_corpora,
                'totalResumes': total_resumes,
                'averageQualityScore': avg_quality,
                'categoryBreakdown': categories,
                'recentJobs': recent_jobs,
                'modelPerformance': model_performance,
                'lastTrainingDate': latest_model.get('completedAt') if latest_model else None
            }

        except Exception as e:
            logger.error(f"Error fetching analytics: {str(e)}")
            return {}

    def search_resumes(
        self,
        query: str = '',
        category: Optional[str] = None,
        min_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Search through training corpus resumes.

        Args:
            query: Search query
            category: Filter by category
            min_score: Minimum quality score
            page: Page number
            page_size: Items per page

        Returns:
            Dictionary with search results
        """
        try:
            results = TrainingResume.search(
                query=query,
                category=category,
                min_score=min_score,
                skip=(page - 1) * page_size,
                limit=page_size
            )

            total_count = TrainingResume.count_search(query, category, min_score)

            return {
                'resumes': results,
                'meta': {
                    'page': page,
                    'pageSize': page_size,
                    'totalCount': total_count,
                    'totalPages': (total_count + page_size - 1) // page_size
                }
            }

        except Exception as e:
            logger.error(f"Error searching resumes: {str(e)}")
            return {'resumes': [], 'meta': {}}

    def get_extracted_patterns(self, pattern_type: str = 'all') -> Dict:
        """
        Get extracted patterns from successful resumes.

        Args:
            pattern_type: Type of patterns (skills, phrases, formats, structures, all)

        Returns:
            Dictionary with extracted patterns
        """
        try:
            patterns = {}

            if pattern_type in ['skills', 'all']:
                patterns['skills'] = TrainingResume.get_common_skills(min_frequency=5)

            if pattern_type in ['phrases', 'all']:
                patterns['phrases'] = TrainingResume.get_common_phrases(min_frequency=3)

            if pattern_type in ['formats', 'all']:
                patterns['formats'] = TrainingResume.get_format_patterns()

            if pattern_type in ['structures', 'all']:
                patterns['structures'] = TrainingResume.get_structure_patterns()

            return patterns

        except Exception as e:
            logger.error(f"Error extracting patterns: {str(e)}")
            return {}

    def validate_resume_quality(
        self,
        resume_text: Optional[str] = None,
        resume_url: Optional[str] = None
    ) -> Dict:
        """
        Validate if a resume meets quality standards.

        Args:
            resume_text: Resume content
            resume_url: Resume file path or URL

        Returns:
            Dictionary with validation results
        """
        try:
            # Parse resume
            if resume_url:
                parsed = self.resume_parser.parse_resume(resume_url)
            elif resume_text:
                parsed = self.resume_parser.parse_text(resume_text)
            else:
                return {'valid': False, 'error': 'No resume provided'}

            # Calculate quality score
            quality_score = self._calculate_quality_score(parsed)

            # Check quality criteria
            criteria = {
                'hasContact': bool(parsed.get('contact')),
                'hasExperience': bool(parsed.get('experience')),
                'hasEducation': bool(parsed.get('education')),
                'hasSkills': bool(parsed.get('skills')),
                'sufficientLength': len(parsed.get('raw_text', '')) > 200,
                'qualityScore': quality_score
            }

            is_valid = (
                quality_score >= 0.6 and
                criteria['hasContact'] and
                criteria['hasExperience'] and
                criteria['sufficientLength']
            )

            return {
                'valid': is_valid,
                'qualityScore': quality_score,
                'criteria': criteria,
                'recommendations': self._get_quality_recommendations(criteria)
            }

        except Exception as e:
            logger.error(f"Error validating resume: {str(e)}")
            return {'valid': False, 'error': str(e)}

    def trigger_auto_training(self) -> Dict:
        """
        Trigger automatic training based on recent user data.

        This is called periodically or when sufficient new data is available.

        Returns:
            Dictionary with trigger results
        """
        try:
            # Check if enough new data since last training
            last_job = TrainingJob.get_latest_completed()
            last_training_date = last_job.get('completedAt') if last_job else datetime(2020, 1, 1)

            new_resumes = TrainingResume.count_since(last_training_date)

            if new_resumes < 50:  # Need at least 50 new resumes
                return {
                    'jobs_started': 0,
                    'resumes_processed': 0,
                    'message': 'Insufficient new data for training'
                }

            # Start training job with all data
            result = self.start_training_job(
                user_id='system',
                corpus_ids=None,  # Use all corpora
                model_type='resume_scoring'
            )

            if result['success']:
                return {
                    'jobs_started': 1,
                    'resumes_processed': new_resumes
                }
            else:
                return {
                    'jobs_started': 0,
                    'resumes_processed': 0,
                    'error': result.get('error')
                }

        except Exception as e:
            logger.error(f"Error triggering auto-training: {str(e)}")
            return {'jobs_started': 0, 'resumes_processed': 0, 'error': str(e)}

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

    def _get_quality_recommendations(self, criteria: Dict) -> List[str]:
        """Get recommendations for improving resume quality."""
        recommendations = []

        if not criteria['hasContact']:
            recommendations.append('Add complete contact information')
        if not criteria['hasExperience']:
            recommendations.append('Add work experience section')
        if not criteria['hasEducation']:
            recommendations.append('Add education details')
        if not criteria['hasSkills']:
            recommendations.append('Add skills section')
        if not criteria['sufficientLength']:
            recommendations.append('Provide more detailed information')
        if criteria['qualityScore'] < 0.7:
            recommendations.append('Improve overall resume structure and content')

        return recommendations

    def _queue_training_job(self, job_id: str, resumes: List, hyperparameters: Dict):
        """
        Queue a training job for background processing.

        Args:
            job_id: Training job ID
            resumes: List of resume data
            hyperparameters: Training hyperparameters
        """
        try:
            # If Celery is available, use it
            from celery_app import train_model_task
            train_model_task.delay(job_id, resumes, hyperparameters)
        except ImportError:
            # Fallback: process inline (for development)
            logger.warning("Celery not available, processing training inline")
            self._process_training_inline(job_id, resumes, hyperparameters)

    def _process_training_inline(self, job_id: str, resumes: List, hyperparameters: Dict):
        """
        Process training job inline (fallback when no Celery).

        Args:
            job_id: Training job ID
            resumes: List of resume data
            hyperparameters: Training hyperparameters
        """
        try:
            # Update job status
            TrainingJob.update_status(job_id, 'running', progress=0)

            # Simulate training (replace with actual ML training)
            import time
            for i in range(10):
                time.sleep(0.5)  # Simulate work
                progress = (i + 1) * 10
                TrainingJob.update_status(job_id, 'running', progress=progress)

            # Mark as completed
            metrics = {
                'accuracy': 0.85,
                'precision': 0.82,
                'recall': 0.88,
                'f1Score': 0.85
            }

            TrainingJob.complete(job_id, metrics)
            logger.info(f"Training job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Error processing training job {job_id}: {str(e)}")
            TrainingJob.update_status(job_id, 'failed', error=str(e))
