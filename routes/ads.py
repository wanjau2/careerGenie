"""Ads configuration and tracking routes."""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

ads_bp = Blueprint('ads', __name__, url_prefix='/api/ads')


@ads_bp.route('/config', methods=['GET'])
def get_ads_config():
    """
    Get AdMob configuration for mobile app.

    Returns:
        JSON response with AdMob unit IDs and settings
    """
    try:
        config = {
            'admob': {
                'appId': os.getenv('ADMOB_APP_ID'),
                'bannerAdUnitId': os.getenv('ADMOB_BANNER_ID'),
                'interstitialAdUnitId': os.getenv('ADMOB_INTERSTITIAL_ID'),
                'rewardedAdUnitId': os.getenv('ADMOB_REWARDED_ID'),
                'nativeAdUnitId': os.getenv('ADMOB_NATIVE_ID'),
                'testMode': os.getenv('ADMOB_TEST_MODE', 'false').lower() == 'true'
            },
            'adSettings': {
                'showBannerAds': True,
                'showInterstitialAds': True,
                'showRewardedAds': True,
                'showNativeAds': True,
                'interstitialAdFrequency': 3,  # Show after every 3 job swipes
                'bannerAdPosition': 'bottom',
                'rewardedAdReward': 10,  # Extra swipes for watching ad
                'enableAdPersonalization': True,
                'minimumSwipesBeforeAds': 5  # Don't show ads until 5 swipes
            },
            'adPlacements': {
                'jobListing': {
                    'showBanner': True,
                    'showNative': True,
                    'nativeAdFrequency': 5  # Show native ad every 5 jobs
                },
                'swipeResult': {
                    'showInterstitial': True,
                    'frequency': 3
                },
                'noMoreSwipes': {
                    'showRewarded': True,
                    'reward': 10
                }
            }
        }

        return jsonify(config), 200

    except Exception as e:
        logger.error(f"Error getting ads config: {str(e)}")
        return jsonify({'error': 'Failed to get ads configuration'}), 500


@ads_bp.route('/track', methods=['POST'])
def track_ad_event():
    """
    Track ad impression/click for analytics.

    Request body:
    {
        "adType": "banner|interstitial|rewarded|native",
        "adUnitId": "...",
        "action": "impression|click|closed|rewarded",
        "userId": "...",
        "timestamp": "...",
        "platform": "android|ios"
    }

    Returns:
        JSON response confirming tracking
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Create ad event
        ad_event = {
            'adType': data.get('adType'),
            'adUnitId': data.get('adUnitId'),
            'action': data.get('action'),
            'userId': data.get('userId'),
            'timestamp': datetime.utcnow(),
            'platform': data.get('platform', 'unknown'),
            'appVersion': data.get('appVersion'),
            'deviceModel': data.get('deviceModel')
        }

        # Optional: Store in database for analytics
        # from config.database import get_database
        # db = get_database()
        # db.ad_events.insert_one(ad_event)

        # Log for now
        logger.info(f"Ad event: {ad_event['action']} - {ad_event['adType']} - User: {ad_event['userId']}")

        # If rewarded ad was completed, could trigger reward logic here
        if ad_event['action'] == 'rewarded' and ad_event['adType'] == 'rewarded':
            # TODO: Grant user extra swipes
            pass

        return jsonify({
            'message': 'Ad event tracked successfully',
            'success': True,
            'eventId': str(datetime.utcnow().timestamp())
        }), 200

    except Exception as e:
        logger.error(f"Error tracking ad event: {str(e)}")
        return jsonify({'error': 'Failed to track ad event'}), 500


@ads_bp.route('/reward', methods=['POST'])
def grant_ad_reward():
    """
    Grant reward for watching rewarded ad.

    Request body:
    {
        "userId": "...",
        "rewardType": "swipes",
        "rewardAmount": 10
    }

    Returns:
        JSON response with updated user stats
    """
    try:
        # from flask_jwt_extended import jwt_required, get_jwt_identity
        # @jwt_required()  # Add JWT protection

        data = request.get_json()
        user_id = data.get('userId')
        reward_type = data.get('rewardType', 'swipes')
        reward_amount = data.get('rewardAmount', 10)

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        # TODO: Implement reward logic
        # from models.user import User
        # User.grant_extra_swipes(user_id, reward_amount)

        logger.info(f"Granted {reward_amount} {reward_type} to user {user_id}")

        return jsonify({
            'message': f'Reward granted: {reward_amount} {reward_type}',
            'success': True,
            'rewardType': reward_type,
            'rewardAmount': reward_amount
        }), 200

    except Exception as e:
        logger.error(f"Error granting reward: {str(e)}")
        return jsonify({'error': 'Failed to grant reward'}), 500


@ads_bp.route('/stats', methods=['GET'])
def get_ad_stats():
    """
    Get ad statistics (for admin/analytics).

    Query params:
    - period: today|week|month|all
    - userId: Optional user ID filter

    Returns:
        JSON response with ad statistics
    """
    try:
        period = request.args.get('period', 'today')
        user_id = request.args.get('userId')

        # Mock data - replace with real database queries
        stats = {
            'period': period,
            'impressions': {
                'banner': 1250,
                'interstitial': 180,
                'rewarded': 45,
                'native': 320,
                'total': 1795
            },
            'clicks': {
                'banner': 38,
                'interstitial': 12,
                'rewarded': 45,  # Rewarded = completed views
                'native': 25,
                'total': 120
            },
            'revenue': {
                'banner': 3.75,
                'interstitial': 5.40,
                'rewarded': 11.25,
                'native': 6.25,
                'total': 26.65,
                'currency': 'USD'
            },
            'metrics': {
                'ctr': 6.68,  # Click-through rate %
                'ecpm': 14.85,  # Effective CPM
                'fillRate': 92.5  # Ad fill rate %
            }
        }

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting ad stats: {str(e)}")
        return jsonify({'error': 'Failed to get ad statistics'}), 500


@ads_bp.route('/test', methods=['GET'])
def test_ads():
    """
    Test endpoint to verify AdMob configuration.

    Returns:
        JSON response with test results
    """
    try:
        # Check if all AdMob IDs are configured
        admob_ids = {
            'appId': os.getenv('ADMOB_APP_ID'),
            'bannerAdUnitId': os.getenv('ADMOB_BANNER_ID'),
            'interstitialAdUnitId': os.getenv('ADMOB_INTERSTITIAL_ID'),
            'rewardedAdUnitId': os.getenv('ADMOB_REWARDED_ID'),
            'nativeAdUnitId': os.getenv('ADMOB_NATIVE_ID')
        }

        # Check which IDs are configured
        configured = {key: bool(value) for key, value in admob_ids.items()}
        all_configured = all(configured.values())

        return jsonify({
            'admobConfigured': all_configured,
            'configuration': configured,
            'testMode': os.getenv('ADMOB_TEST_MODE', 'false').lower() == 'true',
            'message': 'All AdMob IDs configured' if all_configured else 'Some AdMob IDs missing'
        }), 200

    except Exception as e:
        logger.error(f"Error testing ads config: {str(e)}")
        return jsonify({'error': 'Failed to test ads configuration'}), 500
