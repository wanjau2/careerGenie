"""Training and model improvement routes."""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models.training import TrainingCorpus, TrainingJob
from models.user import User
from services.training_service import TrainingService
from services.google_forms_service import GoogleFormsService
from services.resume_scraper import ResumeScraper
from utils.helpers import (
    format_error_response,
    serialize_document,
    serialize_documents,
    calculate_skip_limit,
    get_pagination_metadata
)
from utils.validators import validate_pagination_params

logger = logging.getLogger(__name__)
training_bp = Blueprint('training', __name__, url_prefix='/api/training')

# Initialize services
training_service = TrainingService()
google_forms_service = GoogleFormsService()
resume_scraper = ResumeScraper()


@training_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_training_resumes():
    """
    Upload multiple resumes for training corpus.

    Form data:
    - files: Multiple resume files (PDF, DOCX)
    - corpusName: Name for this training corpus
    - description: Optional description
    - category: success/failed (for outcome tracking)

    Returns:
        JSON response with corpus ID and file count
    """
    try:
        user_id = get_jwt_identity()

        # Check if user is admin (optional - you can remove this for all users)
        user = User.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Get files from request
        if 'files' not in request.files:
            return jsonify(format_error_response("No files provided", 400))

        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify(format_error_response("No files selected", 400))

        # Get metadata
        corpus_name = request.form.get('corpusName', f"Corpus {datetime.utcnow().strftime('%Y-%m-%d')}")
        description = request.form.get('description', '')
        category = request.form.get('category', 'general')  # success, failed, general

        # Upload and process resumes
        result = training_service.upload_corpus(
            user_id=user_id,
            files=files,
            corpus_name=corpus_name,
            description=description,
            category=category
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Upload failed'), 500))

        return jsonify({
            'message': 'Training corpus uploaded successfully',
            'corpusId': result['corpus_id'],
            'filesUploaded': result['files_uploaded'],
            'filesFailed': result['files_failed'],
            'corpus': serialize_document(result['corpus'])
        }), 201

    except Exception as e:
        logger.error(f"Error uploading training corpus: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/corpora', methods=['GET'])
@jwt_required()
def get_training_corpora():
    """
    Get all training corpora.

    Query parameters:
    - page: Page number (default: 1)
    - pageSize: Items per page (default: 20)
    - category: Filter by category (success, failed, general)

    Returns:
        JSON response with list of corpora
    """
    try:
        user_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        category = request.args.get('category')

        is_valid, (validated_page, validated_page_size), error = validate_pagination_params(
            page, page_size
        )

        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Calculate pagination
        skip, limit = calculate_skip_limit(validated_page, validated_page_size)

        # Get corpora
        corpora = TrainingCorpus.get_all(category=category, skip=skip, limit=validated_page_size)
        total_count = TrainingCorpus.get_count(category=category)

        return jsonify({
            'corpora': serialize_documents(corpora),
            'meta': get_pagination_metadata(total_count, validated_page, validated_page_size)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching corpora: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/corpora/<corpus_id>', methods=['GET'])
@jwt_required()
def get_corpus_details(corpus_id):
    """
    Get detailed information about a specific corpus.

    Args:
        corpus_id: Training corpus ID

    Returns:
        JSON response with corpus details
    """
    try:
        corpus = TrainingCorpus.find_by_id(corpus_id)

        if not corpus:
            return jsonify(format_error_response("Corpus not found", 404))

        return jsonify({
            'corpus': serialize_document(corpus)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching corpus: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/corpora/<corpus_id>', methods=['DELETE'])
@jwt_required()
def delete_corpus(corpus_id):
    """
    Delete a training corpus and its files.

    Args:
        corpus_id: Training corpus ID

    Returns:
        JSON response confirming deletion
    """
    try:
        user_id = get_jwt_identity()

        result = training_service.delete_corpus(corpus_id, user_id)

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Deletion failed'), 400))

        return jsonify({
            'message': 'Corpus deleted successfully',
            'corpusId': corpus_id
        }), 200

    except Exception as e:
        logger.error(f"Error deleting corpus: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/jobs/start', methods=['POST'])
@jwt_required()
def start_training_job():
    """
    Start a new training job to improve the model.

    Request body:
    {
        "corpusIds": ["corpus_id_1", "corpus_id_2"],  // Optional, uses all if not specified
        "modelType": "resume_scoring",  // resume_scoring, match_prediction, etc.
        "hyperparameters": {}  // Optional custom hyperparameters
    }

    Returns:
        JSON response with training job details
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        corpus_ids = data.get('corpusIds')
        model_type = data.get('modelType', 'resume_scoring')
        hyperparameters = data.get('hyperparameters', {})

        # Start training job
        result = training_service.start_training_job(
            user_id=user_id,
            corpus_ids=corpus_ids,
            model_type=model_type,
            hyperparameters=hyperparameters
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Failed to start training'), 500))

        return jsonify({
            'message': 'Training job started successfully',
            'jobId': result['job_id'],
            'job': serialize_document(result['job'])
        }), 201

    except Exception as e:
        logger.error(f"Error starting training job: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/jobs/<job_id>', methods=['GET'])
@jwt_required()
def get_training_job(job_id):
    """
    Get status and details of a training job.

    Args:
        job_id: Training job ID

    Returns:
        JSON response with job details
    """
    try:
        job = TrainingJob.find_by_id(job_id)

        if not job:
            return jsonify(format_error_response("Training job not found", 404))

        return jsonify({
            'job': serialize_document(job)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching training job: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_training_analytics():
    """
    Get training analytics and model performance metrics.

    Returns:
        JSON response with analytics data
    """
    try:
        analytics = training_service.get_training_analytics()

        return jsonify({
            'analytics': analytics
        }), 200

    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/search', methods=['GET'])
@jwt_required()
def search_training_resumes():
    """
    Search through training corpus resumes.

    Query parameters:
    - q: Search query
    - category: Filter by category
    - minScore: Minimum quality score
    - page: Page number
    - pageSize: Items per page

    Returns:
        JSON response with search results
    """
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category')
        min_score = request.args.get('minScore', type=float)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)

        results = training_service.search_resumes(
            query=query,
            category=category,
            min_score=min_score,
            page=page,
            page_size=page_size
        )

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/patterns', methods=['GET'])
@jwt_required()
def get_extracted_patterns():
    """
    Get extracted patterns from successful resumes.

    Query parameters:
    - patternType: skills, phrases, formats, structures

    Returns:
        JSON response with extracted patterns
    """
    try:
        pattern_type = request.args.get('patternType', 'all')

        patterns = training_service.get_extracted_patterns(pattern_type)

        return jsonify({
            'patterns': patterns
        }), 200

    except Exception as e:
        logger.error(f"Error fetching patterns: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_resume_quality():
    """
    Validate if a resume meets quality standards for training corpus.

    Request body:
    {
        "resumeText": "resume content...",
        "resumeUrl": "https://..." // or file path
    }

    Returns:
        JSON response with validation results
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("Request body required", 400))

        resume_text = data.get('resumeText')
        resume_url = data.get('resumeUrl')

        if not resume_text and not resume_url:
            return jsonify(format_error_response("Resume text or URL required", 400))

        validation = training_service.validate_resume_quality(resume_text, resume_url)

        return jsonify({
            'validation': validation
        }), 200

    except Exception as e:
        logger.error(f"Error validating resume: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/auto-train', methods=['POST'])
@jwt_required()
def trigger_auto_training():
    """
    Manually trigger automatic training based on recent user data.

    This endpoint allows admins to trigger the progressive learning system
    that normally runs automatically in the background.

    Returns:
        JSON response with training trigger status
    """
    try:
        user_id = get_jwt_identity()

        result = training_service.trigger_auto_training()

        return jsonify({
            'message': 'Auto-training triggered successfully',
            'jobsStarted': result.get('jobs_started', 0),
            'resumesProcessed': result.get('resumes_processed', 0)
        }), 200

    except Exception as e:
        logger.error(f"Error triggering auto-training: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


# ===== GOOGLE FORMS INTEGRATION ENDPOINTS =====

@training_bp.route('/google-forms/import-folder', methods=['POST'])
@jwt_required()
def import_from_google_drive():
    """
    Import resumes from a Google Drive folder.

    Request body:
    {
        "folderId": "google-drive-folder-id",
        "corpusName": "My Training Corpus",
        "category": "general"  // success, failed, general
    }

    Returns:
        JSON response with import results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'folderId' not in data:
            return jsonify(format_error_response("Google Drive folder ID required", 400))

        folder_id = data['folderId']
        corpus_name = data.get('corpusName', 'Google Forms Import')
        category = data.get('category', 'general')

        # Import resumes from folder
        result = google_forms_service.import_resumes_from_folder(
            folder_id=folder_id,
            user_id=user_id,
            corpus_name=corpus_name,
            category=category
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Import failed'), 500))

        return jsonify({
            'message': 'Resumes imported successfully from Google Drive',
            'corpusId': result['corpus_id'],
            'filesUploaded': result['files_uploaded'],
            'filesFailed': result['files_failed'],
            'corpus': serialize_document(result['corpus']),
            'uploadedFiles': result['uploaded_files'],
            'failedFiles': result['failed_files']
        }), 201

    except Exception as e:
        logger.error(f"Error importing from Google Drive: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/google-forms/import-sheets', methods=['POST'])
@jwt_required()
def import_from_google_sheets():
    """
    Import resumes from Google Sheets (Google Form responses).

    Request body:
    {
        "spreadsheetId": "google-sheets-id",
        "sheetName": "Form Responses 1",  // Optional
        "fileUrlColumn": "Resume File"  // Optional, column containing file URLs
    }

    Returns:
        JSON response with import results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'spreadsheetId' not in data:
            return jsonify(format_error_response("Google Sheets spreadsheet ID required", 400))

        spreadsheet_id = data['spreadsheetId']
        sheet_name = data.get('sheetName', 'Form Responses 1')
        file_url_column = data.get('fileUrlColumn', 'Resume File')

        # Import resumes from sheets
        result = google_forms_service.import_from_sheets(
            spreadsheet_id=spreadsheet_id,
            user_id=user_id,
            sheet_name=sheet_name,
            file_url_column=file_url_column
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Import failed'), 500))

        return jsonify({
            'message': 'Resumes imported successfully from Google Sheets',
            'corpusId': result['corpus_id'],
            'filesUploaded': result['files_uploaded'],
            'filesFailed': result['files_failed'],
            'corpus': serialize_document(result['corpus']),
            'uploadedFiles': result['uploaded_files'],
            'failedFiles': result['failed_files']
        }), 201

    except Exception as e:
        logger.error(f"Error importing from Google Sheets: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/google-forms/folder-info/<folder_id>', methods=['GET'])
@jwt_required()
def get_google_drive_folder_info(folder_id):
    """
    Get information about a Google Drive folder (preview before import).

    Args:
        folder_id: Google Drive folder ID

    Returns:
        JSON response with folder information
    """
    try:
        result = google_forms_service.get_folder_info(folder_id)

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Failed to get folder info'), 500))

        return jsonify({
            'folder': result['folder']
        }), 200

    except Exception as e:
        logger.error(f"Error getting folder info: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


# ===== WEB SCRAPING ENDPOINTS =====

@training_bp.route('/scrape/huggingface', methods=['POST'])
@jwt_required()
def scrape_huggingface_dataset():
    """
    Download resumes from Hugging Face public datasets.

    Request body:
    {
        "datasetName": "opensporks/resumes",  // Optional, defaults to opensporks/resumes
        "maxResumes": 100  // Optional, max number of resumes to download
    }

    Returns:
        JSON response with scraping results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        dataset_name = data.get('datasetName', 'opensporks/resumes')
        max_resumes = data.get('maxResumes', 100)

        # Download dataset
        result = resume_scraper.download_huggingface_dataset(
            user_id=user_id,
            dataset_name=dataset_name,
            max_resumes=max_resumes
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Scraping failed'), 500))

        return jsonify({
            'message': 'Resumes scraped successfully from Hugging Face',
            'corpusId': result['corpus_id'],
            'filesUploaded': result['files_uploaded'],
            'filesFailed': result['files_failed'],
            'corpus': serialize_document(result['corpus']),
            'uploadedFiles': result['uploaded_files'][:10],  # Show first 10
            'totalFiles': len(result['uploaded_files'])
        }), 201

    except Exception as e:
        logger.error(f"Error scraping Hugging Face: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/scrape/kaggle', methods=['POST'])
@jwt_required()
def scrape_kaggle_dataset():
    """
    Download resumes from Kaggle public datasets.

    Request body:
    {
        "datasetName": "snehaanbhawal/resume-dataset",  // Optional
        "maxResumes": 100  // Optional
    }

    Returns:
        JSON response with scraping results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        dataset_name = data.get('datasetName', 'snehaanbhawal/resume-dataset')
        max_resumes = data.get('maxResumes', 100)

        # Download dataset
        result = resume_scraper.download_from_kaggle(
            user_id=user_id,
            dataset_name=dataset_name,
            max_resumes=max_resumes
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Scraping failed'), 500))

        return jsonify({
            'message': 'Resumes scraped successfully from Kaggle',
            'corpusId': result['corpus_id'],
            'filesUploaded': result['files_uploaded'],
            'filesFailed': result['files_failed'],
            'corpus': serialize_document(result['corpus']),
            'uploadedFiles': result['uploaded_files'][:10],
            'totalFiles': len(result['uploaded_files'])
        }), 201

    except Exception as e:
        logger.error(f"Error scraping Kaggle: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@training_bp.route('/scrape/url', methods=['POST'])
@jwt_required()
def scrape_from_url():
    """
    Download resumes from a direct URL.

    Request body:
    {
        "url": "https://example.com/resumes.zip",
        "corpusName": "URL Import",  // Optional
        "isZip": true  // Whether the URL points to a ZIP file
    }

    Returns:
        JSON response with scraping results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'url' not in data:
            return jsonify(format_error_response("URL required", 400))

        url = data['url']
        corpus_name = data.get('corpusName', 'URL Import')
        is_zip = data.get('isZip', False)

        # Download from URL
        result = resume_scraper.download_from_url(
            user_id=user_id,
            url=url,
            corpus_name=corpus_name,
            is_zip=is_zip
        )

        if not result['success']:
            return jsonify(format_error_response(result.get('error', 'Download failed'), 500))

        return jsonify({
            'message': 'Resumes downloaded successfully from URL',
            'corpusId': result['corpus_id'],
            'filesUploaded': result['files_uploaded'],
            'filesFailed': result['files_failed'],
            'corpus': serialize_document(result['corpus'])
        }), 201

    except Exception as e:
        logger.error(f"Error downloading from URL: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
