"""Resume management routes for filter modal and application."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime

from models.user import User
from config.database import get_users_collection
from utils.helpers import format_error_response, serialize_document

resume_bp = Blueprint('resume', __name__, url_prefix='/api/resume')


@resume_bp.route('/options', methods=['GET'])
@jwt_required()
def get_resume_options():
    """
    Get available resume options for user to select in filter modal.

    Returns list of all resume versions user can use for applications:
    1. Original uploaded resume
    2. AI-parsed resume
    3. Previously customized versions (from past applications)
    4. Ability to create new custom version

    Returns:
        JSON response with resume options
    """
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)

        if not user:
            return jsonify(format_error_response("User not found", 404))

        resume_options = []

        # Get resumes data
        resumes = user.get('resumes', {})
        profile = user.get('profile', {})

        # Option 1: Original uploaded resume
        if resumes.get('original') or profile.get('resume'):
            original_path = resumes.get('original') or profile.get('resume')
            resume_options.append({
                'id': 'original',
                'type': 'original',
                'name': 'Original Resume',
                'description': 'Your originally uploaded resume',
                'filePath': original_path,
                'uploadedAt': user.get('createdAt'),
                'recommended': False
            })

        # Option 2: AI-parsed resume (structured data)
        if resumes.get('parsed'):
            parsed_data = resumes['parsed']
            resume_options.append({
                'id': 'parsed',
                'type': 'parsed',
                'name': 'AI-Optimized Resume',
                'description': 'AI-parsed and structured resume with enhanced formatting',
                'data': parsed_data,
                'parsedAt': parsed_data.get('parsedAt'),
                'recommended': True  # Recommended for auto-apply
            })

        # Option 3: Previously customized versions
        versions = resumes.get('versions', [])
        for idx, version in enumerate(versions):
            resume_options.append({
                'id': f'version_{idx}',
                'type': 'customized',
                'name': version.get('name', f'Custom Resume {idx + 1}'),
                'description': version.get('description', 'Previously customized for specific job type'),
                'data': version.get('content'),
                'createdAt': version.get('createdAt'),
                'jobType': version.get('jobType'),  # e.g., "Software Engineer"
                'industry': version.get('industry'),  # e.g., "Technology"
                'recommended': False
            })

        # Option 4: Current default/selected resume
        default_version = resumes.get('defaultVersion')

        # Add metadata
        response = {
            'resumeOptions': resume_options,
            'totalOptions': len(resume_options),
            'currentDefault': default_version or 'parsed',  # Default to AI-parsed
            'hasResume': len(resume_options) > 0,
            'recommendation': {
                'message': 'We recommend using the AI-Optimized Resume for best results',
                'preferredOption': 'parsed'
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_bp.route('/select', methods=['POST'])
@jwt_required()
def select_default_resume():
    """
    Set default resume to use for applications (from filter modal).

    Request body:
    {
        "resumeId": "parsed",  // or "original", "version_0", etc.
        "resumeType": "parsed"  // or "original", "customized"
    }

    Returns:
        JSON response confirming selection
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'resumeId' not in data:
            return jsonify(format_error_response("Resume ID not specified", 400))

        resume_id = data['resumeId']
        resume_type = data.get('resumeType', 'parsed')

        users = get_users_collection()
        user = User.find_by_id(user_id)

        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Get the actual resume data based on ID
        resumes = user.get('resumes', {})
        selected_resume = None

        if resume_id == 'original':
            selected_resume = resumes.get('original') or user.get('profile', {}).get('resume')
        elif resume_id == 'parsed':
            selected_resume = resumes.get('parsed')
        elif resume_id.startswith('version_'):
            # Get specific version
            version_idx = int(resume_id.split('_')[1])
            versions = resumes.get('versions', [])
            if version_idx < len(versions):
                selected_resume = versions[version_idx]

        if not selected_resume:
            return jsonify(format_error_response("Resume not found", 404))

        # Update default resume selection
        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'resumes.defaultVersion': selected_resume,
                    'resumes.defaultVersionId': resume_id,
                    'resumes.defaultVersionType': resume_type,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            return jsonify(format_error_response("Failed to update resume selection", 500))

        return jsonify({
            'message': 'Default resume updated successfully',
            'selectedResume': {
                'id': resume_id,
                'type': resume_type
            }
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_bp.route('/create-version', methods=['POST'])
@jwt_required()
def create_custom_version():
    """
    Create a new customized resume version.

    Users can create multiple resume versions tailored for different job types.
    These will appear as options in the filter modal.

    Request body:
    {
        "name": "Software Engineer Resume",
        "description": "Optimized for software engineering roles",
        "jobType": "Software Engineer",
        "industry": "Technology",
        "content": {...}  // Resume data
    }

    Returns:
        JSON response with created version
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("No data provided", 400))

        # Validate required fields
        if 'name' not in data or 'content' not in data:
            return jsonify(format_error_response("Name and content are required", 400))

        users = get_users_collection()
        user = User.find_by_id(user_id)

        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Create new version
        new_version = {
            'name': data['name'],
            'description': data.get('description', ''),
            'jobType': data.get('jobType'),
            'industry': data.get('industry'),
            'content': data['content'],
            'createdAt': datetime.utcnow()
        }

        # Add to versions array
        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$push': {'resumes.versions': new_version},
                '$set': {'updatedAt': datetime.utcnow()}
            }
        )

        if result.modified_count == 0:
            return jsonify(format_error_response("Failed to create resume version", 500))

        # Get the index of the new version
        updated_user = User.find_by_id(user_id)
        version_idx = len(updated_user.get('resumes', {}).get('versions', [])) - 1

        return jsonify({
            'message': 'Resume version created successfully',
            'version': {
                'id': f'version_{version_idx}',
                'name': data['name'],
                'type': 'customized'
            }
        }), 201

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_bp.route('/versions', methods=['GET'])
@jwt_required()
def get_all_versions():
    """
    Get all resume versions for the user.

    Returns:
        JSON response with all resume versions
    """
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)

        if not user:
            return jsonify(format_error_response("User not found", 404))

        resumes = user.get('resumes', {})
        versions = resumes.get('versions', [])

        # Format versions for response
        formatted_versions = []
        for idx, version in enumerate(versions):
            formatted_versions.append({
                'id': f'version_{idx}',
                'name': version.get('name'),
                'description': version.get('description'),
                'jobType': version.get('jobType'),
                'industry': version.get('industry'),
                'createdAt': version.get('createdAt')
            })

        return jsonify({
            'versions': formatted_versions,
            'totalVersions': len(formatted_versions)
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_bp.route('/version/<version_id>', methods=['DELETE'])
@jwt_required()
def delete_version(version_id):
    """
    Delete a specific resume version.

    Args:
        version_id: Version ID (e.g., "version_0")

    Returns:
        JSON response confirming deletion
    """
    try:
        user_id = get_jwt_identity()

        if not version_id.startswith('version_'):
            return jsonify(format_error_response("Invalid version ID", 400))

        version_idx = int(version_id.split('_')[1])

        users = get_users_collection()
        user = User.find_by_id(user_id)

        if not user:
            return jsonify(format_error_response("User not found", 404))

        versions = user.get('resumes', {}).get('versions', [])

        if version_idx >= len(versions):
            return jsonify(format_error_response("Version not found", 404))

        # Remove the version
        versions.pop(version_idx)

        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'resumes.versions': versions,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            return jsonify(format_error_response("Failed to delete version", 500))

        return jsonify({
            'message': 'Resume version deleted successfully'
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
