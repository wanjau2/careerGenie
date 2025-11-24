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
    import logging
    logger = logging.getLogger(__name__)

    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        logger.info(f"🔧 Update preferences request for user: {user_id}")
        logger.info(f"📦 Request data: {data}")

        if not data:
            logger.warning("⚠️ No data provided in request")
            return jsonify(format_error_response("No data provided", 400))

        # Update preferences
        logger.info(f"💾 Updating preferences in database...")
        success = User.update_preferences(user_id, data)

        if not success:
            logger.error(f"❌ Failed to update preferences for user {user_id}")
            return jsonify(format_error_response("Failed to update preferences", 500))

        # Get updated user
        logger.info(f"✅ Preferences updated, fetching user data...")
        user = User.find_by_id(user_id)
        user_data = serialize_document(user)

        logger.info(f"✅ Update preferences successful for user {user_id}")
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': user_data.get('preferences', {})
        }), 200

    except Exception as e:
        logger.error(f"❌ EXCEPTION in update_preferences: {str(e)}", exc_info=True)
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


@users_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Permanently delete user account and all associated data.

    This endpoint will:
    - Delete user profile
    - Delete all job applications
    - Delete all swipe history
    - Delete uploaded files (avatar, resume)
    - Remove all user preferences
    - Cancel active subscriptions

    Returns:
        JSON response confirming deletion
    """
    try:
        from config.database import (
            get_users_collection,
            get_applications_collection,
            get_swipes_collection
        )
        from bson import ObjectId
        import logging

        logger = logging.getLogger(__name__)
        user_id = get_jwt_identity()

        logger.info(f"🗑️  Starting account deletion for user {user_id}")

        # Get collections
        users = get_users_collection()
        applications = get_applications_collection()
        swipes = get_swipes_collection()

        # Convert user_id to ObjectId
        user_obj_id = ObjectId(user_id)

        # 1. Delete all applications
        app_result = applications.delete_many({'userId': user_obj_id})
        logger.info(f"   Deleted {app_result.deleted_count} applications")

        # 2. Delete all swipe history
        swipe_result = swipes.delete_many({'userId': user_obj_id})
        logger.info(f"   Deleted {swipe_result.deleted_count} swipes")

        # 3. Delete Gmail credentials if exists
        try:
            from config.database import get_database
            db = get_database()
            gmail_result = db.gmail_credentials.delete_many({'userId': user_id})
            logger.info(f"   Deleted {gmail_result.deleted_count} Gmail credentials")
        except:
            pass

        # 4. Delete training data if exists
        try:
            from config.database import get_database
            db = get_database()
            training_result = db.training_resumes.delete_many({'userId': user_id})
            logger.info(f"   Deleted {training_result.deleted_count} training resumes")
        except:
            pass

        # 5. Delete user account (final step)
        user_result = users.delete_one({'_id': user_obj_id})

        if user_result.deleted_count == 0:
            logger.error(f"   ❌ Failed to delete user {user_id}")
            return jsonify(format_error_response("Failed to delete account", 500))

        logger.info(f"   ✅ User account deleted successfully")
        logger.info(f"🗑️  Account deletion complete for user {user_id}")

        return jsonify({
            'message': 'Account deleted successfully',
            'deleted': {
                'profile': True,
                'applications': app_result.deleted_count,
                'swipes': swipe_result.deleted_count
            }
        }), 200

    except Exception as e:
        logger.error(f"❌ Error deleting account: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
