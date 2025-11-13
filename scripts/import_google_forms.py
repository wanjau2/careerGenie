#!/usr/bin/env python3
"""
Automated script to import resumes from Google Forms.

This script can be run manually or scheduled via cron to periodically
import new resumes from a Google Drive folder.

Usage:
    python scripts/import_google_forms.py

Environment Variables:
    API_URL: Backend API URL (default: http://localhost:8000)
    ADMIN_TOKEN: JWT token for authentication
    GOOGLE_FORMS_FOLDER_ID: Google Drive folder ID
    IMPORT_METHOD: 'folder' or 'sheets' (default: folder)
    GOOGLE_SHEETS_ID: Google Sheets ID (if using sheets method)
"""

import os
import sys
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv('API_URL', 'http://localhost:8000')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
FOLDER_ID = os.getenv('GOOGLE_FORMS_FOLDER_ID')
SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
IMPORT_METHOD = os.getenv('IMPORT_METHOD', 'folder')  # 'folder' or 'sheets'

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_from_folder():
    """Import resumes from Google Drive folder."""
    if not FOLDER_ID:
        logger.error("GOOGLE_FORMS_FOLDER_ID not set in environment")
        return False

    logger.info(f"Importing resumes from Google Drive folder: {FOLDER_ID}")

    try:
        response = requests.post(
            f"{API_URL}/api/training/google-forms/import-folder",
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "folderId": FOLDER_ID,
                "corpusName": f"Auto-Import {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "category": "general"
            },
            timeout=300  # 5 minutes timeout
        )

        if response.status_code == 201:
            data = response.json()
            logger.info(f"✓ Successfully imported {data['filesUploaded']} resumes")
            logger.info(f"  Corpus ID: {data['corpusId']}")

            if data['filesFailed'] > 0:
                logger.warning(f"  {data['filesFailed']} files failed to import")
                logger.warning(f"  Failed files: {data.get('failedFiles', [])}")

            return True
        else:
            logger.error(f"✗ Import failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error("✗ Request timed out after 5 minutes")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Request error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}")
        return False


def import_from_sheets():
    """Import resumes from Google Sheets."""
    if not SHEETS_ID:
        logger.error("GOOGLE_SHEETS_ID not set in environment")
        return False

    logger.info(f"Importing resumes from Google Sheets: {SHEETS_ID}")

    try:
        response = requests.post(
            f"{API_URL}/api/training/google-forms/import-sheets",
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "spreadsheetId": SHEETS_ID,
                "sheetName": "Form Responses 1",
                "fileUrlColumn": "Upload Your Resume"
            },
            timeout=300  # 5 minutes timeout
        )

        if response.status_code == 201:
            data = response.json()
            logger.info(f"✓ Successfully imported {data['filesUploaded']} resumes")
            logger.info(f"  Corpus ID: {data['corpusId']}")

            if data['filesFailed'] > 0:
                logger.warning(f"  {data['filesFailed']} files failed to import")
                logger.warning(f"  Failed files: {data.get('failedFiles', [])}")

            return True
        else:
            logger.error(f"✗ Import failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error("✗ Request timed out after 5 minutes")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Request error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}")
        return False


def check_folder_info():
    """Check folder information before importing."""
    if not FOLDER_ID:
        return None

    try:
        response = requests.get(
            f"{API_URL}/api/training/google-forms/folder-info/{FOLDER_ID}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            folder = data.get('folder', {})
            logger.info(f"Folder: {folder.get('name')}")
            logger.info(f"Resume count: {folder.get('resumeCount')}")
            return folder
        else:
            logger.warning(f"Could not fetch folder info: {response.status_code}")
            return None

    except Exception as e:
        logger.warning(f"Error checking folder info: {str(e)}")
        return None


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Google Forms Resume Import")
    logger.info("=" * 60)

    # Check required environment variables
    if not ADMIN_TOKEN:
        logger.error("ADMIN_TOKEN not set in environment")
        logger.error("Please set ADMIN_TOKEN in .env file")
        sys.exit(1)

    # Check folder info if using folder method
    if IMPORT_METHOD == 'folder':
        folder_info = check_folder_info()
        if folder_info and folder_info.get('resumeCount', 0) == 0:
            logger.info("No new resumes found in folder. Exiting.")
            sys.exit(0)

    # Run import
    if IMPORT_METHOD == 'sheets':
        success = import_from_sheets()
    else:
        success = import_from_folder()

    # Exit with appropriate code
    if success:
        logger.info("=" * 60)
        logger.info("Import completed successfully!")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("Import failed!")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
