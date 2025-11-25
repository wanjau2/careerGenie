"""Resume variations management routes."""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models.resume_variation import ResumeVariation
from models.user_enhanced import EnhancedUser
from services.resume_variation_service import ResumeVariationService
from utils.helpers import (
    format_error_response,
    serialize_document,
    serialize_documents,
    is_valid_object_id
)

logger = logging.getLogger(__name__)
resume_variations_bp = Blueprint('resume_variations', __name__, url_prefix='/api/resumes/variations')


@resume_variations_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_variations():
    """
    Generate resume variations for a user.

    Request body:
    {
        "numVariations": 3,  // optional, default 3
        "targetJobTypes": ["tech", "management"]  // optional
    }

    Returns:
        JSON response with created variations
    """
    try:
        user_id = get_jwt_identity()

        # Get user's base resume
        user = EnhancedUser.find_by_id(user_id)
        if not user:
            return jsonify(format_error_response("User not found", 404))

        resumes = user.get('resumes', {})
        base_resume = resumes.get('parsed')

        if not base_resume:
            return jsonify(format_error_response(
                "No resume found. Please upload a resume first.",
                400
            ))

        # Get request parameters
        data = request.get_json() or {}
        num_variations = data.get('numVariations', 3)
        target_job_types = data.get('targetJobTypes')

        # Validate num_variations
        if not isinstance(num_variations, int) or num_variations < 1 or num_variations > 5:
            return jsonify(format_error_response(
                "numVariations must be between 1 and 5",
                400
            ))

        # Generate variations
        logger.info(f"Generating {num_variations} resume variations for user {user_id}")
        service = ResumeVariationService()
        result = service.generate_variations(
            user_id=user_id,
            base_resume_data=base_resume,
            num_variations=num_variations,
            target_job_types=target_job_types
        )

        if not result['success']:
            return jsonify(format_error_response(result['error'], 500))

        return jsonify({
            'message': f"Successfully generated {result['count']} resume variations",
            'variations': result['variations']
        }), 201

    except Exception as e:
        logger.error(f"Error generating variations: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('', methods=['GET'])
@jwt_required()
def get_variations():
    """
    Get all resume variations for the current user.

    Query parameters:
    - jobType: Filter by job type (optional)
    - status: Filter by status (optional)

    Returns:
        JSON response with variations list
    """
    try:
        user_id = get_jwt_identity()

        job_type = request.args.get('jobType')
        status = request.args.get('status')

        variations = ResumeVariation.get_user_variations(
            user_id,
            job_type=job_type,
            status=status
        )

        return jsonify({
            'variations': serialize_documents(variations),
            'count': len(variations)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching variations: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('/<variation_id>', methods=['GET'])
@jwt_required()
def get_variation(variation_id):
    """
    Get a specific resume variation by ID.

    Args:
        variation_id: Variation ID

    Returns:
        JSON response with variation details
    """
    try:
        user_id = get_jwt_identity()

        if not is_valid_object_id(variation_id):
            return jsonify(format_error_response("Invalid variation ID", 400))

        variation = ResumeVariation.get_variation_by_id(variation_id)

        if not variation:
            return jsonify(format_error_response("Variation not found", 404))

        # Verify user owns this variation
        if str(variation['userId']) != user_id:
            return jsonify(format_error_response("Unauthorized", 403))

        return jsonify({
            'variation': serialize_document(variation)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching variation: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('/<variation_id>', methods=['DELETE'])
@jwt_required()
def delete_variation(variation_id):
    """
    Delete a resume variation.

    Args:
        variation_id: Variation ID

    Returns:
        JSON response confirming deletion
    """
    try:
        user_id = get_jwt_identity()

        if not is_valid_object_id(variation_id):
            return jsonify(format_error_response("Invalid variation ID", 400))

        success = ResumeVariation.delete_variation(variation_id, user_id)

        if not success:
            return jsonify(format_error_response(
                "Variation not found or unauthorized",
                404
            ))

        return jsonify({
            'message': 'Variation deleted successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error deleting variation: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('/<variation_id>/use', methods=['POST'])
@jwt_required()
def mark_variation_used(variation_id):
    """
    Mark a variation as used (increment usage counter).

    Args:
        variation_id: Variation ID

    Request body:
    {
        "successful": true  // optional, whether application was successful
    }

    Returns:
        JSON response confirming update
    """
    try:
        user_id = get_jwt_identity()

        if not is_valid_object_id(variation_id):
            return jsonify(format_error_response("Invalid variation ID", 400))

        # Verify ownership
        variation = ResumeVariation.get_variation_by_id(variation_id)
        if not variation or str(variation['userId']) != user_id:
            return jsonify(format_error_response("Unauthorized", 403))

        data = request.get_json() or {}
        successful = data.get('successful', False)

        success = ResumeVariation.increment_usage(variation_id, successful)

        if not success:
            return jsonify(format_error_response("Failed to update variation", 500))

        return jsonify({
            'message': 'Variation usage updated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error updating variation usage: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_variation_stats():
    """
    Get statistics about user's resume variations.

    Returns:
        JSON response with variation statistics
    """
    try:
        user_id = get_jwt_identity()

        stats = ResumeVariation.get_variation_stats(user_id)

        return jsonify({
            'stats': stats
        }), 200

    except Exception as e:
        logger.error(f"Error fetching variation stats: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('/find-best', methods=['POST'])
@jwt_required()
def find_best_variation():
    """
    Find the best resume variation for a specific job.

    Request body:
    {
        "jobId": "job_id_here",  // optional
        "jobData": {  // optional if jobId provided
            "title": "Software Engineer",
            "jobType": "tech",
            "description": "..."
        }
    }

    Returns:
        JSON response with best matching variation
    """
    try:
        user_id = get_jwt_identity()

        data = request.get_json()
        if not data:
            return jsonify(format_error_response("Request body required", 400))

        job_data = data.get('jobData')
        job_id = data.get('jobId')

        # If jobId provided, fetch job data
        if job_id and not job_data:
            from models.job import Job
            job = Job.find_by_id(job_id)
            if job:
                job_data = job

        if not job_data:
            return jsonify(format_error_response("Job data required", 400))

        # Find best variation
        best_variation = ResumeVariation.find_best_variation_for_job(user_id, job_data)

        if not best_variation:
            return jsonify({
                'message': 'No variations found. Consider generating some first.',
                'variation': None
            }), 200

        return jsonify({
            'message': 'Best variation found',
            'variation': serialize_document(best_variation)
        }), 200

    except Exception as e:
        logger.error(f"Error finding best variation: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))


@resume_variations_bp.route('/<variation_id>/export', methods=['POST'])
@jwt_required()
def export_variation():
    """
    Export a resume variation as PDF or DOCX.

    Args:
        variation_id: Variation ID

    Request body:
    {
        "format": "pdf",  // or "docx"
        "template": "modern"  // optional: "modern", "classic", "minimal"
    }

    Returns:
        File download (PDF or DOCX)
    """
    try:
        user_id = get_jwt_identity()

        if not is_valid_object_id(variation_id):
            return jsonify(format_error_response("Invalid variation ID", 400))

        # Get variation
        variation = ResumeVariation.get_variation_by_id(variation_id)

        if not variation:
            return jsonify(format_error_response("Variation not found", 404))

        # Verify user owns this variation
        if str(variation['userId']) != user_id:
            return jsonify(format_error_response("Unauthorized", 403))

        # Get request parameters
        data = request.get_json() or {}
        file_format = data.get('format', 'pdf').lower()
        template = data.get('template', 'modern')

        if file_format not in ['pdf', 'docx']:
            return jsonify(format_error_response("Format must be 'pdf' or 'docx'", 400))

        if template not in ['modern', 'classic', 'minimal']:
            return jsonify(format_error_response("Template must be 'modern', 'classic', or 'minimal'", 400))

        # Generate document using document generator service
        from services.document_generator import DocumentGenerator

        generator = DocumentGenerator()
        resume_data = variation.get('tailoredResume', {})

        try:
            # Generate the resume file
            file_path = generator.generate_resume(
                user_data=resume_data,
                template=template,
                format=file_format
            )

            # Send file
            from flask import send_file
            import os

            filename = f"resume_variation_{variation_id}.{file_format}"

            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf' if file_format == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        except Exception as gen_error:
            logger.error(f"Error generating document: {str(gen_error)}")
            return jsonify(format_error_response(f"Failed to generate document: {str(gen_error)}", 500))

    except Exception as e:
        logger.error(f"Error exporting variation: {str(e)}")
        return jsonify(format_error_response(f"Server error: {str(e)}", 500))
