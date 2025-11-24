"""Gmail API integration service for reading and parsing job application emails."""
import os
import base64
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.database import get_database

logger = logging.getLogger(__name__)


class GmailService:
    """Service for Gmail API OAuth and email operations."""

    # Gmail API scopes - read-only access to emails
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self):
        """Initialize Gmail service."""
        self.credentials_file = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials/gmail_credentials.json')
        self.redirect_uri = os.getenv('GMAIL_REDIRECT_URI', 'http://localhost:8000/api/email/oauth2callback')

    def get_authorization_url(self, user_id: str) -> str:
        """
        Generate OAuth2 authorization URL for user to grant Gmail access.

        Args:
            user_id: User ID to associate with credentials

        Returns:
            str: Authorization URL for user to visit
        """
        try:
            # Check if credentials file exists
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {self.credentials_file}. "
                    "Please download OAuth 2.0 credentials from Google Cloud Console."
                )

            # Create OAuth flow
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=self.redirect_uri
            )

            # Generate authorization URL with state parameter containing user_id
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,
                prompt='consent'  # Force consent screen to get refresh token
            )

            # Store flow state temporarily for callback
            db = get_database()
            db.oauth_states.update_one(
                {'userId': user_id},
                {
                    '$set': {
                        'state': state,
                        'createdAt': datetime.utcnow(),
                        'expiresAt': datetime.utcnow() + timedelta(minutes=10)
                    }
                },
                upsert=True
            )

            logger.info(f"Generated Gmail authorization URL for user {user_id}")
            return authorization_url

        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise

    def handle_oauth_callback(self, code: str, state: str) -> Tuple[bool, str, Optional[str]]:
        """
        Handle OAuth callback and store credentials.

        Args:
            code: Authorization code from OAuth callback
            state: State parameter (contains user_id)

        Returns:
            Tuple[bool, str, Optional[str]]: (success, user_id, error_message)
        """
        try:
            # Verify state and get user_id
            db = get_database()
            state_doc = db.oauth_states.find_one({'state': state})

            if not state_doc:
                return False, '', 'Invalid or expired state parameter'

            user_id = state_doc['userId']

            # Check if state has expired
            if datetime.utcnow() > state_doc['expiresAt']:
                db.oauth_states.delete_one({'_id': state_doc['_id']})
                return False, user_id, 'Authorization session expired'

            # Exchange code for credentials
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=self.redirect_uri
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Store credentials in database
            self._store_credentials(user_id, credentials)

            # Clean up state
            db.oauth_states.delete_one({'_id': state_doc['_id']})

            logger.info(f"Successfully stored Gmail credentials for user {user_id}")
            return True, user_id, None

        except Exception as e:
            logger.error(f"Error handling OAuth callback: {str(e)}")
            return False, '', str(e)

    def _store_credentials(self, user_id: str, credentials: Credentials):
        """Store Gmail credentials in database."""
        db = get_db()

        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }

        db.gmail_credentials.update_one(
            {'userId': user_id},
            {
                '$set': {
                    'credentials': creds_data,
                    'connectedAt': datetime.utcnow(),
                    'enabled': True,
                    'scanEnabled': True
                }
            },
            upsert=True
        )

    def _load_credentials(self, user_id: str) -> Optional[Credentials]:
        """Load and refresh Gmail credentials from database."""
        try:
            db = get_database()
            creds_doc = db.gmail_credentials.find_one({'userId': user_id})

            if not creds_doc or not creds_doc.get('enabled'):
                return None

            creds_data = creds_doc['credentials']

            # Recreate credentials object
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )

            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Update stored credentials
                self._store_credentials(user_id, credentials)

            return credentials

        except Exception as e:
            logger.error(f"Error loading credentials for user {user_id}: {str(e)}")
            return None

    def disconnect(self, user_id: str) -> bool:
        """
        Disconnect Gmail integration for user.

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        try:
            db = get_database()
            result = db.gmail_credentials.update_one(
                {'userId': user_id},
                {'$set': {'enabled': False, 'disconnectedAt': datetime.utcnow()}}
            )

            logger.info(f"Disconnected Gmail for user {user_id}")
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error disconnecting Gmail for user {user_id}: {str(e)}")
            return False

    def get_status(self, user_id: str) -> Dict:
        """
        Get Gmail integration status for user.

        Args:
            user_id: User ID

        Returns:
            dict: Status information
        """
        try:
            db = get_database()
            creds_doc = db.gmail_credentials.find_one({'userId': user_id})

            if not creds_doc:
                return {
                    'enabled': False,
                    'scanEnabled': False,
                    'connectedAt': None,
                    'lastScanDate': None,
                    'lastScanResults': None
                }

            return {
                'enabled': creds_doc.get('enabled', False),
                'scanEnabled': creds_doc.get('scanEnabled', True),
                'connectedAt': creds_doc.get('connectedAt').isoformat() if creds_doc.get('connectedAt') else None,
                'lastScanDate': creds_doc.get('lastScanDate').isoformat() if creds_doc.get('lastScanDate') else None,
                'lastScanResults': creds_doc.get('lastScanResults')
            }

        except Exception as e:
            logger.error(f"Error getting Gmail status for user {user_id}: {str(e)}")
            return {'enabled': False, 'error': str(e)}

    def toggle_scan(self, user_id: str, enabled: bool) -> bool:
        """
        Enable or disable automatic email scanning.

        Args:
            user_id: User ID
            enabled: Whether to enable scanning

        Returns:
            bool: Success status
        """
        try:
            db = get_database()
            result = db.gmail_credentials.update_one(
                {'userId': user_id},
                {'$set': {'scanEnabled': enabled}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error toggling scan for user {user_id}: {str(e)}")
            return False

    def fetch_emails(
        self,
        user_id: str,
        days_back: int = 7,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Fetch recent emails from user's Gmail.

        Args:
            user_id: User ID
            days_back: How many days back to search
            max_results: Maximum number of emails to fetch

        Returns:
            List[Dict]: List of email messages
        """
        try:
            credentials = self._load_credentials(user_id)
            if not credentials:
                logger.warning(f"No valid credentials found for user {user_id}")
                return []

            # Build Gmail API service
            service = build('gmail', 'v1', credentials=credentials)

            # Calculate date for search query
            after_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y/%m/%d')

            # Search for job-related emails
            query = f'after:{after_date} (from:noreply OR from:jobs OR from:talent OR from:recruiting OR from:hr OR subject:interview OR subject:application OR subject:position OR subject:offer OR subject:rejection OR subject:congratulations)'

            # Get message IDs
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                logger.info(f"No job-related emails found for user {user_id}")
                return []

            # Fetch full message details
            emails = []
            for msg in messages:
                try:
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email_data = self._parse_message(message)
                    if email_data:
                        emails.append(email_data)

                except HttpError as e:
                    logger.error(f"Error fetching message {msg['id']}: {str(e)}")
                    continue

            logger.info(f"Fetched {len(emails)} job-related emails for user {user_id}")
            return emails

        except HttpError as e:
            logger.error(f"Gmail API error for user {user_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching emails for user {user_id}: {str(e)}")
            return []

    def _parse_message(self, message: Dict) -> Optional[Dict]:
        """
        Parse Gmail message into structured format.

        Args:
            message: Gmail message object

        Returns:
            Optional[Dict]: Parsed email data
        """
        try:
            headers = message['payload']['headers']

            # Extract headers
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Extract body
            body = self._get_message_body(message['payload'])

            # Parse date
            from email.utils import parsedate_to_datetime
            try:
                received_date = parsedate_to_datetime(date_str)
            except:
                received_date = datetime.utcnow()

            return {
                'id': message['id'],
                'threadId': message['threadId'],
                'subject': subject,
                'from': from_email,
                'receivedAt': received_date.isoformat(),
                'body': body,
                'snippet': message.get('snippet', '')
            }

        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None

    def _get_message_body(self, payload: Dict) -> str:
        """Extract email body from message payload."""
        try:
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    elif part['mimeType'] == 'text/html':
                        # Fallback to HTML if no plain text
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            else:
                # Simple message
                data = payload['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            return ''

        except Exception as e:
            logger.error(f"Error extracting message body: {str(e)}")
            return ''

    def update_scan_results(self, user_id: str, results: Dict):
        """Update last scan results in database."""
        try:
            db = get_database()
            db.gmail_credentials.update_one(
                {'userId': user_id},
                {
                    '$set': {
                        'lastScanDate': datetime.utcnow(),
                        'lastScanResults': results
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating scan results: {str(e)}")
