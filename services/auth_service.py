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

    @staticmethod
    def forgot_password(data):
        """
        Request password reset.

        Args:
            data: Request data with email

        Returns:
            tuple: (response_data, status_code)
        """
        email = data.get('email')
        if not email:
            return format_error_response("Email is required", 400)

        # Validate email
        is_valid, result = validate_email_address(email)
        if not is_valid:
            return format_error_response(f"Invalid email: {result}", 400)

        # Generate reset token
        reset_token, user_id = User.set_reset_token(result)

        # Return success even if user doesn't exist (security best practice)
        # This prevents email enumeration attacks
        if not reset_token:
            return {
                'message': 'If an account with that email exists, a password reset link has been sent.'
            }, 200

        # TODO: In production, send email with reset link
        # For now, return the token (only for development/testing)
        # In production, you would send: https://yourapp.com/reset-password?token={reset_token}
        return {
            'message': 'Password reset link sent to your email.',
            'resetToken': reset_token  # Remove this in production!
        }, 200

    @staticmethod
    def reset_password(data):
        """
        Reset password with token.

        Args:
            data: Request data with token and newPassword

        Returns:
            tuple: (response_data, status_code)
        """
        token = data.get('token')
        new_password = data.get('newPassword')

        if not token:
            return format_error_response("Reset token is required", 400)

        if not new_password:
            return format_error_response("New password is required", 400)

        # Validate password
        is_valid, error = validate_password(new_password)
        if not is_valid:
            return format_error_response(error, 400)

        # Verify token
        user = User.verify_reset_token(token)
        if not user:
            return format_error_response("Invalid or expired reset token", 400)

        # Update password
        success = User.update_password(str(user['_id']), new_password)
        if not success:
            return format_error_response("Failed to reset password", 500)

        return {
            'message': 'Password reset successfully. You can now login with your new password.'
        }, 200

    @staticmethod
    def change_password(user_id, data):
        """
        Change password for logged-in user.

        Args:
            user_id: User ID
            data: Request data with currentPassword and newPassword

        Returns:
            tuple: (response_data, status_code)
        """
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        if not current_password:
            return format_error_response("Current password is required", 400)

        if not new_password:
            return format_error_response("New password is required", 400)

        # Validate new password
        is_valid, error = validate_password(new_password)
        if not is_valid:
            return format_error_response(error, 400)

        # Get user
        user = User.find_by_id(user_id)
        if not user:
            return format_error_response("User not found", 404)

        # Verify current password
        if not User.verify_password(current_password, user['password_hash']):
            return format_error_response("Current password is incorrect", 401)

        # Check if new password is same as current
        if User.verify_password(new_password, user['password_hash']):
            return format_error_response("New password must be different from current password", 400)

        # Update password
        success = User.update_password(user_id, new_password)
        if not success:
            return format_error_response("Failed to change password", 500)

        return {
            'message': 'Password changed successfully'
        }, 200

    @staticmethod
    def verify_token(user_id):
        """
        Verify JWT token is valid.

        Args:
            user_id: User ID from JWT token

        Returns:
            tuple: (response_data, status_code)
        """
        # If we reach here, JWT is valid (jwt_required passed)
        user = User.find_by_id(user_id)
        if not user:
            return format_error_response("User not found", 404)

        # Check if user is active
        if not user.get('isActive', True):
            return format_error_response("Account is deactivated", 403)

        return {
            'valid': True,
            'userId': user_id,
            'email': user.get('email')
        }, 200
