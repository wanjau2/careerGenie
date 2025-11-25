"""Document generation routes for resumes and cover letters."""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from services.document_generator import DocumentGenerator
from utils.helpers import format_error_response
import os

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')


@documents_bp.route('/generate-resume', methods=['POST'])
@jwt_required()
def generate_resume():
    """
    Generate a professional resume from user's profile data.

    Request body:
    {
        "format": "pdf" or "docx" (default: "pdf"),
        "template": "modern", "classic", or "minimal" (default: "modern"),
        "includePhoto": boolean (optional)
    }

    Returns:
        Resume file for download
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        # Get user data
        user = User.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Check if user has resume data
        if not user.get('resumes', {}).get('parsed'):
            return jsonify(format_error_response(
                "No resume data found. Please upload and parse your resume first.", 400
            ))

        # Get generation parameters
        format_type = data.get('format', 'pdf').lower()
        template = data.get('template', 'modern').lower()

        if format_type not in ['pdf', 'docx']:
            return jsonify(format_error_response("Invalid format. Use 'pdf' or 'docx'", 400))

        if template not in ['modern', 'classic', 'minimal']:
            return jsonify(format_error_response(
                "Invalid template. Use 'modern', 'classic', or 'minimal'", 400
            ))

        # Prepare user data for resume generation
        parsed_resume = user.get('resumes', {}).get('parsed', {})
        user_data = {
            'personalInfo': parsed_resume.get('personalInfo', {}),
            'summary': parsed_resume.get('summary', ''),
            'experiences': parsed_resume.get('experiences', []),
            'education': parsed_resume.get('education', []),
            'skills': parsed_resume.get('skills', []),
            'certifications': parsed_resume.get('certifications', []),
            'projects': parsed_resume.get('projects', []),
        }

        # Generate resume
        generator = DocumentGenerator()
        file_path = generator.generate_resume(user_data, format_type, template)

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"resume_{user.get('profile', {}).get('fullName', 'user').replace(' ', '_')}.{format_type}",
            mimetype='application/pdf' if format_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return jsonify(format_error_response(f"Failed to generate resume: {str(e)}", 500))


@documents_bp.route('/generate-cover-letter', methods=['POST'])
@jwt_required()
def generate_cover_letter():
    """
    Generate a tailored cover letter for a job application.

    Request body:
    {
        "jobId": "job_id" (optional, will fetch job details),
        "jobData": {  (if jobId not provided)
            "title": "Job Title",
            "company": "Company Name",
            "description": "Job description..."
        },
        "format": "pdf" or "docx" (default: "pdf"),
        "customContent": "Additional content to include" (optional)
    }

    Returns:
        Cover letter file for download
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify(format_error_response("No data provided", 400))

        # Get user data
        user = User.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Get job data
        job_data = data.get('jobData')
        job_id = data.get('jobId')

        if not job_data and not job_id:
            return jsonify(format_error_response(
                "Either jobData or jobId must be provided", 400
            ))

        if job_id:
            # Fetch job from database
            from models.job import Job
            from utils.helpers import is_valid_object_id

            if not is_valid_object_id(job_id):
                return jsonify(format_error_response("Invalid job ID", 400))

            job = Job.find_by_id(job_id)

            if not job:
                return jsonify(format_error_response("Job not found", 404))

            # Use fetched job data
            job_data = job

        # Validate job data
        if not job_data.get('title') or not job_data.get('company'):
            return jsonify(format_error_response(
                "Job data must include title and company", 400
            ))

        # Get generation parameters
        format_type = data.get('format', 'pdf').lower()
        custom_content = data.get('customContent')

        if format_type not in ['pdf', 'docx']:
            return jsonify(format_error_response("Invalid format. Use 'pdf' or 'docx'", 400))

        # Prepare user data
        parsed_resume = user.get('resumes', {}).get('parsed', {})
        user_data = {
            'personalInfo': parsed_resume.get('personalInfo', {}),
            'summary': parsed_resume.get('summary', ''),
            'experiences': parsed_resume.get('experiences', []),
            'education': parsed_resume.get('education', []),
            'skills': parsed_resume.get('skills', []),
        }

        # Generate cover letter
        generator = DocumentGenerator()
        file_path = generator.generate_cover_letter(
            user_data, job_data, format_type, custom_content
        )

        # Send file
        company_name = job_data.get('company', 'company').replace(' ', '_')
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"cover_letter_{company_name}.{format_type}",
            mimetype='application/pdf' if format_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return jsonify(format_error_response(f"Failed to generate cover letter: {str(e)}", 500))


@documents_bp.route('/templates', methods=['GET'])
def get_resume_templates():
    """
    Get available resume templates.

    Returns:
        JSON with template information
    """
    templates = [
        {
            'id': 'modern',
            'name': 'Modern',
            'description': 'Clean and contemporary design with color accents',
            'preview': '/static/templates/modern_preview.png'
        },
        {
            'id': 'classic',
            'name': 'Classic',
            'description': 'Traditional professional format',
            'preview': '/static/templates/classic_preview.png'
        },
        {
            'id': 'minimal',
            'name': 'Minimal',
            'description': 'Simple and elegant layout',
            'preview': '/static/templates/minimal_preview.png'
        }
    ]

    return jsonify({
        'templates': templates,
        'count': len(templates)
    }), 200


@documents_bp.route('/preview-resume', methods=['POST'])
@jwt_required()
def preview_resume():
    """
    Generate a preview of resume without downloading.

    Request body:
    {
        "template": "modern", "classic", or "minimal" (default: "modern")
    }

    Returns:
        JSON with resume data formatted for preview
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        # Get user data
        user = User.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response("User not found", 404))

        # Get parsed resume data
        parsed_resume = user.get('resumes', {}).get('parsed', {})

        if not parsed_resume:
            return jsonify(format_error_response(
                "No resume data found. Please upload and parse your resume first.", 400
            ))

        return jsonify({
            'success': True,
            'preview': {
                'personalInfo': parsed_resume.get('personalInfo', {}),
                'summary': parsed_resume.get('summary', ''),
                'experiences': parsed_resume.get('experiences', []),
                'education': parsed_resume.get('education', []),
                'skills': parsed_resume.get('skills', []),
                'certifications': parsed_resume.get('certifications', []),
                'projects': parsed_resume.get('projects', []),
            }
        }), 200

    except Exception as e:
        return jsonify(format_error_response(f"Failed to generate preview: {str(e)}", 500))
