"""Onboarding routes for multi-step user registration."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from models.user_enhanced import EnhancedUser
from models.user import User
from services.resume_parser import ResumeParser
from services.skill_recommendation import SkillRecommendationService
from services.skill_taxonomy import SkillTaxonomyService
from utils.validators import validate_required_fields
from config.database import get_users_collection

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/api/onboarding')


@onboarding_bp.route('/start', methods=['POST'])
@jwt_required()
def start_onboarding():
    """
    Start the onboarding process.
    Initialize onboarding state for user.

    Returns:
        JSON with onboarding status
    """
    user_id = get_jwt_identity()
    users = get_users_collection()

    # Update user onboarding state
    result = users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'onboardingStep': 1,
                'onboardingCompleted': False
            }
        }
    )

    if result.modified_count == 0:
        return jsonify({'error': 'Failed to start onboarding'}), 400

    return jsonify({
        'message': 'Onboarding started',
        'currentStep': 1,
        'totalSteps': 5
    }), 200


@onboarding_bp.route('/step/<int:step>', methods=['POST'])
@jwt_required()
def complete_onboarding_step(step):
    """
    Complete a specific onboarding step and save data.

    Step 1: Basic Information (name, phone, location)
    Step 2: Professional Background (career level, experience, current role)
    Step 3: Work Experience & Education
    Step 4: Skills Selection
    Step 5: Job Preferences

    Args:
        step: Step number (1-5)

    Returns:
        JSON with next step info
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate step number
    if step < 1 or step > 5:
        return jsonify({'error': 'Invalid step number'}), 400

    # Save step data
    success = EnhancedUser.update_onboarding_progress(user_id, step, data)

    if not success:
        return jsonify({'error': 'Failed to save onboarding data'}), 400

    # Check if this is the final step
    if step == 5:
        return jsonify({
            'message': 'Onboarding step completed',
            'currentStep': step,
            'nextStep': 'complete',
            'totalSteps': 5
        }), 200

    return jsonify({
        'message': 'Onboarding step completed',
        'currentStep': step,
        'nextStep': step + 1,
        'totalSteps': 5
    }), 200


@onboarding_bp.route('/complete', methods=['POST'])
@jwt_required()
def complete_onboarding():
    """
    Mark onboarding as completed and save all onboarding data.

    Expected request body:
    - jobTitle: User's desired job title
    - skills: List of user skills
    - experience: Experience level
    - location: Location object {city, formatted}
    - preferences: Preferences object {jobTypes, salaryMin, salaryMax, autoApplyEnabled}
    - bio: Optional bio/summary

    Returns:
        JSON with completion status
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Save all onboarding data and mark as complete
    success = EnhancedUser.complete_onboarding_with_data(user_id, data)

    if not success:
        return jsonify({'error': 'Failed to complete onboarding'}), 400

    return jsonify({
        'message': 'Onboarding completed successfully',
        'onboardingCompleted': True
    }), 200


@onboarding_bp.route('/status', methods=['GET'])
@jwt_required()
def get_onboarding_status():
    """
    Get current onboarding status for user.

    Returns:
        JSON with current step and completion status
    """
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'onboardingCompleted': user.get('onboardingCompleted', False),
        'currentStep': user.get('onboardingStep', 0),
        'totalSteps': 5
    }), 200


@onboarding_bp.route('/parse-resume', methods=['POST'])
@jwt_required()
def parse_resume():
    """
    Parse uploaded resume and extract structured data.
    Supports PDF and DOCX formats.
    Uses AI-powered parsing with fallback to rule-based parsing.

    Returns:
        JSON with parsed resume data
    """
    user_id = get_jwt_identity()

    # Check if file is present
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided'}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    allowed_extensions = {'pdf', 'docx', 'doc'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Only PDF and DOCX are supported'}), 400

    try:
        # Save file temporarily
        import os
        import tempfile

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f'{user_id}_{file.filename}')
        file.save(temp_path)

        # Parse resume
        parser = ResumeParser()
        parsed_data = parser.parse_resume(temp_path)

        # Queue resume for training corpus (background task)
        try:
            from celery_app import process_user_resume_for_training
            process_user_resume_for_training.delay(user_id, temp_path)
        except ImportError:
            # Celery not available, skip training corpus addition
            pass

        # Clean up temp file (will be copied by background task if Celery is available)
        # For now, we keep it temporarily for the background task
        # The background task will handle cleanup

        # Optionally merge with user profile
        merge_with_profile = request.form.get('mergeWithProfile', 'false').lower() == 'true'

        if merge_with_profile:
            # Update user profile with parsed data
            users = get_users_collection()
            users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'profile.phone': parsed_data.get('contactInfo', {}).get('phone'),
                        'profile.location': parsed_data.get('contactInfo', {}).get('location', {}),
                        'workExperience': parsed_data.get('workExperience', []),
                        'education': parsed_data.get('education', []),
                        'skills': [
                            {'name': skill, 'source': 'parsed', 'proficiency': 'intermediate'}
                            for skill in parsed_data.get('skills', [])
                        ],
                        'professional.summary': parsed_data.get('summary', ''),
                        'resumes.parsed': parsed_data
                    }
                }
            )

        return jsonify({
            'success': True,
            'parsedData': parsed_data,
            'merged': merge_with_profile
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to parse resume: {str(e)}'
        }), 500


@onboarding_bp.route('/skills/recommend', methods=['POST'])
@jwt_required()
def recommend_skills():
    """
    Get diverse skill recommendations for user during onboarding.
    Returns skills across ALL industries if user hasn't specified preferences,
    or focused recommendations if industries are specified.

    Request body should include:
    - jobPreferences (optional): target industries, roles
    - professional (optional): career level, experience
    - skills (optional): current skills

    Returns:
        JSON with organized skill recommendations
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    # Get user's current profile
    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Merge request data with user profile
    user_data = {
        'jobPreferences': data.get('jobPreferences', user.get('jobPreferences', {})),
        'professional': data.get('professional', user.get('professional', {})),
        'skills': data.get('skills', user.get('skills', []))
    }

    try:
        # Get skill recommendations
        recommender = SkillRecommendationService()
        recommendations = recommender.get_onboarding_skill_recommendations(user_data)

        return jsonify({
            'success': True,
            'recommendations': recommendations
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate recommendations: {str(e)}'
        }), 500


