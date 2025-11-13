"""User profile management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from utils.helpers import format_error_response, serialize_document
from utils.validators import validate_user_profile_data

users_bp = Blueprint('users', __name__, url_prefix='/api/user')


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get user profile.

    Returns:
        JSON response with user profile data
    """
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)

        if not user:
            return jsonify(format_error_response("User not found", 404))

        user_data = serialize_document(user)

        # Remove sensitive data
        if 'password_hash' in user_data:
            del user_data['password_hash']

        return jsonify({'user': user_data}), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile.

    Request body:
    {
        "firstName": "John",
        "lastName": "Doe",
        "phone": "+1234567890",
        "location": {
            "city": "San Francisco",
            "state": "CA",
            "coordinates": [37.7749, -122.4194]
        },
        "skills": ["Python", "React", "Node.js"],
        "experience": "2-5 years",
        "expectedSalary": {
            "min": 80000,
            "max": 120000
        }
    }

    Returns:
        JSON response with updated user data
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("No data provided", 400))

        # Validate profile data
        is_valid, error = validate_user_profile_data(data)
        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Update profile
        success = User.update_profile(user_id, data)

        if not success:
            return jsonify(format_error_response("Failed to update profile", 500))

        # Get updated user
        user = User.find_by_id(user_id)
        user_data = serialize_document(user)

        # Remove sensitive data
        if 'password_hash' in user_data:
            del user_data['password_hash']

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user_data
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@users_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """
    Update user job preferences.

    Request body:
    {
        "jobTypes": ["Full-time", "Remote"],
        "industries": ["Technology", "Finance"],
        "roleLevels": ["Mid-level", "Senior"],
        "remoteOnly": false
    }

    Returns:
        JSON response with updated preferences
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("No data provided", 400))

        # Update preferences
        success = User.update_preferences(user_id, data)

        if not success:
            return jsonify(format_error_response("Failed to update preferences", 500))

        # Get updated user
        user = User.find_by_id(user_id)
        user_data = serialize_document(user)

        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': user_data.get('preferences', {})
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@users_bp.route('/subscription/status', methods=['GET'])
@jwt_required()
def get_subscription_status():
    """
    Get user subscription and swipe status.

    Returns:
        JSON response with subscription details
    """
    try:
        user_id = get_jwt_identity()
        swipe_status = User.get_swipe_status(user_id)

        if not swipe_status:
            return jsonify(format_error_response("User not found", 404))

        return jsonify({'subscription': swipe_status}), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@users_bp.route('/subscription/upgrade', methods=['POST'])
@jwt_required()
def upgrade_subscription():
    """
    Upgrade user subscription plan.

    2-Tier System:
    - Free: 50 swipes/day
    - Paid: Unlimited swipes + auto-apply ($8.99/month)

    Request body:
    {
        "plan": "paid"  // or "free" to downgrade
    }

    Returns:
        JSON response confirming upgrade
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'plan' not in data:
            return jsonify(format_error_response("Plan not specified", 400))

        plan = data['plan']
        valid_plans = ['free', 'paid']

        if plan not in valid_plans:
            return jsonify(format_error_response(
                f"Invalid plan. Must be one of: {', '.join(valid_plans)}. Paid plan is $8.99/month.",
                400
            ))

        # Update subscription
        success = User.upgrade_subscription(user_id, plan)

        if not success:
            return jsonify(format_error_response("Failed to update subscription", 500))

        # Get updated swipe status
        swipe_status = User.get_swipe_status(user_id)

        # Add pricing info
        pricing_info = {
            'free': {'price': 0, 'features': ['50 swipes/day', 'Manual apply']},
            'paid': {
                'price': 8.99,
                'features': [
                    'Unlimited swipes',
                    'Auto-apply on swipe right',
                    'AI-generated cover letters',
                    'Resume customization'
                ]
            }
        }

        return jsonify({
            'message': f'Subscription {"upgraded" if plan == "paid" else "changed"} to {plan} successfully',
            'subscription': swipe_status,
            'planDetails': pricing_info[plan]
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@users_bp.route('/account', methods=['DELETE'])
@jwt_required()
def deactivate_account():
    """
    Deactivate user account.

    Returns:
        JSON response confirming deactivation
    """
    try:
        from config.database import get_users_collection
        from bson import ObjectId

        user_id = get_jwt_identity()
        users = get_users_collection()

        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'isActive': False}}
        )

        if result.modified_count == 0:
            return jsonify(format_error_response("Failed to deactivate account", 500))

        return jsonify({'message': 'Account deactivated successfully'}), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
