"""Authentication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth_service import AuthService
from utils.helpers import format_error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.

    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePass123",
        "firstName": "John",
        "lastName": "Doe"
    }

    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify(format_error_response("No data provided", 400))

        response, status_code = AuthService.register_user(data)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user.

    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePass123"
    }

    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify(format_error_response("No data provided", 400))

        response, status_code = AuthService.login_user(data)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.

    Returns:
        JSON response with new access token
    """
    try:
        user_id = get_jwt_identity()
        response, status_code = AuthService.refresh_access_token(user_id)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user profile.

    Returns:
        JSON response with user data
    """
    try:
        user_id = get_jwt_identity()
        response, status_code = AuthService.get_user_profile(user_id)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (client should discard tokens).

    Returns:
        JSON response confirming logout
    """
    # In a more complete implementation, you would:
    # 1. Add token to blacklist
    # 2. Clear any server-side sessions
    # For now, we just return success and let client clear tokens

    return jsonify({
        'message': 'Logout successful. Please discard your tokens.'
    }), 200
