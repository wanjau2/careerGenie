"""Subscription and swipe tracking routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from utils.helpers import format_success_response, format_error_response
import logging

logger = logging.getLogger(__name__)

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/track-swipe', methods=['POST'])
@jwt_required()
def track_swipe():
    """
    Track a user swipe and update swipe count.

    For free users: Increments swipe count (max 50/day)
    For paid users: Unlimited swipes

    Returns:
        JSON response with swipe status
    """
    try:
        user_id = get_jwt_identity()

        # Increment swipe count
        success, swipes_remaining = User.increment_swipes(user_id)

        if not success:
            return jsonify(format_error_response(
                'Swipe limit reached. Upgrade to premium for unlimited swipes.',
                403
            )), 403

        # Get updated swipe status
        swipe_status = User.get_swipe_status(user_id)

        return jsonify(format_success_response(
            data=swipe_status,
            message='Swipe tracked successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error tracking swipe: {str(e)}")
        return jsonify(format_error_response(
            'Failed to track swipe',
            500
        )), 500


@subscription_bp.route('/status', methods=['GET'])
@jwt_required()
def get_subscription_status():
    """
    Get user's subscription status and swipe limits.

    Returns:
        JSON response with subscription details
    """
    try:
        user_id = get_jwt_identity()

        # Get user data
        user = User.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response('User not found', 404)), 404

        subscription = user.get('subscription', {})
        swipe_status = User.get_swipe_status(user_id)

        # Combine subscription and swipe info
        status = {
            'plan': subscription.get('plan', 'free'),
            'isPremium': subscription.get('plan') == 'paid',
            'swipesUsed': swipe_status.get('swipesUsed', 0),
            'swipeLimit': swipe_status.get('swipeLimit', 50),
            'swipesRemaining': swipe_status.get('swipesRemaining', 0),
            'resetDate': swipe_status.get('resetDate'),
            'subscriptionEnd': subscription.get('subscriptionEnd'),
        }

        return jsonify(format_success_response(
            data=status,
            message='Subscription status retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return jsonify(format_error_response(
            'Failed to get subscription status',
            500
        )), 500


@subscription_bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_subscription():
    """
    Upgrade user to paid subscription.

    Request body:
        - plan: 'paid' (only option for now)
        - paymentMethod: 'mpesa', 'card', etc.
        - paymentReference: Payment transaction ID

    Returns:
        JSON response with upgrade status
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        plan = data.get('plan', 'paid')

        if plan not in ['paid', 'free']:
            return jsonify(format_error_response(
                'Invalid plan. Choose "paid" or "free"',
                400
            )), 400

        # Upgrade subscription
        success = User.upgrade_subscription(user_id, plan)

        if not success:
            return jsonify(format_error_response(
                'Failed to upgrade subscription',
                500
            )), 500

        return jsonify(format_success_response(
            data={'plan': plan, 'isPremium': plan == 'paid'},
            message='Subscription upgraded successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        return jsonify(format_error_response(
            'Failed to upgrade subscription',
            500
        )), 500


@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """
    Cancel paid subscription and revert to free tier.

    Returns:
        JSON response with cancellation status
    """
    try:
        user_id = get_jwt_identity()

        # Downgrade to free
        success = User.upgrade_subscription(user_id, 'free')

        if not success:
            return jsonify(format_error_response(
                'Failed to cancel subscription',
                500
            )), 500

        return jsonify(format_success_response(
            data={'plan': 'free', 'isPremium': False},
            message='Subscription cancelled successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        return jsonify(format_error_response(
            'Failed to cancel subscription',
            500
        )), 500


@subscription_bp.route('/pricing', methods=['GET'])
def get_pricing():
    """
    Get subscription pricing information.

    Returns:
        JSON response with pricing details
    """
    try:
        pricing = {
            'plans': [
                {
                    'id': 'free',
                    'name': 'Free',
                    'price': 0,
                    'currency': 'USD',
                    'interval': 'month',
                    'features': [
                        '50 job swipes per day',
                        'Manual job applications',
                        'Basic job matching',
                        'Course recommendations'
                    ]
                },
                {
                    'id': 'paid',
                    'name': 'Premium',
                    'price': 8.99,
                    'currency': 'USD',
                    'interval': 'month',
                    'features': [
                        'Unlimited job swipes',
                        'Auto-apply to matched jobs',
                        'Advanced job matching',
                        'Priority support',
                        'Resume optimization',
                        'Course recommendations'
                    ]
                }
            ]
        }

        return jsonify(format_success_response(
            data=pricing,
            message='Pricing retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error getting pricing: {str(e)}")
        return jsonify(format_error_response(
            'Failed to get pricing',
            500
        )), 500
