"""LinkedIn OAuth authentication service."""
import os
import requests
from authlib.integrations.flask_client import OAuth
from flask import session


class LinkedInAuthService:
    """Handle LinkedIn OAuth 2.0 authentication."""

    def __init__(self, app=None):
        """
        Initialize LinkedIn OAuth service.

        Args:
            app: Flask application instance
        """
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI')
        self.oauth = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize OAuth with Flask app."""
        self.oauth = OAuth(app)

        self.oauth.register(
            name='linkedin',
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
            access_token_params=None,
            authorize_url='https://www.linkedin.com/oauth/v2/authorization',
            authorize_params=None,
            api_base_url='https://api.linkedin.com/v2/',
            client_kwargs={'scope': 'r_liteprofile r_emailaddress w_member_social'},
        )

    def get_authorization_url(self):
        """
        Get LinkedIn authorization URL.

        Returns:
            str: Authorization URL to redirect user to
        """
        if not self.oauth:
            raise ValueError("OAuth not initialized. Call init_app() first.")

        linkedin = self.oauth.create_client('linkedin')
        redirect_uri = self.redirect_uri
        return linkedin.authorize_redirect(redirect_uri)

    def handle_callback(self, code):
        """
        Handle OAuth callback and exchange code for access token.

        Args:
            code: Authorization code from LinkedIn

        Returns:
            dict: Access token response
        """
        token_url = 'https://www.linkedin.com/oauth/v2/accessToken'

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        return response.json()

    def get_user_profile(self, access_token):
        """
        Fetch user's LinkedIn profile data.

        Args:
            access_token: LinkedIn access token

        Returns:
            dict: User profile data
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        # Get basic profile
        profile_url = 'https://api.linkedin.com/v2/me'
        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        # Get email
        email_url = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'
        email_response = requests.get(email_url, headers=headers)
        email_response.raise_for_status()
        email_data = email_response.json()

        # Extract email
        email = None
        if 'elements' in email_data and len(email_data['elements']) > 0:
            email = email_data['elements'][0]['handle~']['emailAddress']

        # Combine data
        user_data = {
            'id': profile_data.get('id'),
            'firstName': profile_data.get('localizedFirstName'),
            'lastName': profile_data.get('localizedLastName'),
            'email': email,
            'profilePicture': None,  # Would need additional API call
            'headline': None,  # Requires additional permissions
        }

        return user_data

    def get_user_positions(self, access_token):
        """
        Fetch user's work experience (positions).

        Note: Requires additional LinkedIn API permissions.

        Args:
            access_token: LinkedIn access token

        Returns:
            list: Work experience entries
        """
        # Note: This endpoint requires partner program access or specific permissions
        # For now, return empty list - implement when permissions are available

        return {
            'message': 'Work experience requires LinkedIn Partner Program access',
            'positions': []
        }

    def revoke_access(self, access_token):
        """
        Revoke LinkedIn access token.

        Args:
            access_token: Token to revoke

        Returns:
            bool: Success status
        """
        try:
            revoke_url = 'https://www.linkedin.com/oauth/v2/revoke'
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'token': access_token
            }

            response = requests.post(revoke_url, data=data)
            return response.status_code == 200

        except Exception as e:
            print(f"Error revoking LinkedIn access: {e}")
            return False
