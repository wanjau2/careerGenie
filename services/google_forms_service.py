"""Google Forms/Drive/Sheets integration service for collecting training resumes."""
import os
import logging
import io
from datetime import datetime
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from bson import ObjectId

from models.training import TrainingCorpus, TrainingResume
from services.resume_parser import ResumeParser

logger = logging.getLogger(__name__)


class GoogleFormsService:
    """Service for importing resumes from Google Forms/Drive/Sheets."""

    def __init__(self):
        """Initialize Google Forms service."""
        self.credentials = None
        self.drive_service = None
        self.sheets_service = None
        self.resume_parser = ResumeParser()
        self.training_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')

        # Ensure training directories exist
        os.makedirs(os.path.join(self.training_dir, 'resumes'), exist_ok=True)
        os.makedirs(os.path.join(self.training_dir, 'google_forms'), exist_ok=True)

        self._initialize_services()

    def _initialize_services(self):
        """Initialize Google API services with credentials."""
        try:
            import json

            # Scopes for Drive and Sheets API
            scopes = [
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/spreadsheets.readonly'
            ]

            # Try to load from environment variable first (for Railway/production)
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

            if service_account_json:
                # Parse JSON from environment variable
                logger.info("Loading Google credentials from environment variable")
                credentials_dict = json.loads(service_account_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=scopes
                )
            else:
                # Fall back to file (for local development)
                credentials_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')

                if not credentials_path or not os.path.exists(credentials_path):
                    logger.warning("Google service account credentials not found. Google Forms integration disabled.")
                    return

                logger.info("Loading Google credentials from file")
                self.credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=scopes
                )

            # Build services
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)

            logger.info("Google API services initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Google API services: {str(e)}")
            self.credentials = None

    def import_resumes_from_folder(
        self,
        folder_id: str,
        user_id: str,
        corpus_name: str = "Google Forms Import",
        category: str = "general"
    ) -> Dict:
        """
        Import all resume files from a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID
            user_id: User ID importing the resumes
            corpus_name: Name for the training corpus
            category: Category for the corpus

        Returns:
            Dictionary with import results
        """
        if not self.drive_service:
            return {
                'success': False,
                'error': 'Google Drive service not initialized. Check credentials.'
            }

        try:
            # Create corpus directory
            corpus_id = str(ObjectId())
            corpus_path = os.path.join(self.training_dir, 'google_forms', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            # Query files in the folder
            query = f"'{folder_id}' in parents and (mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mimeType='application/msword') and trashed=false"

            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, createdTime, size)",
                pageSize=100
            ).execute()

            files = results.get('files', [])

            if not files:
                return {
                    'success': False,
                    'error': 'No resume files found in the specified folder'
                }

            uploaded_files = []
            failed_files = []

            # Process each file
            for file_meta in files:
                try:
                    # Download file
                    file_id = file_meta['id']
                    file_name = file_meta['name']

                    logger.info(f"Downloading file: {file_name}")

                    request = self.drive_service.files().get_media(fileId=file_id)
                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                    # Save file locally
                    file_path = os.path.join(corpus_path, file_name)
                    with open(file_path, 'wb') as f:
                        f.write(file_content.getvalue())

                    # Parse resume
                    parsed = self.resume_parser.parse_resume(file_path)

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(parsed)

                    # Create training resume record
                    training_resume = {
                        'corpusId': corpus_id,
                        'filename': file_name,
                        'filePath': file_path,
                        'parsedData': parsed,
                        'qualityScore': quality_score,
                        'googleDriveFileId': file_id,
                        'uploadedAt': datetime.utcnow(),
                        'source': 'google_forms'
                    }

                    # Save to database
                    resume_id = TrainingResume.create(training_resume)

                    uploaded_files.append({
                        'filename': file_name,
                        'resumeId': str(resume_id),
                        'qualityScore': quality_score,
                        'googleDriveFileId': file_id
                    })

                    logger.info(f"Successfully imported: {file_name}")

                except Exception as e:
                    logger.error(f"Error processing file {file_meta.get('name', 'unknown')}: {str(e)}")
                    failed_files.append({
                        'filename': file_meta.get('name', 'unknown'),
                        'error': str(e)
                    })

            # Create corpus record
            corpus_data = {
                '_id': ObjectId(corpus_id),
                'name': corpus_name,
                'description': f"Imported from Google Drive folder on {datetime.utcnow().strftime('%Y-%m-%d')}",
                'category': category,
                'uploadedBy': ObjectId(user_id),
                'filesCount': len(uploaded_files),
                'totalResumes': len(uploaded_files),
                'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
                'googleDriveFolderId': folder_id,
                'source': 'google_forms',
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }

            TrainingCorpus.create(corpus_data)

            return {
                'success': True,
                'corpus_id': corpus_id,
                'corpus': corpus_data,
                'files_uploaded': len(uploaded_files),
                'files_failed': len(failed_files),
                'uploaded_files': uploaded_files,
                'failed_files': failed_files
            }

        except Exception as e:
            logger.error(f"Error importing resumes from Google Drive: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def import_from_sheets(
        self,
        spreadsheet_id: str,
        user_id: str,
        sheet_name: str = "Form Responses 1",
        file_url_column: str = "Resume File"
    ) -> Dict:
        """
        Import resumes from Google Sheets (form responses).

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            user_id: User ID importing the resumes
            sheet_name: Name of the sheet/tab with form responses
            file_url_column: Column name containing file URLs

        Returns:
            Dictionary with import results
        """
        if not self.sheets_service:
            return {
                'success': False,
                'error': 'Google Sheets service not initialized. Check credentials.'
            }

        try:
            # Read spreadsheet data
            range_name = f"{sheet_name}!A1:Z1000"  # Adjust range as needed
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                return {
                    'success': False,
                    'error': 'No data found in spreadsheet'
                }

            # Parse headers
            headers = values[0]

            # Find file URL column index
            try:
                file_url_idx = headers.index(file_url_column)
            except ValueError:
                return {
                    'success': False,
                    'error': f"Column '{file_url_column}' not found in sheet. Available columns: {', '.join(headers)}"
                }

            # Extract file IDs from URLs
            file_ids = []
            additional_data = []

            for row in values[1:]:  # Skip header row
                if len(row) > file_url_idx and row[file_url_idx]:
                    # Parse Google Drive URL to extract file ID
                    file_url = row[file_url_idx]
                    file_id = self._extract_file_id_from_url(file_url)

                    if file_id:
                        # Store additional form data
                        row_data = {}
                        for i, header in enumerate(headers):
                            if i < len(row):
                                row_data[header] = row[i]

                        file_ids.append(file_id)
                        additional_data.append(row_data)

            if not file_ids:
                return {
                    'success': False,
                    'error': 'No valid Google Drive file URLs found in the specified column'
                }

            # Create corpus directory
            corpus_id = str(ObjectId())
            corpus_path = os.path.join(self.training_dir, 'google_forms', corpus_id)
            os.makedirs(corpus_path, exist_ok=True)

            uploaded_files = []
            failed_files = []

            # Process each file
            for file_id, form_data in zip(file_ids, additional_data):
                try:
                    # Get file metadata
                    file_meta = self.drive_service.files().get(
                        fileId=file_id,
                        fields='name, mimeType'
                    ).execute()

                    file_name = file_meta['name']

                    logger.info(f"Downloading file: {file_name}")

                    # Download file
                    request = self.drive_service.files().get_media(fileId=file_id)
                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                    # Save file locally
                    file_path = os.path.join(corpus_path, file_name)
                    with open(file_path, 'wb') as f:
                        f.write(file_content.getvalue())

                    # Parse resume
                    parsed = self.resume_parser.parse_resume(file_path)

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(parsed)

                    # Create training resume record
                    training_resume = {
                        'corpusId': corpus_id,
                        'filename': file_name,
                        'filePath': file_path,
                        'parsedData': parsed,
                        'qualityScore': quality_score,
                        'googleDriveFileId': file_id,
                        'formData': form_data,  # Store additional form responses
                        'uploadedAt': datetime.utcnow(),
                        'source': 'google_forms'
                    }

                    # Save to database
                    resume_id = TrainingResume.create(training_resume)

                    uploaded_files.append({
                        'filename': file_name,
                        'resumeId': str(resume_id),
                        'qualityScore': quality_score,
                        'googleDriveFileId': file_id
                    })

                    logger.info(f"Successfully imported: {file_name}")

                except Exception as e:
                    logger.error(f"Error processing file {file_id}: {str(e)}")
                    failed_files.append({
                        'fileId': file_id,
                        'error': str(e)
                    })

            # Create corpus record
            corpus_data = {
                '_id': ObjectId(corpus_id),
                'name': f"Google Forms Import - {datetime.utcnow().strftime('%Y-%m-%d')}",
                'description': f"Imported from Google Sheets on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                'category': 'general',
                'uploadedBy': ObjectId(user_id),
                'filesCount': len(uploaded_files),
                'totalResumes': len(uploaded_files),
                'averageQualityScore': sum(f['qualityScore'] for f in uploaded_files) / len(uploaded_files) if uploaded_files else 0,
                'googleSheetsId': spreadsheet_id,
                'source': 'google_forms',
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }

            TrainingCorpus.create(corpus_data)

            return {
                'success': True,
                'corpus_id': corpus_id,
                'corpus': corpus_data,
                'files_uploaded': len(uploaded_files),
                'files_failed': len(failed_files),
                'uploaded_files': uploaded_files,
                'failed_files': failed_files
            }

        except Exception as e:
            logger.error(f"Error importing from Google Sheets: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_folder_info(self, folder_id: str) -> Dict:
        """
        Get information about a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            Dictionary with folder information
        """
        if not self.drive_service:
            return {
                'success': False,
                'error': 'Google Drive service not initialized'
            }

        try:
            # Get folder metadata
            folder = self.drive_service.files().get(
                fileId=folder_id,
                fields='id, name, createdTime, modifiedTime'
            ).execute()

            # Count files in folder
            query = f"'{folder_id}' in parents and (mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mimeType='application/msword') and trashed=false"

            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=1000
            ).execute()

            files = results.get('files', [])

            return {
                'success': True,
                'folder': {
                    'id': folder['id'],
                    'name': folder['name'],
                    'createdTime': folder.get('createdTime'),
                    'modifiedTime': folder.get('modifiedTime'),
                    'resumeCount': len(files)
                }
            }

        except Exception as e:
            logger.error(f"Error getting folder info: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_file_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract Google Drive file ID from various URL formats.

        Args:
            url: Google Drive URL

        Returns:
            File ID or None
        """
        import re

        # Handle different Google Drive URL formats
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/open\?id=([a-zA-Z0-9-_]+)',
            r'^([a-zA-Z0-9-_]+)$'  # Just the ID
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _calculate_quality_score(self, parsed_data: Dict) -> float:
        """
        Calculate quality score for a resume.

        Args:
            parsed_data: Parsed resume data

        Returns:
            Quality score between 0 and 1
        """
        score = 0.0
        max_score = 10.0

        # Contact information (1 point)
        if parsed_data.get('contact'):
            score += 1.0

        # Experience (3 points)
        experience = parsed_data.get('experience', [])
        if len(experience) > 0:
            score += 1.0
        if len(experience) >= 2:
            score += 1.0
        if len(experience) >= 3:
            score += 1.0

        # Education (2 points)
        education = parsed_data.get('education', [])
        if len(education) > 0:
            score += 1.5
        if len(education) >= 2:
            score += 0.5

        # Skills (2 points)
        skills = parsed_data.get('skills', [])
        if len(skills) >= 3:
            score += 1.0
        if len(skills) >= 6:
            score += 1.0

        # Length/completeness (2 points)
        text_length = len(parsed_data.get('raw_text', ''))
        if text_length > 200:
            score += 1.0
        if text_length > 500:
            score += 1.0

        return round(score / max_score, 2)
