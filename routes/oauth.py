"""OAuth authentication routes for LinkedIn."""
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, create_refresh_token
import os
import secrets
from datetime import datetime, timedelta

from services.linkedin_auth import LinkedInAuthService
from models.user import User
from config.database import get_database
from utils.helpers import format_success_response, format_error_response

oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/oauth')

# Initialize LinkedIn auth service
linkedin_auth = LinkedInAuthService()


@oauth_bp.route('/linkedin/url', methods=['GET'])
def get_linkedin_auth_url():
    """
    Get LinkedIn OAuth authorization URL.

    Query Parameters:
        redirect_uri: Redirect URI after OAuth completion

    Returns:
        JSON with authorization URL and state
    """
    try:
        redirect_uri = request.args.get('redirect_uri')

        if not redirect_uri:
            return jsonify(format_error_response(
                'redirect_uri parameter is required',
                400
            )), 400

        # Log the redirect URI for debugging
        print(f'DEBUG [OAuth]: Generating LinkedIn auth URL with redirect_uri: {redirect_uri}')

        # Get LinkedIn credentials from environment
        client_id = os.getenv('LINKEDIN_CLIENT_ID')

        if not client_id:
            return jsonify(format_error_response(
                'LinkedIn OAuth not configured. Please set LINKEDIN_CLIENT_ID environment variable.',
                503
            )), 503

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        session['linkedin_oauth_state'] = state
        session['linkedin_redirect_uri'] = redirect_uri

        print(f'DEBUG [OAuth]: Generated state: {state}')

        # Build authorization URL
        # Updated scopes for LinkedIn API v2 (openid profile email are the new standard scopes)
        # Note: r_liteprofile and r_emailaddress are deprecated
        scope = 'openid profile email'
        auth_url = (
            f'https://www.linkedin.com/oauth/v2/authorization'
            f'?response_type=code'
            f'&client_id={client_id}'
            f'&redirect_uri={redirect_uri}'
            f'&state={state}'
            f'&scope={scope}'
        )

        return jsonify(format_success_response(
            data={
                'authUrl': auth_url,
                'state': state
            },
            message='LinkedIn authorization URL generated'
        )), 200

    except Exception as e:
        return jsonify(format_error_response(
            f'Failed to generate LinkedIn auth URL: {str(e)}',
            500
        )), 500


@oauth_bp.route('/linkedin/callback', methods=['POST'])
def linkedin_callback():
    """
    Handle LinkedIn OAuth callback.

    Request Body:
        code: Authorization code from LinkedIn
        redirect_uri: Redirect URI used in authorization
        state: State parameter for CSRF protection (optional)

    Returns:
        JSON with access token and user data
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify(format_error_response(
                'Request body is required',
                400
            )), 400

        code = data.get('code')
        redirect_uri = data.get('redirectUri')
        state = data.get('state')

        if not code or not redirect_uri:
            return jsonify(format_error_response(
                'code and redirectUri are required',
                400
            )), 400

        # Verify state if provided (CSRF protection)
        if state and session.get('linkedin_oauth_state'):
            if state != session.get('linkedin_oauth_state'):
                return jsonify(format_error_response(
                    'Invalid state parameter',
                    400
                )), 400

        # Exchange code for access token
        client_id = os.getenv('LINKEDIN_CLIENT_ID')
        client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')

        if not client_id or not client_secret:
            return jsonify(format_error_response(
                'LinkedIn OAuth not configured',
                503
            )), 503

        # Create LinkedIn auth service instance
        linkedin = LinkedInAuthService()
        linkedin.client_id = client_id
        linkedin.client_secret = client_secret
        linkedin.redirect_uri = redirect_uri

        # Get access token
        token_response = linkedin.handle_callback(code)
        access_token = token_response.get('access_token')

        if not access_token:
            return jsonify(format_error_response(
                'Failed to obtain access token from LinkedIn',
                400
            )), 400

        # Get user profile from LinkedIn
        user_profile = linkedin.get_user_profile(access_token)

        if not user_profile or not user_profile.get('email'):
            return jsonify(format_error_response(
                'Failed to retrieve user profile from LinkedIn',
                400
            )), 400

        # Check if user exists
        db = get_database()
        users_collection = db['users']

        email = user_profile['email']
        existing_user = users_collection.find_one({'email': email})

        if existing_user:
            # User exists - login
            user_id = str(existing_user['_id'])

            # Update LinkedIn profile data if needed
            update_data = {
                'linkedinId': user_profile.get('id'),
                'linkedinProfile': user_profile,
                'lastLogin': datetime.utcnow()
            }
            users_collection.update_one(
                {'_id': existing_user['_id']},
                {'$set': update_data}
            )

        else:
            # New user - register
            new_user = {
                'email': email,
                'firstName': user_profile.get('firstName', ''),
                'lastName': user_profile.get('lastName', ''),
                'linkedinId': user_profile.get('id'),
                'linkedinProfile': user_profile,
                'isEmailVerified': True,  # LinkedIn email is verified
                'createdAt': datetime.utcnow(),
                'lastLogin': datetime.utcnow(),
                'role': 'user',
                'subscriptionTier': 'free',
                'subscriptionStatus': 'active',
                'onboardingCompleted': False,
                'profile': {
                    'skills': [],
                    'experience': '',
                    'location': {},
                    'preferences': {
                        'jobTypes': [],
                        'industries': [],
                        'minSalary': 0,
                        'maxSalary': 0,
                        'remote': True,
                        'willingToRelocate': False
                    }
                }
            }

            result = users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)

        # Generate JWT tokens
        access_token_jwt = create_access_token(identity=user_id)
        refresh_token_jwt = create_refresh_token(identity=user_id)

        # Clear session
        session.pop('linkedin_oauth_state', None)
        session.pop('linkedin_redirect_uri', None)

        return jsonify(format_success_response(
            data={
                'accessToken': access_token_jwt,
                'refreshToken': refresh_token_jwt,
                'user': {
                    'id': user_id,
                    'email': email,
                    'firstName': user_profile.get('firstName', ''),
                    'lastName': user_profile.get('lastName', ''),
                    'onboardingCompleted': existing_user.get('onboardingCompleted', False) if existing_user else False
                }
            },
            message='LinkedIn authentication successful'
        )), 200

    except Exception as e:
        return jsonify(format_error_response(
            f'LinkedIn authentication failed: {str(e)}',
            500
        )), 500


@oauth_bp.route('/google/url', methods=['GET'])
def get_google_auth_url():
    """
    Get Google OAuth authorization URL.

    Note: This is a placeholder for future Google OAuth implementation.
    """
    return jsonify(format_error_response(
        'Google OAuth not yet implemented',
        501
    )), 501


@oauth_bp.route('/google/callback', methods=['POST'])
def google_callback():
    """
    Handle Google OAuth callback.

    Note: This is a placeholder for future Google OAuth implementation.
    """
    return jsonify(format_error_response(
        'Google OAuth not yet implemented',
        501
    )), 501
