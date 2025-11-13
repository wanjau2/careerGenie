"""Authentication service."""
from flask_jwt_extended import create_access_token, create_refresh_token
from models.user import User
from utils.validators import validate_email_address, validate_password, validate_required_fields
from utils.helpers import format_error_response, serialize_document


class AuthService:
    """Handle authentication logic."""

    @staticmethod
    def register_user(data):
        """
        Register a new user.

        Args:
            data: Registration data (email, password, firstName, lastName)

        Returns:
            tuple: (response_data, status_code)
        """
        # Validate required fields
        required_fields = ['email', 'password']
        is_valid, missing = validate_required_fields(data, required_fields)

        if not is_valid:
            return format_error_response(
                f"Missing required fields: {', '.join(missing)}",
                400
            )

        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName', '')
        last_name = data.get('lastName', '')

        # Validate email
        is_valid, result = validate_email_address(email)
        if not is_valid:
            return format_error_response(f"Invalid email: {result}", 400)

        normalized_email = result

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            return format_error_response(error, 400)

        # Check if user already exists
        existing_user = User.find_by_email(normalized_email)
        if existing_user:
            return format_error_response("Email already registered", 409)

        # Create user
        try:
            user_id = User.create_user(
                normalized_email,
                password,
                first_name,
                last_name
            )

            # Generate tokens
            access_token = create_access_token(identity=str(user_id))
            refresh_token = create_refresh_token(identity=str(user_id))

            # Get created user
            user = User.find_by_id(user_id)
            user_data = serialize_document(user)

            # Remove password hash from response
            if 'password_hash' in user_data:
                del user_data['password_hash']

            return {
                'message': 'User registered successfully',
                'user': user_data,
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 201

        except Exception as e:
            return format_error_response(f"Registration failed: {str(e)}", 500)

    @staticmethod
    def login_user(data):
        """
        Login a user.

        Args:
            data: Login data (email, password)

        Returns:
            tuple: (response_data, status_code)
        """
        # Validate required fields
        required_fields = ['email', 'password']
        is_valid, missing = validate_required_fields(data, required_fields)

        if not is_valid:
            return format_error_response(
                f"Missing required fields: {', '.join(missing)}",
                400
            )

        email = data.get('email')
        password = data.get('password')

        # Find user
        user = User.find_by_email(email)
        if not user:
            return format_error_response("Invalid credentials", 401)

        # Check if user is active
        if not user.get('isActive', True):
            return format_error_response("Account is deactivated", 403)

        # Verify password
        if not User.verify_password(password, user['password_hash']):
            return format_error_response("Invalid credentials", 401)

        # Generate tokens
        user_id = str(user['_id'])
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        # Serialize user data
        user_data = serialize_document(user)

        # Remove password hash from response
        if 'password_hash' in user_data:
            del user_data['password_hash']

        return {
            'message': 'Login successful',
            'user': user_data,
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 200

    @staticmethod
    def refresh_access_token(user_id):
        """
        Generate new access token.

        Args:
            user_id: User ID from refresh token

        Returns:
            tuple: (response_data, status_code)
        """
        # Verify user exists
        user = User.find_by_id(user_id)
        if not user:
            return format_error_response("User not found", 404)

        # Check if user is active
        if not user.get('isActive', True):
            return format_error_response("Account is deactivated", 403)

        # Generate new access token
        access_token = create_access_token(identity=user_id)

        return {
            'message': 'Token refreshed successfully',
            'access_token': access_token
        }, 200

    @staticmethod
    def get_user_profile(user_id):
        """
        Get user profile.

        Args:
            user_id: User ID

        Returns:
            tuple: (response_data, status_code)
        """
        user = User.find_by_id(user_id)
        if not user:
            return format_error_response("User not found", 404)

        # Serialize and clean user data
        user_data = serialize_document(user)

        # Remove password hash
        if 'password_hash' in user_data:
            del user_data['password_hash']

        return {'user': user_data}, 200
