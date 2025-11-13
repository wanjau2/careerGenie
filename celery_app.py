"""Celery application for background task processing."""
import os
import logging
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'career_genie',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50
)


@celery_app.task(name='train_model_task', bind=True)
def train_model_task(self, job_id: str, resumes: list, hyperparameters: dict):
    """
    Background task for training ML models.

    Args:
        self: Celery task instance
        job_id: Training job ID
        resumes: List of resume data
        hyperparameters: Training hyperparameters

    Returns:
        Dictionary with training results
    """
    try:
        from models.training import TrainingJob
        from services.ml_training import train_resume_scoring_model

        # Update job status to running
        TrainingJob.update_status(job_id, 'running', progress=0)
        logger.info(f"Starting training job {job_id} with {len(resumes)} resumes")

        # Progress callback
        def on_progress(progress: int, message: str = ''):
            TrainingJob.update_status(job_id, 'running', progress=progress)
            self.update_state(
                state='PROGRESS',
                meta={'current': progress, 'total': 100, 'status': message}
            )

        # Train the model
        metrics = train_resume_scoring_model(
            resumes=resumes,
            hyperparameters=hyperparameters,
            on_progress=on_progress
        )

        # Mark job as completed
        TrainingJob.complete(job_id, metrics)
        logger.info(f"Training job {job_id} completed successfully")

        return {
            'job_id': job_id,
            'status': 'completed',
            'metrics': metrics
        }

    except Exception as e:
        logger.error(f"Error in training job {job_id}: {str(e)}")

        # Mark job as failed
        from models.training import TrainingJob
        TrainingJob.update_status(job_id, 'failed', error=str(e))

        # Re-raise exception for Celery to handle
        raise


@celery_app.task(name='auto_training_check', bind=True)
def auto_training_check(self):
    """
    Periodic task to check if automatic training should be triggered.

    This runs on a schedule (e.g., daily) to check if there's enough new data
    to warrant retraining the model.
    """
    try:
        from services.training_service import TrainingService

        logger.info("Running automatic training check")
        training_service = TrainingService()

        result = training_service.trigger_auto_training()

        if result.get('jobs_started', 0) > 0:
            logger.info(f"Auto-training triggered: {result['resumes_processed']} new resumes")
        else:
            logger.info("Auto-training skipped: insufficient new data")

        return result

    except Exception as e:
        logger.error(f"Error in auto-training check: {str(e)}")
        raise


@celery_app.task(name='process_user_resume_for_training', bind=True)
def process_user_resume_for_training(self, user_id: str, resume_path: str):
    """
    Background task to add user's resume to training corpus.

    Args:
        self: Celery task instance
        user_id: User ID
        resume_path: Path to resume file

    Returns:
        Dictionary with processing results
    """
    try:
        from models.training import TrainingResume
        from services.resume_parser import ResumeParser
        from datetime import datetime
        import shutil

        logger.info(f"Processing resume for user {user_id}")

        # Parse resume
        parser = ResumeParser()
        parsed = parser.parse_resume(resume_path)

        # Calculate quality score
        quality_score = _calculate_quality_score(parsed)

        # Only add to training corpus if quality is sufficient
        if quality_score >= 0.6:
            # Copy resume to training directory
            from services.training_service import TrainingService
            training_service = TrainingService()

            import os
            from bson import ObjectId

            # Create user corpus directory if not exists
            corpus_id = f"user_{user_id}"
            corpus_path = os.path.join(training_service.training_dir, 'resumes', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            # Copy resume file
            filename = os.path.basename(resume_path)
            dest_path = os.path.join(corpus_path, filename)
            shutil.copy2(resume_path, dest_path)

            # Create training resume record
            training_resume = {
                'corpusId': corpus_id,
                'userId': ObjectId(user_id),
                'filename': filename,
                'filePath': dest_path,
                'parsedData': parsed,
                'qualityScore': quality_score,
                'uploadedAt': datetime.utcnow(),
                'source': 'user_signup'
            }

            resume_id = TrainingResume.create(training_resume)
            logger.info(f"Added user resume to training corpus: {resume_id}")

            return {
                'success': True,
                'resume_id': str(resume_id),
                'quality_score': quality_score
            }
        else:
            logger.info(f"Resume quality too low ({quality_score}), skipping training corpus")
            return {
                'success': False,
                'reason': 'quality_too_low',
                'quality_score': quality_score
            }

    except Exception as e:
        logger.error(f"Error processing user resume: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def _calculate_quality_score(parsed_data: dict) -> float:
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


# Periodic task schedule
celery_app.conf.beat_schedule = {
    'auto-training-check-daily': {
        'task': 'auto_training_check',
        'schedule': 86400.0,  # Run once per day (in seconds)
    },
}
