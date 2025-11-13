"""File upload and storage service."""
import os
from PIL import Image
import io
from werkzeug.utils import secure_filename
from config.settings import Config
from utils.helpers import generate_unique_filename, get_file_extension
from utils.validators import validate_file_type


class FileService:
    """Handle file uploads and storage."""

    @staticmethod
    def save_profile_picture(file, user_id):
        """
        Save and process profile picture.

        Args:
            file: FileStorage object
            user_id: User ID

        Returns:
            str: File path or None if failed
        """
        try:
            # Validate file type
            if not validate_file_type(file, Config.ALLOWED_IMAGE_EXTENSIONS):
                raise ValueError("Invalid image file type. Allowed: " +
                               ", ".join(Config.ALLOWED_IMAGE_EXTENSIONS))

            # Generate unique filename
            unique_filename = generate_unique_filename(
                file.filename,
                user_id,
                prefix='profile'
            )

            # Create directory if it doesn't exist
            upload_path = os.path.join(Config.UPLOAD_FOLDER, 'profiles')
            os.makedirs(upload_path, exist_ok=True)

            # Full file path
            file_path = os.path.join(upload_path, unique_filename)

            # Process image
            with Image.open(file.stream) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    else:
                        background.paste(img)
                    img = background

                # Resize maintaining aspect ratio
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)

                # Save optimized image
                img.save(file_path, 'JPEG', quality=85, optimize=True)

            # Return relative path for storage
            return f"/uploads/profiles/{unique_filename}"

        except Exception as e:
            print(f"Error saving profile picture: {e}")
            return None

    @staticmethod
    def save_resume(file, user_id):
        """
        Save resume document.

        Args:
            file: FileStorage object
            user_id: User ID

        Returns:
            str: File path or None if failed
        """
        try:
            # Validate file type
            if not validate_file_type(file, Config.ALLOWED_DOCUMENT_EXTENSIONS):
                raise ValueError("Invalid document file type. Allowed: " +
                               ", ".join(Config.ALLOWED_DOCUMENT_EXTENSIONS))

            # Generate unique filename
            unique_filename = generate_unique_filename(
                file.filename,
                user_id,
                prefix='resume'
            )

            # Create directory if it doesn't exist
            upload_path = os.path.join(Config.UPLOAD_FOLDER, 'resumes')
            os.makedirs(upload_path, exist_ok=True)

            # Full file path
            file_path = os.path.join(upload_path, unique_filename)

            # Save file
            file.save(file_path)

            # Return relative path for storage
            return f"/uploads/resumes/{unique_filename}"

        except Exception as e:
            print(f"Error saving resume: {e}")
            return None

    @staticmethod
    def save_document(file, user_id, doc_type='document'):
        """
        Save generic document.

        Args:
            file: FileStorage object
            user_id: User ID
            doc_type: Type of document

        Returns:
            str: File path or None if failed
        """
        try:
            # Validate file type
            if not validate_file_type(file, Config.ALLOWED_DOCUMENT_EXTENSIONS):
                raise ValueError("Invalid document file type")

            # Generate unique filename
            unique_filename = generate_unique_filename(
                file.filename,
                user_id,
                prefix=doc_type
            )

            # Create directory if it doesn't exist
            upload_path = os.path.join(Config.UPLOAD_FOLDER, 'documents')
            os.makedirs(upload_path, exist_ok=True)

            # Full file path
            file_path = os.path.join(upload_path, unique_filename)

            # Save file
            file.save(file_path)

            # Return relative path for storage
            return f"/uploads/documents/{unique_filename}"

        except Exception as e:
            print(f"Error saving document: {e}")
            return None

    @staticmethod
    def delete_file(file_path):
        """
        Delete a file from storage.

        Args:
            file_path: Relative file path

        Returns:
            bool: True if successful
        """
        try:
            # Convert relative path to absolute
            if file_path.startswith('/uploads/'):
                file_path = file_path[1:]  # Remove leading slash

            full_path = os.path.join(Config.UPLOAD_FOLDER, file_path.replace('/uploads/', ''))

            # Delete file if it exists
            if os.path.exists(full_path):
                os.remove(full_path)
                return True

            return False

        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    @staticmethod
    def validate_image_file(file):
        """
        Validate image file before processing.

        Args:
            file: FileStorage object

        Returns:
            tuple: (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"

        if file.filename == '':
            return False, "No file selected"

        # Check file type
        if not validate_file_type(file, Config.ALLOWED_IMAGE_EXTENSIONS):
            return False, f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_IMAGE_EXTENSIONS)}"

        # Check file size (read first chunk to check)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > Config.MAX_CONTENT_LENGTH:
            max_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"

        # Verify it's actually an image
        try:
            img = Image.open(file.stream)
            img.verify()
            file.stream.seek(0)  # Reset stream after verification
            return True, None
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    @staticmethod
    def validate_document_file(file):
        """
        Validate document file before processing.

        Args:
            file: FileStorage object

        Returns:
            tuple: (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"

        if file.filename == '':
            return False, "No file selected"

        # Check file type
        if not validate_file_type(file, Config.ALLOWED_DOCUMENT_EXTENSIONS):
            return False, f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_DOCUMENT_EXTENSIONS)}"

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > Config.MAX_CONTENT_LENGTH:
            max_mb = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"

        return True, None
