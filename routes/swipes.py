"""Swipe tracking and management routes."""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models.job import Job
from models.swipe import Swipe
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
swipes_bp = Blueprint('swipes', __name__, url_prefix='/api/swipes')


@swipes_bp.route('/', methods=['POST'])
@jwt_required()
def record_swipe():
    """
    Record a swipe action on a job.

    Request body:
    {
        "jobId": "job_id_here",
        "action": "like",  // or "dislike", "superlike"
        "matchScore": 0.85  // optional
    }

    Returns:
        JSON response confirming swipe
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("No data provided", 400))

        job_id = data.get('jobId')
        action = data.get('action')

        if not job_id:
            return jsonify(format_error_response("Job ID is required", 400))

        if not action:
            return jsonify(format_error_response("Action not specified", 400))

        if not is_valid_object_id(job_id):
            return jsonify(format_error_response("Invalid job ID", 400))

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

        # Auto-apply for paid users on like/superlike
        auto_applied = False
        application_id = None

        if action in ['like', 'superlike']:
            user = User.find_by_id(user_id)
            subscription = user.get('subscription', {})
            plan = subscription.get('plan', 'free')

            if plan == 'paid':
                # Trigger auto-apply workflow
                try:
                    from services.auto_apply_service import AutoApplyService
                    auto_apply = AutoApplyService()
                    apply_result = auto_apply.apply_to_job_automatically(
                        user_id=user_id,
                        job_id=job_id,
                        job_data=job,
                        user_profile=user
                    )

                    if apply_result['success']:
                        auto_applied = True
                        application_id = apply_result.get('applicationId')
                except Exception as e:
                    logger.warning(f"Auto-apply failed: {str(e)}")

        return jsonify({
            'message': f'Job {action}d successfully',
            'swipesRemaining': swipes_remaining,
            'action': action,
            'jobId': job_id,
            'autoApplied': auto_applied,
            'applicationId': application_id
        }), 200

    except Exception as e:
        logger.error(f"Error recording swipe: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@swipes_bp.route('/liked', methods=['GET'])
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
        logger.error(f"Error getting liked jobs: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@swipes_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_swipe_statistics():
    """
    Get swipe statistics for the current user.

    Returns:
        JSON response with swipe statistics
    """
    try:
        user_id = get_jwt_identity()

        # Get statistics from Swipe model
        stats = Swipe.get_statistics(user_id)

        # Get user subscription info
        user = User.find_by_id(user_id)
        if user:
            subscription = user.get('subscription', {})
            stats['subscription'] = {
                'plan': subscription.get('plan', 'free'),
                'swipesUsed': subscription.get('swipesUsed', 0),
                'swipeLimit': subscription.get('swipeLimit', 0),
                'swipesRemaining': max(0, subscription.get('swipeLimit', 0) - subscription.get('swipesUsed', 0)),
                'resetDate': subscription.get('resetDate')
            }

        return jsonify({
            'statistics': stats
        }), 200

    except Exception as e:
        logger.error(f"Error getting swipe statistics: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@swipes_bp.route('/history', methods=['GET'])
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
                swipe_data['jobData'] = serialize_document(job)
                # Frontend expects 'swipedAt' not 'timestamp'
                if 'timestamp' in swipe_data:
                    swipe_data['swipedAt'] = swipe_data['timestamp']
                result.append(swipe_data)

        # Get total count
        total_count = Swipe.get_swipe_count(user_id, action)

        return jsonify({
            'swipes': result,
            'meta': get_pagination_metadata(total_count, validated_page, validated_page_size)
        }), 200

    except Exception as e:
        logger.error(f"Error getting swipe history: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@swipes_bp.route('/undo', methods=['POST'])
@jwt_required()
def undo_last_swipe():
    """
    Undo the last swipe action.

    Returns:
        JSON response confirming undo
    """
    try:
        user_id = get_jwt_identity()

        # Get last swipe
        swipes = Swipe.get_user_swipes(user_id, action=None, skip=0, limit=1)

        if not swipes:
            return jsonify(format_error_response("No swipes to undo", 404))

        last_swipe = swipes[0]

        # Delete the swipe
        from config.database import get_swipes_collection
        swipes_collection = get_swipes_collection()

        result = swipes_collection.delete_one({'_id': last_swipe['_id']})

        if result.deleted_count == 0:
            return jsonify(format_error_response("Failed to undo swipe", 500))

        # Decrement swipe count
        User.decrement_swipes(user_id)

        return jsonify({
            'message': 'Swipe undone successfully',
            'undoneSwipe': serialize_document(last_swipe)
        }), 200

    except Exception as e:
        logger.error(f"Error undoing swipe: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
