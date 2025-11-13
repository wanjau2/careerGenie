"""Job management and swipe tracking routes."""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models.job import Job
from models.swipe import Swipe, Application
from models.user import User
from utils.helpers import (
    format_error_response,
    serialize_document,
    serialize_documents,
    calculate_skip_limit,
    get_pagination_metadata,
    is_valid_object_id
)
from utils.validators import validate_pagination_params

logger = logging.getLogger(__name__)
jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')


@jobs_bp.route('', methods=['GET'])
@jwt_required()
def get_jobs():
    """
    Get jobs for swiping with filter support.

    Query parameters:
    - page: Page number (default: 1)
    - pageSize: Items per page (default: 20)
    - keywords: Search keywords (job title, description)
    - city: City filter
    - state: State filter
    - country: Country filter
    - remote: Remote jobs only (true/false)
    - minSalary: Minimum salary
    - maxSalary: Maximum salary
    - jobTypes: Comma-separated job types (Full-time,Part-time,Contract)
    - industries: Comma-separated industries
    - experienceLevels: Comma-separated experience levels (Entry,Mid,Senior)
    - companySize: Comma-separated company sizes (1-10,11-50,51-200,etc)
    - datePosted: Date filter (24h,3days,week,month)
    - minMatchScore: Minimum match score (0.0-1.0)
    - usePreferences: Use saved user preferences (true/false, default: true)

    Returns:
        JSON response with filtered job recommendations
    """
    try:
        user_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)

        is_valid, (validated_page, validated_page_size), error = validate_pagination_params(
            page, page_size
        )

        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Get user profile
        user = User.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Build filters from query parameters
        filters = {}
        use_preferences = request.args.get('usePreferences', 'true').lower() == 'true'

        # Start with user preferences if enabled
        if use_preferences:
            preferences = user.get('preferences', {})
            filters = {
                'jobTypes': preferences.get('jobTypes', []),
                'industries': preferences.get('industries', []),
                'roleLevels': preferences.get('roleLevels', []),
                'remoteOnly': preferences.get('remoteOnly', False)
            }
            expected_salary = preferences.get('expectedSalary', {})
            if expected_salary:
                filters['minSalary'] = expected_salary.get('min')
                filters['maxSalary'] = expected_salary.get('max')

        # Override with query parameters (filters from filter modal)
        if request.args.get('keywords'):
            filters['keywords'] = request.args.get('keywords')

        if request.args.get('city'):
            filters['city'] = request.args.get('city')

        if request.args.get('state'):
            filters['state'] = request.args.get('state')

        if request.args.get('country'):
            filters['country'] = request.args.get('country')

        if request.args.get('remote'):
            filters['remoteOnly'] = request.args.get('remote').lower() == 'true'

        if request.args.get('minSalary'):
            filters['minSalary'] = int(request.args.get('minSalary'))

        if request.args.get('maxSalary'):
            filters['maxSalary'] = int(request.args.get('maxSalary'))

        if request.args.get('jobTypes'):
            filters['jobTypes'] = request.args.get('jobTypes').split(',')

        if request.args.get('industries'):
            filters['industries'] = request.args.get('industries').split(',')

        if request.args.get('experienceLevels'):
            filters['experienceLevels'] = request.args.get('experienceLevels').split(',')

        if request.args.get('companySize'):
            filters['companySize'] = request.args.get('companySize').split(',')

        if request.args.get('datePosted'):
            filters['datePosted'] = request.args.get('datePosted')

        # Get match score threshold
        min_match_score = float(request.args.get('minMatchScore', 0.0))

        # Get jobs user has already swiped on
        swiped_job_ids = Swipe.get_swiped_job_ids(user_id)

        # Calculate pagination
        skip, limit = calculate_skip_limit(validated_page, validated_page_size)

        # Get jobs with filters
        jobs = Job.get_active_jobs(filters, skip=skip, limit=validated_page_size * 2)

        # Exclude already swiped jobs
        if swiped_job_ids:
            exclude_ids = [ObjectId(jid) if isinstance(jid, str) else jid for jid in swiped_job_ids]
            jobs = [job for job in jobs if job['_id'] not in exclude_ids]

        # Calculate match scores
        from utils.helpers import calculate_match_score
        preferences = user.get('preferences', {})

        jobs_with_scores = []
        for job in jobs:
            match_score = calculate_match_score(preferences, job)
            if match_score >= min_match_score:
                jobs_with_scores.append({
                    'job': job,
                    'matchScore': match_score
                })

        # Sort by match score
        jobs_with_scores.sort(key=lambda x: x['matchScore'], reverse=True)

        # Limit results
        jobs_with_scores = jobs_with_scores[:validated_page_size]

        # Serialize jobs
        result = []
        for item in jobs_with_scores:
            job_data = serialize_document(item['job'])
            job_data['matchScore'] = round(item['matchScore'], 2)
            result.append(job_data)

        # Get total count
        total_count = Job.get_total_count(filters)

        return jsonify({
            'jobs': result,
            'meta': {
                'page': validated_page,
                'pageSize': validated_page_size,
                'count': len(result),
                'totalCount': total_count,
                'filtersApplied': filters
            }
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/<job_id>', methods=['GET'])
@jwt_required()
def get_job_details(job_id):
    """
    Get detailed information about a specific job.

    Args:
        job_id: Job ID

    Returns:
        JSON response with job details
    """
    try:
        if not is_valid_object_id(job_id):
            return jsonify(format_error_response("Invalid job ID", 400))

        job = Job.find_by_id(job_id)

        if not job:
            return jsonify(format_error_response("Job not found", 404))

        job_data = serialize_document(job)

        # Calculate match score for this user
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)

        if user:
            from utils.helpers import calculate_match_score
            preferences = user.get('preferences', {})
            match_score = calculate_match_score(preferences, job)
            job_data['matchScore'] = round(match_score, 2)

        return jsonify({'job': job_data}), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/<job_id>/swipe', methods=['POST'])
@jwt_required()
def swipe_job(job_id):
    """
    Record a swipe action on a job.

    Args:
        job_id: Job ID

    Request body:
    {
        "action": "like",  // or "dislike", "superlike"
        "matchScore": 0.85  // optional
    }

    Returns:
        JSON response confirming swipe
    """
    try:
        user_id = get_jwt_identity()

        if not is_valid_object_id(job_id):
            return jsonify(format_error_response("Invalid job ID", 400))

        # Get request data
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify(format_error_response("Action not specified", 400))

        action = data['action']
        valid_actions = ['like', 'dislike', 'superlike']

        if action not in valid_actions:
            return jsonify(format_error_response(
                f"Invalid action. Must be one of: {', '.join(valid_actions)}",
                400
            ))

        # Check if job exists
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify(format_error_response("Job not found", 404))

        # Check if already swiped
        if Swipe.has_swiped(user_id, job_id):
            return jsonify(format_error_response("Already swiped on this job", 409))

        # Check swipe limit
        success, swipes_remaining = User.increment_swipes(user_id)

        if not success:
            return jsonify(format_error_response(
                "Swipe limit reached. Please upgrade your subscription.",
                429
            ))

        # Record swipe
        match_score = data.get('matchScore')
        Swipe.record_swipe(user_id, job_id, action, match_score)

        # NEW: Auto-apply for paid users on like/superlike
        if action in ['like', 'superlike']:
            user = User.find_by_id(user_id)
            subscription = user.get('subscription', {})
            plan = subscription.get('plan', 'free')

            # Check if user is on paid plan
            if plan == 'paid':
                # Trigger auto-apply workflow
                from services.auto_apply_service import AutoApplyService

                auto_apply = AutoApplyService()
                apply_result = auto_apply.apply_to_job_automatically(
                    user_id=user_id,
                    job_id=job_id,
                    job_data=job,
                    user_profile=user
                )

                if apply_result['success']:
                    return jsonify({
                        'message': 'Job liked and application submitted automatically!',
                        'swipesRemaining': swipes_remaining,
                        'action': action,
                        'jobId': job_id,
                        'autoApplied': True,
                        'applicationId': apply_result.get('applicationId'),
                        'coverLetterGenerated': apply_result.get('coverLetterGenerated', False),
                        'resumeCustomized': apply_result.get('resumeCustomized', False)
                    }), 200
                else:
                    # Auto-apply failed, but swipe was still recorded
                    return jsonify({
                        'message': f'Job {action}d successfully (auto-apply failed)',
                        'swipesRemaining': swipes_remaining,
                        'action': action,
                        'jobId': job_id,
                        'autoApplied': False,
                        'autoApplyError': apply_result.get('error')
                    }), 200

        # Free users or dislike action
        return jsonify({
            'message': f'Job {action}d successfully',
            'swipesRemaining': swipes_remaining,
            'action': action,
            'jobId': job_id,
            'autoApplied': False
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/liked', methods=['GET'])
@jwt_required()
def get_liked_jobs():
    """
    Get jobs that user has liked.

    Query parameters:
    - page: Page number (default: 1)
    - pageSize: Items per page (default: 20)

    Returns:
        JSON response with liked jobs
    """
    try:
        user_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)

        is_valid, (validated_page, validated_page_size), error = validate_pagination_params(
            page, page_size
        )

        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Calculate pagination
        skip, limit = calculate_skip_limit(validated_page, validated_page_size)

        # Get liked job IDs
        liked_job_ids = Swipe.get_liked_jobs(user_id, skip, limit)

        # Get job details
        from config.database import get_jobs_collection
        jobs_collection = get_jobs_collection()

        jobs = list(jobs_collection.find({'_id': {'$in': liked_job_ids}}))
        jobs_data = serialize_documents(jobs)

        # Get total count
        total_count = Swipe.get_swipe_count(user_id, action='like')

        return jsonify({
            'jobs': jobs_data,
            'meta': get_pagination_metadata(total_count, validated_page, validated_page_size)
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/history', methods=['GET'])
@jwt_required()
def get_swipe_history():
    """
    Get user's swipe history.

    Query parameters:
    - page: Page number (default: 1)
    - pageSize: Items per page (default: 20)
    - action: Filter by action (like, dislike, superlike)

    Returns:
        JSON response with swipe history
    """
    try:
        user_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        action = request.args.get('action')

        is_valid, (validated_page, validated_page_size), error = validate_pagination_params(
            page, page_size
        )

        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Calculate pagination
        skip, limit = calculate_skip_limit(validated_page, validated_page_size)

        # Get swipe history
        swipes = Swipe.get_user_swipes(user_id, action, skip, limit)

        # Get job details for each swipe
        from config.database import get_jobs_collection
        jobs_collection = get_jobs_collection()

        result = []
        for swipe in swipes:
            job = jobs_collection.find_one({'_id': swipe['jobId']})
            if job:
                swipe_data = serialize_document(swipe)
                swipe_data['job'] = serialize_document(job)
                result.append(swipe_data)

        # Get total count
        total_count = Swipe.get_swipe_count(user_id, action)

        return jsonify({
            'swipes': result,
            'meta': get_pagination_metadata(total_count, validated_page, validated_page_size)
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/<job_id>/apply', methods=['POST'])
@jwt_required()
def apply_to_job(job_id):
    """
    Apply to a job.

    Args:
        job_id: Job ID

    Request body:
    {
        "coverLetter": "Dear hiring manager...",
        "additionalNotes": "Optional notes"
    }

    Returns:
        JSON response confirming application
    """
    try:
        user_id = get_jwt_identity()

        if not is_valid_object_id(job_id):
            return jsonify(format_error_response("Invalid job ID", 400))

        # Check if job exists
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify(format_error_response("Job not found", 404))

        # Check if already applied
        existing_apps = Application.get_user_applications(user_id)
        job_obj_id = ObjectId(job_id)

        for app in existing_apps:
            if app['jobId'] == job_obj_id:
                return jsonify(format_error_response("Already applied to this job", 409))

        # Get application data
        data = request.get_json() or {}

        # Create application
        app_id = Application.create_application(user_id, job_id, data)

        return jsonify({
            'message': 'Application submitted successfully',
            'applicationId': str(app_id)
        }), 201

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    """
    Get user's job applications with filtering support (History Tab).

    Query parameters:
    - status: Filter by status (applied, interviewed, rejected, hired)
    - page: Page number (default: 1)
    - pageSize: Items per page (default: 20)
    - keywords: Search in job title or company name
    - city: Filter by city
    - state: Filter by state
    - jobTypes: Filter by job types (comma-separated)
    - industries: Filter by industries (comma-separated)
    - dateFrom: Applications from date (ISO format)
    - dateTo: Applications to date (ISO format)
    - sortBy: Sort field (appliedAt, company, title, status)
    - sortOrder: Sort order (asc, desc, default: desc)

    Returns:
        JSON response with filtered applications
    """
    try:
        user_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)

        is_valid, (validated_page, validated_page_size), error = validate_pagination_params(
            page, page_size
        )

        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Get all user applications (we'll filter manually)
        applications = Application.get_user_applications(user_id, status=None, skip=0, limit=1000)

        # Enrich with job details and apply filters
        from config.database import get_jobs_collection
        jobs_collection = get_jobs_collection()

        # Build filters from query parameters
        status_filter = request.args.get('status')
        keywords = request.args.get('keywords', '').lower()
        city_filter = request.args.get('city', '').lower()
        state_filter = request.args.get('state', '')
        job_types = request.args.get('jobTypes', '').split(',') if request.args.get('jobTypes') else []
        industries = request.args.get('industries', '').split(',') if request.args.get('industries') else []
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')

        filtered_apps = []
        for app in applications:
            # Status filter
            if status_filter and app.get('status') != status_filter:
                continue

            # Date range filter
            if date_from:
                try:
                    from datetime import datetime
                    app_date = app.get('appliedAt')
                    if app_date < datetime.fromisoformat(date_from.replace('Z', '+00:00')):
                        continue
                except:
                    pass

            if date_to:
                try:
                    from datetime import datetime
                    app_date = app.get('appliedAt')
                    if app_date > datetime.fromisoformat(date_to.replace('Z', '+00:00')):
                        continue
                except:
                    pass

            # Get job details
            job = jobs_collection.find_one({'_id': app['jobId']})
            if not job:
                continue

            # Keywords filter (job title or company name)
            if keywords:
                title = job.get('title', '').lower()
                company = job.get('company', {}).get('name', '').lower()
                if keywords not in title and keywords not in company:
                    continue

            # City filter
            if city_filter:
                job_city = job.get('location', {}).get('city', '').lower()
                if city_filter not in job_city:
                    continue

            # State filter
            if state_filter:
                job_state = job.get('location', {}).get('state', '')
                if state_filter != job_state:
                    continue

            # Job types filter
            if job_types and job_types[0]:  # Check if not empty list
                job_type = job.get('employment', {}).get('type', '')
                if job_type not in job_types:
                    continue

            # Industries filter
            if industries and industries[0]:  # Check if not empty list
                job_industry = job.get('company', {}).get('industry', '')
                if job_industry not in industries:
                    continue

            # Passed all filters - add to results
            app_data = serialize_document(app)
            app_data['job'] = serialize_document(job)
            filtered_apps.append(app_data)

        # Sort applications
        sort_by = request.args.get('sortBy', 'appliedAt')
        sort_order = request.args.get('sortOrder', 'desc')

        if sort_by == 'appliedAt':
            filtered_apps.sort(key=lambda x: x.get('appliedAt', ''), reverse=(sort_order == 'desc'))
        elif sort_by == 'company':
            filtered_apps.sort(key=lambda x: x.get('job', {}).get('company', {}).get('name', ''), reverse=(sort_order == 'desc'))
        elif sort_by == 'title':
            filtered_apps.sort(key=lambda x: x.get('job', {}).get('title', ''), reverse=(sort_order == 'desc'))
        elif sort_by == 'status':
            filtered_apps.sort(key=lambda x: x.get('status', ''), reverse=(sort_order == 'desc'))

        # Apply pagination
        total_count = len(filtered_apps)
        skip, limit = calculate_skip_limit(validated_page, validated_page_size)
        paginated_apps = filtered_apps[skip:skip+limit]

        return jsonify({
            'applications': paginated_apps,
            'meta': get_pagination_metadata(total_count, validated_page, validated_page_size)
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/search', methods=['GET'])
@jwt_required()
def search_jobs():
    """
    Search jobs by keyword.

    Query parameters:
    - q: Search query
    - limit: Maximum results (default: 20)

    Returns:
        JSON response with search results
    """
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)

        if not query:
            return jsonify(format_error_response("Search query required", 400))

        # Search jobs
        jobs = Job.search_jobs(query, min(limit, 100))
        jobs_data = serialize_documents(jobs)

        return jsonify({
            'jobs': jobs_data,
            'meta': {
                'query': query,
                'count': len(jobs_data)
            }
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/sources', methods=['GET'])
def get_job_sources():
    """
    Get available job sources/APIs.

    Returns:
        JSON response with available job sources and their status
    """
    try:
        from services.job_aggregation import JobAggregationService

        job_service = JobAggregationService()
        available_sources = job_service.get_available_sources()

        # Define all possible sources with metadata
        all_sources = {
            'jsearch': {
                'id': 'jsearch',
                'name': 'JSearch',
                'description': 'Google for Jobs aggregator',
                'icon': 'https://rapidapi.com/favicon.ico',
                'enabled': 'jsearch' in available_sources
            },
            'careerjet': {
                'id': 'careerjet',
                'name': 'Careerjet',
                'description': 'International job search engine',
                'icon': 'https://www.careerjet.com/favicon.ico',
                'enabled': 'careerjet' in available_sources
            },
            'jobs_search': {
                'id': 'jobs_search',
                'name': 'Jobs Search API',
                'description': 'LinkedIn, Indeed, ZipRecruiter aggregator',
                'icon': 'https://rapidapi.com/favicon.ico',
                'enabled': 'jobs_search' in available_sources
            },
            'linkedin': {
                'id': 'linkedin',
                'name': 'LinkedIn Jobs',
                'description': 'Direct LinkedIn job listings',
                'icon': 'https://static.licdn.com/sc/h/eahiplrwoq61f4uan012ia17i',
                'enabled': 'linkedin' in available_sources
            },
            'indeed': {
                'id': 'indeed',
                'name': 'Indeed Jobs',
                'description': 'Direct Indeed job listings',
                'icon': 'https://www.indeed.com/favicon.ico',
                'enabled': 'indeed' in available_sources
            }
        }

        # Get cache stats if available
        cache_stats = job_service.get_cache_stats()

        return jsonify({
            'sources': list(all_sources.values()),
            'totalSources': len(all_sources),
            'enabledSources': len(available_sources),
            'caching': cache_stats
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/filters', methods=['GET'])
def get_job_filters():
    """
    Get available filter options for job search.

    Returns:
        JSON response with filter options (job types, industries, etc.)
    """
    try:
        # Return standardized filter options
        filters = {
            'jobTypes': [
                'FULLTIME',
                'PARTTIME',
                'CONTRACT',
                'CONTRACTOR',
                'INTERN',
                'TEMPORARY'
            ],
            'experienceLevels': [
                'Internship',
                'Entry Level',
                'Mid Level',
                'Senior',
                'Lead',
                'Executive'
            ],
            'industries': [
                'Technology',
                'Healthcare',
                'Finance',
                'Education',
                'Marketing',
                'Sales',
                'Engineering',
                'Design',
                'Human Resources',
                'Customer Service',
                'Operations',
                'Legal',
                'Consulting',
                'Real Estate',
                'Retail',
                'Manufacturing',
                'Transportation',
                'Hospitality',
                'Media',
                'Non-Profit',
                'Government',
                'Other'
            ],
            'companySizes': [
                '1-10',
                '11-50',
                '51-200',
                '201-500',
                '501-1000',
                '1001-5000',
                '5001+'
            ],
            'datePosted': [
                {'value': 'all', 'label': 'All time'},
                {'value': 'today', 'label': 'Past 24 hours'},
                {'value': '3days', 'label': 'Past 3 days'},
                {'value': 'week', 'label': 'Past week'},
                {'value': 'month', 'label': 'Past month'}
            ],
            'salaryRanges': [
                {'min': 0, 'max': 30000, 'label': 'Under $30k'},
                {'min': 30000, 'max': 50000, 'label': '$30k - $50k'},
                {'min': 50000, 'max': 75000, 'label': '$50k - $75k'},
                {'min': 75000, 'max': 100000, 'label': '$75k - $100k'},
                {'min': 100000, 'max': 150000, 'label': '$100k - $150k'},
                {'min': 150000, 'max': 200000, 'label': '$150k - $200k'},
                {'min': 200000, 'max': None, 'label': '$200k+'}
            ],
            'remoteOptions': [
                {'value': False, 'label': 'On-site'},
                {'value': True, 'label': 'Remote only'}
            ]
        }

        return jsonify(filters), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_job_statistics():
    """
    Get job statistics and analytics.

    Returns:
        JSON response with job statistics
    """
    try:
        user_id = get_jwt_identity()

        # Get total jobs count
        total_jobs = Job.get_total_count({})

        # Get active jobs count
        active_jobs = Job.get_total_count({'isActive': True})

        # Get user's swipe statistics
        swipe_stats = Swipe.get_statistics(user_id)

        # Get user's application statistics
        applications = Application.get_user_applications(user_id)
        app_stats = {
            'total': len(applications),
            'applied': len([a for a in applications if a.get('status') == 'applied']),
            'interviewed': len([a for a in applications if a.get('status') == 'interviewed']),
            'rejected': len([a for a in applications if a.get('status') == 'rejected']),
            'hired': len([a for a in applications if a.get('status') == 'hired'])
        }

        # Get top industries from database
        from config.database import get_jobs_collection
        jobs_collection = get_jobs_collection()

        pipeline = [
            {'$match': {'isActive': True}},
            {'$group': {
                '_id': '$company.industry',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]

        top_industries = list(jobs_collection.aggregate(pipeline))

        # Get top locations
        pipeline = [
            {'$match': {'isActive': True}},
            {'$group': {
                '_id': {
                    'city': '$location.city',
                    'state': '$location.state'
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]

        top_locations = list(jobs_collection.aggregate(pipeline))

        return jsonify({
            'jobStatistics': {
                'totalJobs': total_jobs,
                'activeJobs': active_jobs,
                'topIndustries': [
                    {
                        'industry': item['_id'],
                        'count': item['count']
                    } for item in top_industries if item['_id']
                ],
                'topLocations': [
                    {
                        'city': item['_id'].get('city'),
                        'state': item['_id'].get('state'),
                        'count': item['count']
                    } for item in top_locations
                ]
            },
            'swipeStatistics': swipe_stats,
            'applicationStatistics': app_stats
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@jobs_bp.route('/fetch', methods=['POST'])
@jwt_required()
def fetch_jobs():
    """
    Fetch jobs from external APIs and save to database.

    Request body:
    {
        "query": "Python developer",
        "location": "New York, NY",
        "filters": {
            "remote": true,
            "date_posted": "week",
            "employment_types": ["FULLTIME"]
        },
        "sources": ["jsearch", "linkedin", "indeed"],  // Optional, defaults to all
        "limit": 20,
        "saveToDb": true  // Whether to save fetched jobs to database (default: true)
    }

    Returns:
        JSON response with fetched jobs
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("Request body required", 400))

        query = data.get('query')
        if not query:
            return jsonify(format_error_response("Query parameter required", 400))

        location = data.get('location')
        filters = data.get('filters', {})
        sources = data.get('sources')  # None = use all sources
        limit = data.get('limit', 20)
        save_to_db = data.get('saveToDb', True)

        # Import job aggregation service
        from services.job_aggregation import JobAggregationService

        job_service = JobAggregationService()

        # Fetch jobs from external APIs
        jobs = job_service.search_jobs(
            query=query,
            location=location,
            filters=filters,
            sources=sources,
            limit=limit,
            use_cache=True
        )

        # Save to database if requested
        saved_count = 0
        if save_to_db and jobs:
            from config.database import get_jobs_collection
            from datetime import datetime

            jobs_collection = get_jobs_collection()

            for job in jobs:
                try:
                    # Check if job already exists (by externalId and source)
                    external_id = job.get('externalId')
                    source = job.get('source')

                    if external_id and source:
                        existing = jobs_collection.find_one({
                            'externalId': external_id,
                            'source': source
                        })

                        if not existing:
                            # Add timestamps
                            job['createdAt'] = datetime.utcnow()
                            job['updatedAt'] = datetime.utcnow()

                            # Insert job
                            jobs_collection.insert_one(job)
                            saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving job to database: {str(e)}")
                    continue

        # Serialize jobs for response
        jobs_data = []
        for job in jobs:
            job_copy = job.copy()
            # Convert ObjectId to string if present
            if '_id' in job_copy:
                job_copy['_id'] = str(job_copy['_id'])
            # Convert datetime to ISO string
            if 'postedAt' in job_copy and hasattr(job_copy['postedAt'], 'isoformat'):
                job_copy['postedAt'] = job_copy['postedAt'].isoformat()
            if 'createdAt' in job_copy and hasattr(job_copy['createdAt'], 'isoformat'):
                job_copy['createdAt'] = job_copy['createdAt'].isoformat()
            if 'updatedAt' in job_copy and hasattr(job_copy['updatedAt'], 'isoformat'):
                job_copy['updatedAt'] = job_copy['updatedAt'].isoformat()
            jobs_data.append(job_copy)

        return jsonify({
            'jobs': jobs_data,
            'meta': {
                'query': query,
                'location': location,
                'filters': filters,
                'sources': sources or job_service.get_available_sources(),
                'count': len(jobs),
                'savedToDb': save_to_db,
                'savedCount': saved_count
            }
        }), 200

    except Exception as e:
        import traceback
        logger.error(f"Error fetching jobs: {str(e)}\n{traceback.format_exc()}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