@onboarding_bp.route('/skills/search', methods=['GET'])
@jwt_required()
def search_skills():
    """
    Search for skills across all industries.

    Query parameters:
    - q: Search query
    - industry: Optional industry filter

    Returns:
        JSON with matching skills
    """
    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400

    industry_filter = request.args.get('industry')

    try:
        taxonomy = SkillTaxonomyService()
        results = taxonomy.search_skills(query, industry_key=industry_filter)

        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500


@onboarding_bp.route('/skills/industries', methods=['GET'])
def get_all_industries():
    """
    Get list of all supported industries.
    Public endpoint - no authentication required.

    Returns:
        JSON with all industries
    """
    try:
        taxonomy = SkillTaxonomyService()
        industries = taxonomy.get_all_industries()

        return jsonify({
            'success': True,
            'industries': [
                {'key': key, 'name': name}
                for key, name in industries.items()
            ],
            'count': len(industries)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch industries: {str(e)}'
        }), 500


@onboarding_bp.route('/skills/categories/<industry_key>', methods=['GET'])
def get_skill_categories(industry_key):
    """
    Get skill categories for a specific industry.
    Public endpoint - no authentication required.

    Args:
        industry_key: Industry identifier

    Returns:
        JSON with categories and skills
    """
    try:
        taxonomy = SkillTaxonomyService()
        categories = taxonomy.get_skills_by_industry(industry_key)

        if not categories:
            return jsonify({'error': 'Industry not found'}), 404

        # Format response
        formatted_categories = []
        for cat_key, cat_data in categories.items():
            formatted_categories.append({
                'key': cat_key,
                'name': cat_data['display_name'],
                'skills': cat_data['skills'],
                'skillCount': len(cat_data['skills'])
            })

        return jsonify({
            'success': True,
            'industry': industry_key,
            'categories': formatted_categories,
            'totalCategories': len(formatted_categories)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch categories: {str(e)}'
        }), 500


@onboarding_bp.route('/linkedin/merge', methods=['POST'])
@jwt_required()
def merge_linkedin_data():
    """
    Merge LinkedIn OAuth data with user profile during onboarding.

    Request body should include LinkedIn API response data.

    Returns:
        JSON with merge status
    """
    user_id = get_jwt_identity()
    linkedin_data = request.get_json()

    if not linkedin_data:
        return jsonify({'error': 'No LinkedIn data provided'}), 400

    try:
        success = EnhancedUser.update_linkedin_data(user_id, linkedin_data)

        if not success:
            return jsonify({'error': 'Failed to merge LinkedIn data'}), 400

        return jsonify({
            'success': True,
            'message': 'LinkedIn data merged successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Merge failed: {str(e)}'
        }), 500
