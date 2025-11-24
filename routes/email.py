"""Email integration routes for Gmail OAuth and scanning."""
import logging
from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.gmail_service import GmailService
from services.email_parser_service import EmailParserService
from models.swipe import Application
from utils.helpers import format_error_response

logger = logging.getLogger(__name__)

email_bp = Blueprint('email', __name__, url_prefix='/api/email')


@email_bp.route('/status', methods=['GET'])
@jwt_required()
def get_email_status():
    """
    Get Gmail integration status for current user.

    Returns:
        JSON response with integration status
    """
    try:
        user_id = get_jwt_identity()
        gmail_service = GmailService()

        status = gmail_service.get_status(user_id)

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Error getting email status: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@email_bp.route('/connect/gmail', methods=['POST'])
@jwt_required()
def connect_gmail():
    """
    Initiate Gmail OAuth flow.

    Returns:
        JSON response with authorization URL
    """
    try:
        user_id = get_jwt_identity()
        gmail_service = GmailService()

        # Generate authorization URL
        auth_url = gmail_service.get_authorization_url(user_id)

        return jsonify({
            'message': 'Authorization URL generated',
            'authorizationUrl': auth_url
        }), 200

    except FileNotFoundError as e:
        logger.error(f"Gmail credentials file not found: {str(e)}")
        return jsonify(format_error_response(
            "Gmail integration not configured. Please contact administrator.",
            503
        ))
    except Exception as e:
        logger.error(f"Error connecting Gmail: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@email_bp.route('/oauth2callback', methods=['GET'])
def oauth_callback():
    """
    Handle OAuth2 callback from Google.

    Query params:
        code: Authorization code
        state: State parameter (contains user_id)
        error: Error if user denied access

    Returns:
        Redirect to frontend with success/error status
    """
    try:
        # Check for error
        error = request.args.get('error')
        if error:
            logger.warning(f"OAuth error: {error}")
            # Redirect to frontend with error
            frontend_url = request.host_url.replace('8000', '3000')  # Adjust for Flutter
            return redirect(f"{frontend_url}email-integration?error={error}")

        # Get authorization code and state
        code = request.args.get('code')
        state = request.args.get('state')

        if not code or not state:
            return jsonify(format_error_response("Missing authorization code or state", 400))

        # Handle callback
        gmail_service = GmailService()
        success, user_id, error_msg = gmail_service.handle_oauth_callback(code, state)

        if not success:
            logger.error(f"OAuth callback failed: {error_msg}")
            return jsonify(format_error_response(error_msg or "OAuth callback failed", 400))

        # Success - return simple HTML page that closes
        return '''
        <html>
            <head><title>Gmail Connected</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✓ Gmail Connected Successfully!</h1>
                <p>You can close this window and return to the app.</p>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 2000);
                </script>
            </body>
        </html>
        '''

    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@email_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def disconnect_gmail():
    """
    Disconnect Gmail integration.

    Returns:
        JSON response with success status
    """
    try:
        user_id = get_jwt_identity()
        gmail_service = GmailService()

        success = gmail_service.disconnect(user_id)

        if not success:
            return jsonify(format_error_response("Failed to disconnect Gmail", 500))

        return jsonify({
            'message': 'Gmail disconnected successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@email_bp.route('/toggle', methods=['POST'])
@jwt_required()
def toggle_scan():
    """
    Enable or disable automatic email scanning.

    Request body:
    {
        "enabled": true/false
    }

    Returns:
        JSON response with success status
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if 'enabled' not in data:
            return jsonify(format_error_response("'enabled' field is required", 400))

        enabled = data['enabled']
        gmail_service = GmailService()

        success = gmail_service.toggle_scan(user_id, enabled)

        if not success:
            return jsonify(format_error_response("Failed to toggle scan setting", 500))

        return jsonify({
            'message': f'Automatic scanning {"enabled" if enabled else "disabled"}',
            'enabled': enabled
        }), 200

    except Exception as e:
        logger.error(f"Error toggling scan: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@email_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_emails():
    """
    Manually scan emails for job application updates.

    Request body:
    {
        "daysBack": 7,      // optional, default 7
        "maxResults": 100   // optional, default 100
    }

    Returns:
        JSON response with scan results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        days_back = data.get('daysBack', 7)
        max_results = data.get('maxResults', 100)

        logger.info(f"Starting email scan for user {user_id}: {days_back} days, max {max_results} emails")

        # Initialize services
        gmail_service = GmailService()
        parser_service = EmailParserService()

        # Fetch emails from Gmail
        emails = gmail_service.fetch_emails(user_id, days_back, max_results)

        if not emails:
            return jsonify({
                'message': 'No job-related emails found',
                'emailsScanned': 0,
                'jobEmailsFound': 0,
                'applicationsMatched': 0,
                'statusesUpdated': 0
            }), 200

        # Get user's applications
        applications = Application.get_user_applications(user_id, skip=0, limit=1000)

        # Scan and match emails to applications
        results = parser_service.scan_and_update_applications(emails, applications)

        # Update application statuses
        for update in results['updates']:
            app_id = update['applicationId']
            new_status = update['newStatus']
            confidence = update['confidence']

            # Map status to database format
            status_mapping = {
                'rejected': 'rejected',
                'interview_scheduled': 'interview_scheduled',
                'under_review': 'under_review',
                'offer_received': 'accepted',  # Map to accepted (can be refined)
                'interviewed': 'interviewed'
            }

            db_status = status_mapping.get(new_status)
            if db_status:
                note = f"Auto-detected from email: {update['emailSubject']} (confidence: {confidence:.0%})"
                Application.update_application_status(app_id, db_status, note)

        # Store scan results
        gmail_service.update_scan_results(user_id, {
            'emailsScanned': results['emailsScanned'],
            'jobEmailsFound': results['jobEmailsFound'],
            'applicationsMatched': results['applicationsMatched'],
            'statusesUpdated': results['statusesUpdated']
        })

        logger.info(f"Email scan completed for user {user_id}: {results}")

        return jsonify({
            'message': 'Email scan completed successfully',
            **results
        }), 200

    except Exception as e:
        logger.error(f"Error scanning emails: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@email_bp.route('/test', methods=['GET'])
@jwt_required()
def test_connection():
    """
    Test Gmail connection for current user.

    Returns:
        JSON response with connection status
    """
    try:
        user_id = get_jwt_identity()
        gmail_service = GmailService()

        # Try to load credentials
        credentials = gmail_service._load_credentials(user_id)

        if not credentials:
            return jsonify({
                'connected': False,
                'message': 'No valid Gmail credentials found'
            }), 200

        return jsonify({
            'connected': True,
            'message': 'Gmail connection is active',
            'hasRefreshToken': credentials.refresh_token is not None
        }), 200

    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
