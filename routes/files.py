"""File upload routes."""
from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from services.file_service import FileService
from utils.helpers import format_error_response
from config.settings import Config
import os

files_bp = Blueprint('files', __name__, url_prefix='/api/files')


@files_bp.route('/upload-avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """
    Upload user profile picture.

    Form data:
    - file: Image file (png, jpg, jpeg, gif, webp)

    Returns:
        JSON response with file URL
    """
    try:
        user_id = get_jwt_identity()

        # Check if file is present
        if 'file' not in request.files:
            return jsonify(format_error_response("No file provided", 400))

        file = request.files['file']

        # Validate file
        is_valid, error = FileService.validate_image_file(file)
        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Get user's current profile picture (for deletion)
        user = User.find_by_id(user_id)
        old_picture = user.get('profile', {}).get('profilePicture') if user else None

        # Save new profile picture
        file_path = FileService.save_profile_picture(file, user_id)

        if not file_path:
            return jsonify(format_error_response("Failed to save profile picture", 500))

        # Update user profile
        success = User.update_profile_picture(user_id, file_path)

        if not success:
            # Cleanup uploaded file if database update failed
            FileService.delete_file(file_path)
            return jsonify(format_error_response("Failed to update profile", 500))

        # Delete old profile picture if it exists
        if old_picture:
            FileService.delete_file(old_picture)

        return jsonify({
            'message': 'Profile picture uploaded successfully',
            'filePath': file_path,
            'fileUrl': f"{request.host_url.rstrip('/')}{file_path}"
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@files_bp.route('/upload-resume', methods=['POST'])
@jwt_required()
def upload_resume():
    """
    Upload user resume.

    Form data:
    - file: Document file (pdf, doc, docx)

    Returns:
        JSON response with file URL
    """
    try:
        user_id = get_jwt_identity()

        # Check if file is present
        if 'file' not in request.files:
            return jsonify(format_error_response("No file provided", 400))

        file = request.files['file']

        # Validate file
        is_valid, error = FileService.validate_document_file(file)
        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Get user's current resume (for deletion)
        user = User.find_by_id(user_id)
        old_resume = user.get('profile', {}).get('resume') if user else None

        # Save new resume
        file_path = FileService.save_resume(file, user_id)

        if not file_path:
            return jsonify(format_error_response("Failed to save resume", 500))

        # Queue resume for training corpus (background task)
        try:
            from celery_app import process_user_resume_for_training
            # Get absolute path for the saved resume
            abs_path = os.path.abspath(file_path) if not os.path.isabs(file_path) else file_path
            process_user_resume_for_training.delay(user_id, abs_path)
        except ImportError:
            # Celery not available, skip training corpus addition
            pass

        # Update user profile
        success = User.update_resume(user_id, file_path)

        if not success:
            # Cleanup uploaded file if database update failed
            FileService.delete_file(file_path)
            return jsonify(format_error_response("Failed to update profile", 500))

        # Delete old resume if it exists
        if old_resume:
            FileService.delete_file(old_resume)

        return jsonify({
            'message': 'Resume uploaded successfully',
            'filePath': file_path,
            'fileUrl': f"{request.host_url.rstrip('/')}{file_path}"
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@files_bp.route('/upload-document', methods=['POST'])
@jwt_required()
def upload_document():
    """
    Upload generic document.

    Form data:
    - file: Document file (pdf, doc, docx)
    - docType: Type of document (optional)

    Returns:
        JSON response with file URL
    """
    try:
        user_id = get_jwt_identity()

        # Check if file is present
        if 'file' not in request.files:
            return jsonify(format_error_response("No file provided", 400))

        file = request.files['file']
        doc_type = request.form.get('docType', 'document')

        # Validate file
        is_valid, error = FileService.validate_document_file(file)
        if not is_valid:
            return jsonify(format_error_response(error, 400))

        # Save document
        file_path = FileService.save_document(file, user_id, doc_type)

        if not file_path:
            return jsonify(format_error_response("Failed to save document", 500))

        return jsonify({
            'message': 'Document uploaded successfully',
            'filePath': file_path,
            'fileUrl': f"{request.host_url.rstrip('/')}{file_path}"
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@files_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_file():
    """
    Delete a file.

    Request body:
    {
        "filePath": "/uploads/profiles/image.jpg"
    }

    Returns:
        JSON response confirming deletion
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'filePath' not in data:
            return jsonify(format_error_response("File path not provided", 400))

        file_path = data['filePath']

        # Security check: ensure file belongs to user
        if str(user_id) not in file_path:
            return jsonify(format_error_response("Unauthorized", 403))

        # Delete file
        success = FileService.delete_file(file_path)

        if not success:
            return jsonify(format_error_response("Failed to delete file", 500))

        return jsonify({'message': 'File deleted successfully'}), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


# Serve uploaded files (for development - in production, use nginx or CDN)
@files_bp.route('/uploads/<path:filename>')
def serve_file(filename):
    """
    Serve uploaded files.

    Note: In production, files should be served by nginx or a CDN.
    This route is for development purposes only.
    """
    try:
        upload_folder = Config.UPLOAD_FOLDER
        return send_from_directory(upload_folder, filename)

    except Exception as e:
        return jsonify(format_error_response(f"File not found: {str(e)}", 404))
