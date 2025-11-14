"""Course routes - API endpoints for course management."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from services.course_aggregation import CourseAggregationService
from utils.helpers import format_success_response, format_error_response

logger = logging.getLogger(__name__)

# Create blueprint
courses_bp = Blueprint('courses', __name__, url_prefix='/api/courses')

# Initialize aggregation service
course_service = CourseAggregationService()


@courses_bp.route('/', methods=['GET'])
def get_courses():
    """
    Get courses with optional filters.

    Query Parameters:
        - search: Search query
        - category: Course category
        - level: Difficulty level
        - isFree: Filter for free courses (true/false)
        - provider: Specific provider (coursera, udemy)
        - sources: Comma-separated list of sources
        - page: Page number (default: 1)
        - pageSize: Results per page (default: 20)

    Returns:
        JSON response with course list
    """
    try:
        # Get query parameters
        search = request.args.get('search')
        category = request.args.get('category')
        level = request.args.get('level')
        is_free = request.args.get('isFree')
        provider = request.args.get('provider')
        sources_param = request.args.get('sources')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))

        # Parse boolean
        is_free_bool = None
        if is_free and is_free.lower() in ['true', '1', 'yes']:
            is_free_bool = True
        elif is_free and is_free.lower() in ['false', '0', 'no']:
            is_free_bool = False

        # Parse sources
        sources = None
        if sources_param:
            sources = [s.strip() for s in sources_param.split(',')]
        elif provider:
            sources = [provider]

        # Search courses
        result = course_service.search_courses(
            query=search,
            category=category,
            level=level,
            is_free=is_free_bool,
            sources=sources,
            page=page,
            page_size=page_size
        )

        return jsonify(format_success_response(
            data=result,
            message='Courses retrieved successfully'
        )), 200

    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        return jsonify(format_error_response(
            'Invalid parameter value',
            400
        )), 400

    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch courses',
            500
        )), 500


@courses_bp.route('/search', methods=['GET'])
def search_courses():
    """
    Search courses across platforms with advanced filters.

    Query Parameters:
        - keywords: Search keywords
        - skills: Comma-separated list of skills
        - category: Course category
        - level: Difficulty level
        - sources: Comma-separated list of sources
        - page: Page number (default: 1)
        - pageSize: Results per page (default: 20)

    Returns:
        JSON response with search results
    """
    try:
        keywords = request.args.get('keywords')
        skills = request.args.get('skills')
        category = request.args.get('category')
        level = request.args.get('level')
        sources_param = request.args.get('sources')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))

        # Build search query from keywords and skills
        query_parts = []
        if keywords:
            query_parts.append(keywords)
        if skills:
            query_parts.extend(skills.split(','))

        query = ' '.join(query_parts) if query_parts else None

        # Parse sources
        sources = None
        if sources_param:
            sources = [s.strip() for s in sources_param.split(',')]

        # Search courses
        result = course_service.search_courses(
            query=query,
            category=category,
            level=level,
            sources=sources,
            page=page,
            page_size=page_size
        )

        return jsonify(format_success_response(
            data=result,
            message='Search completed successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error searching courses: {str(e)}")
        return jsonify(format_error_response(
            'Failed to search courses',
            500
        )), 500


@courses_bp.route('/recommended', methods=['GET'])
@jwt_required()
def get_recommended_courses():
    """
    Get AI-recommended courses based on user's profile, job swipes, and skill gaps.

    Progressive recommendation logic:
    1. If user has skills -> recommend based on skills
    2. If no skills but has swiped jobs -> recommend based on swiped job skills
    3. If no swipes but has profile (job title/experience) -> recommend based on area of work
    4. Fallback -> generic popular skills

    Query Parameters:
        - limit: Number of courses to return (default: 20)

    Returns:
        JSON response with recommended courses
    """
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 20))

        # Get user's profile from database
        from models.user import User
        from models.swipe import Swipe
        from models.job import Job
        from bson import ObjectId

        user = User.find_by_id(user_id)
        skills = []
        recommendation_source = 'generic'

        if user and user.get('profile'):
            profile = user.get('profile', {})

            # 1. Try to get skills from user profile
            profile_skills = profile.get('skills', [])
            if profile_skills:
                skills = profile_skills
                recommendation_source = 'profile_skills'
                logger.info(f"Using profile skills for recommendations: {skills}")

            # 2. If no skills, try to infer from swiped jobs
            if not skills:
                liked_swipes = Swipe.get_user_swipes(user_id, action='like', limit=10)
                liked_swipes.extend(Swipe.get_user_swipes(user_id, action='superlike', limit=5))

                if liked_swipes:
                    # Extract skills from liked jobs
                    job_skills = set()
                    for swipe in liked_swipes:
                        job = Job.find_by_id(swipe.get('jobId'))
                        if job:
                            # Extract from job title
                            title = job.get('title', '').lower()

                            # Common job title keywords to skills mapping
                            # Supports ALL fields: tech, healthcare, business, education, trades, etc.
                            title_to_skills = {
                                # Tech/Programming
                                'python': ['Python', 'Django', 'Flask'],
                                'javascript': ['JavaScript', 'React', 'Node.js'],
                                'java': ['Java', 'Spring Boot', 'Maven'],
                                'data': ['Python', 'SQL', 'Data Analysis', 'Machine Learning'],
                                'frontend': ['HTML', 'CSS', 'JavaScript', 'React'],
                                'backend': ['Python', 'Node.js', 'SQL', 'REST APIs'],
                                'fullstack': ['JavaScript', 'React', 'Node.js', 'SQL'],
                                'devops': ['Docker', 'Kubernetes', 'AWS', 'CI/CD'],
                                'designer': ['Figma', 'Adobe XD', 'UI/UX Design'],
                                'product': ['Product Management', 'Agile', 'Analytics'],
                                'mobile': ['React Native', 'Flutter', 'Swift', 'Kotlin'],

                                # Healthcare
                                'nurse': ['Nursing', 'Patient Care', 'Medical Terminology', 'First Aid'],
                                'nursing': ['Nursing', 'Patient Care', 'Medical Terminology', 'First Aid'],
                                'doctor': ['Medicine', 'Diagnosis', 'Medical Ethics', 'Anatomy'],
                                'medical': ['Medical Terminology', 'Healthcare', 'Patient Care'],
                                'healthcare': ['Healthcare Management', 'Patient Care', 'Medical Ethics'],
                                'pharmacy': ['Pharmacology', 'Drug Interactions', 'Patient Counseling'],
                                'dental': ['Dentistry', 'Oral Health', 'Patient Care'],
                                'therapy': ['Physical Therapy', 'Occupational Therapy', 'Patient Care'],

                                # Business & Finance
                                'accountant': ['Accounting', 'Financial Reporting', 'Tax', 'Excel'],
                                'accounting': ['Accounting', 'Financial Reporting', 'Tax', 'Excel'],
                                'finance': ['Financial Analysis', 'Budgeting', 'Investment', 'Excel'],
                                'business': ['Business Management', 'Strategy', 'Operations'],
                                'management': ['Management', 'Leadership', 'Team Building'],
                                'sales': ['Sales Techniques', 'Negotiation', 'CRM', 'Communication'],
                                'marketing': ['Digital Marketing', 'SEO', 'Social Media', 'Content Marketing'],
                                'hr': ['Human Resources', 'Recruitment', 'Employee Relations'],
                                'operations': ['Operations Management', 'Process Improvement', 'Logistics'],

                                # Education
                                'teacher': ['Teaching', 'Classroom Management', 'Lesson Planning', 'Assessment'],
                                'teaching': ['Teaching', 'Classroom Management', 'Lesson Planning', 'Assessment'],
                                'education': ['Educational Psychology', 'Curriculum Development', 'Teaching Methods'],
                                'tutor': ['Tutoring', 'Subject Expertise', 'Student Engagement'],
                                'professor': ['Teaching', 'Research', 'Academic Writing', 'Mentoring'],

                                # Trades & Services
                                'electrician': ['Electrical Wiring', 'Safety Codes', 'Troubleshooting'],
                                'plumber': ['Plumbing', 'Pipe Fitting', 'Water Systems'],
                                'mechanic': ['Automotive Repair', 'Diagnostics', 'Engine Maintenance'],
                                'carpenter': ['Carpentry', 'Blueprint Reading', 'Construction'],
                                'construction': ['Construction Management', 'Safety', 'Project Planning'],
                                'hvac': ['HVAC Systems', 'Climate Control', 'Maintenance'],

                                # Creative & Arts
                                'graphic': ['Graphic Design', 'Adobe Creative Suite', 'Branding'],
                                'photographer': ['Photography', 'Photo Editing', 'Composition'],
                                'video': ['Video Editing', 'Adobe Premiere', 'Cinematography'],
                                'writer': ['Creative Writing', 'Copywriting', 'Editing'],
                                'artist': ['Art', 'Drawing', 'Digital Art', 'Illustration'],

                                # Customer Service & Retail
                                'customer': ['Customer Service', 'Communication', 'Problem Solving'],
                                'retail': ['Retail Management', 'Sales', 'Customer Service', 'Inventory'],
                                'hospitality': ['Hospitality Management', 'Customer Service', 'Event Planning'],
                                'chef': ['Culinary Arts', 'Food Safety', 'Menu Planning', 'Cooking'],
                                'cook': ['Cooking', 'Food Preparation', 'Kitchen Management'],
                            }

                            for keyword, skill_list in title_to_skills.items():
                                if keyword in title:
                                    job_skills.update(skill_list)

                    if job_skills:
                        skills = list(job_skills)[:10]  # Limit to top 10
                        recommendation_source = 'liked_jobs'
                        logger.info(f"Using skills from liked jobs: {skills}")

            # 3. If still no skills, use profile metadata (job title, experience)
            if not skills:
                job_title = profile.get('jobTitle', '').lower()
                experience = profile.get('experience', '').lower()

                # Map experience level to appropriate skills
                # Supports ALL fields: tech, healthcare, business, education, trades, etc.
                area_skills = []

                # Tech & Engineering
                if any(word in job_title or word in experience for word in ['software', 'developer', 'engineer', 'programmer']):
                    area_skills = ['Python', 'JavaScript', 'Git', 'SQL', 'REST APIs']
                elif any(word in job_title or word in experience for word in ['data', 'analyst', 'scientist']):
                    area_skills = ['Python', 'SQL', 'Data Analysis', 'Excel', 'Tableau']
                elif any(word in job_title or word in experience for word in ['design', 'ux', 'ui']):
                    area_skills = ['Figma', 'Adobe XD', 'UI/UX Design', 'Prototyping']
                elif any(word in job_title or word in experience for word in ['product', 'manager']):
                    area_skills = ['Product Management', 'Agile', 'Analytics', 'User Research']

                # Business & Marketing
                elif any(word in job_title or word in experience for word in ['marketing', 'digital']):
                    area_skills = ['Digital Marketing', 'SEO', 'Google Analytics', 'Content Marketing']
                elif any(word in job_title or word in experience for word in ['sales', 'business']):
                    area_skills = ['Sales', 'CRM', 'Communication', 'Negotiation']
                elif any(word in job_title or word in experience for word in ['account', 'finance', 'financial']):
                    area_skills = ['Accounting', 'Financial Analysis', 'Excel', 'Budgeting']
                elif any(word in job_title or word in experience for word in ['hr', 'human resources', 'recruitment']):
                    area_skills = ['Human Resources', 'Recruitment', 'Employee Relations', 'Communication']

                # Healthcare
                elif any(word in job_title or word in experience for word in ['nurse', 'nursing', 'medical']):
                    area_skills = ['Nursing', 'Patient Care', 'Medical Terminology', 'First Aid']
                elif any(word in job_title or word in experience for word in ['doctor', 'physician', 'healthcare']):
                    area_skills = ['Medicine', 'Patient Care', 'Medical Ethics', 'Healthcare Management']
                elif any(word in job_title or word in experience for word in ['pharmacy', 'pharmacist']):
                    area_skills = ['Pharmacology', 'Drug Interactions', 'Patient Counseling']
                elif any(word in job_title or word in experience for word in ['therapy', 'therapist', 'physical therapy']):
                    area_skills = ['Physical Therapy', 'Patient Care', 'Rehabilitation']

                # Education
                elif any(word in job_title or word in experience for word in ['teacher', 'teaching', 'educator']):
                    area_skills = ['Teaching', 'Classroom Management', 'Lesson Planning', 'Assessment']
                elif any(word in job_title or word in experience for word in ['tutor', 'tutoring']):
                    area_skills = ['Tutoring', 'Subject Expertise', 'Student Engagement']
                elif any(word in job_title or word in experience for word in ['professor', 'academic', 'lecturer']):
                    area_skills = ['Teaching', 'Research', 'Academic Writing', 'Mentoring']

                # Trades & Construction
                elif any(word in job_title or word in experience for word in ['electrician', 'electrical']):
                    area_skills = ['Electrical Wiring', 'Safety Codes', 'Troubleshooting']
                elif any(word in job_title or word in experience for word in ['plumber', 'plumbing']):
                    area_skills = ['Plumbing', 'Pipe Fitting', 'Water Systems']
                elif any(word in job_title or word in experience for word in ['mechanic', 'automotive']):
                    area_skills = ['Automotive Repair', 'Diagnostics', 'Engine Maintenance']
                elif any(word in job_title or word in experience for word in ['carpenter', 'construction', 'builder']):
                    area_skills = ['Carpentry', 'Construction', 'Blueprint Reading']

                # Creative & Arts
                elif any(word in job_title or word in experience for word in ['graphic', 'designer']):
                    area_skills = ['Graphic Design', 'Adobe Creative Suite', 'Branding']
                elif any(word in job_title or word in experience for word in ['photographer', 'photography']):
                    area_skills = ['Photography', 'Photo Editing', 'Composition']
                elif any(word in job_title or word in experience for word in ['video', 'videographer', 'editor']):
                    area_skills = ['Video Editing', 'Adobe Premiere', 'Cinematography']
                elif any(word in job_title or word in experience for word in ['writer', 'content', 'copywriter']):
                    area_skills = ['Creative Writing', 'Copywriting', 'Editing', 'Content Marketing']

                # Customer Service & Hospitality
                elif any(word in job_title or word in experience for word in ['customer service', 'support', 'customer']):
                    area_skills = ['Customer Service', 'Communication', 'Problem Solving']
                elif any(word in job_title or word in experience for word in ['retail', 'store', 'cashier']):
                    area_skills = ['Retail Management', 'Sales', 'Customer Service']
                elif any(word in job_title or word in experience for word in ['hospitality', 'hotel', 'restaurant']):
                    area_skills = ['Hospitality Management', 'Customer Service', 'Event Planning']
                elif any(word in job_title or word in experience for word in ['chef', 'cook', 'culinary']):
                    area_skills = ['Culinary Arts', 'Food Safety', 'Cooking', 'Menu Planning']

                if area_skills:
                    skills = area_skills
                    recommendation_source = 'profile_area'
                    logger.info(f"Using skills from profile area ({job_title}): {skills}")

        # 4. Fallback to generic popular skills (diverse across ALL fields)
        if not skills:
            skills = [
                'Communication',           # Universal skill
                'Leadership',              # Universal skill
                'Project Management',      # Business/Tech
                'Data Analysis',           # Business/Tech
                'Customer Service'         # Service industries
            ]
            recommendation_source = 'generic'
            logger.info("Using generic skill recommendations (multi-field)")

        result = course_service.get_recommended_courses(
            skills=skills,
            limit=limit
        )

        # Add metadata about recommendation source
        result['recommendation_source'] = recommendation_source
        result['skills_used'] = skills

        return jsonify(format_success_response(
            data=result,
            message='Recommendations retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify(format_error_response(
            'Failed to get recommendations',
            500
        )), 500


@courses_bp.route('/<course_id>', methods=['GET'])
def get_course_details(course_id):
    """
    Get detailed information about a specific course.

    Args:
        course_id: Course ID with source prefix (e.g., 'coursera_123')

    Returns:
        JSON response with course details
    """
    try:
        course = course_service.get_course_details(course_id)

        if not course:
            return jsonify(format_error_response(
                'Course not found',
                404
            )), 404

        return jsonify(format_success_response(
            data={'course': course},
            message='Course details retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching course details: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch course details',
            500
        )), 500


@courses_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get available course categories from all sources.

    Returns:
        JSON response with categories
    """
    try:
        categories = course_service.get_all_categories()

        return jsonify(format_success_response(
            data={'categories': categories},
            message='Categories retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch categories',
            500
        )), 500


@courses_bp.route('/providers', methods=['GET'])
def get_providers():
    """
    Get available course providers.

    Returns:
        JSON response with providers
    """
    try:
        providers = [
            {
                'id': 'coursera',
                'name': 'Coursera',
                'logo': 'https://upload.wikimedia.org/wikipedia/commons/e/e5/Coursera_logo.PNG',
                'description': 'Online courses from top universities'
            },
            {
                'id': 'udemy',
                'name': 'Udemy',
                'logo': 'https://www.udemy.com/staticx/udemy/images/v7/logo-udemy.svg',
                'description': 'Online learning and teaching marketplace'
            }
        ]

        return jsonify(format_success_response(
            data={'providers': providers},
            message='Providers retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching providers: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch providers',
            500
        )), 500


@courses_bp.route('/featured', methods=['GET'])
def get_featured_courses():
    """
    Get featured/popular courses from all sources.

    Query Parameters:
        - limit: Number of courses to return (default: 20)

    Returns:
        JSON response with featured courses
    """
    try:
        limit = int(request.args.get('limit', 20))

        result = course_service.get_featured_courses(limit=limit)

        return jsonify(format_success_response(
            data=result,
            message='Featured courses retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching featured courses: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch featured courses',
            500
        )), 500


@courses_bp.route('/ads', methods=['GET'])
def get_course_ads():
    """
    Get course advertisement configuration.

    Returns:
        JSON response with ad configuration
    """
    try:
        # Return empty ads for now
        # TODO: Implement Google AdSense integration
        ads = []

        return jsonify(format_success_response(
            data={'ads': ads},
            message='Ads retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching ads: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch ads',
            500
        )), 500


@courses_bp.route('/ads-config', methods=['GET'])
def get_ads_config():
    """
    Get AdSense configuration for courses page.

    Returns:
        JSON response with ads configuration
    """
    try:
        # Return empty config for now - ads are disabled
        config = {
            'enabled': False,
            'publisherId': None,
            'adSlots': []
        }

        return jsonify(format_success_response(
            data=config,
            message='Ads config retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching ads config: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch ads config',
            500
        )), 500


@courses_bp.route('/skill-gaps', methods=['GET'])
@jwt_required()
def get_skill_gaps():
    """
    Get user's skill gap analysis.

    Returns:
        JSON response with skill gaps
    """
    try:
        user_id = get_jwt_identity()

        # Get user's skills and analyze gaps
        from models.user import User
        user = User.find_by_id(user_id)
        user_skills = []

        if user and user.get('profile'):
            user_skills = user.get('profile', {}).get('skills', [])

        # Common in-demand skills for analysis
        high_demand_skills = [
            'Python', 'JavaScript', 'React', 'Node.js', 'Docker',
            'Kubernetes', 'AWS', 'Machine Learning', 'Data Science',
            'TypeScript', 'Go', 'Rust', 'DevOps', 'CI/CD'
        ]

        # Calculate skill gaps
        user_skills_lower = [s.lower() for s in user_skills]
        gaps = [skill for skill in high_demand_skills
                if skill.lower() not in user_skills_lower]

        # Categorize by priority (simple heuristic)
        high_priority = gaps[:min(3, len(gaps))]
        medium_priority = gaps[3:min(6, len(gaps))] if len(gaps) > 3 else []
        low_priority = gaps[6:] if len(gaps) > 6 else []

        skill_gaps = {
            'userSkills': user_skills,
            'skillGaps': {
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority
            },
            'skillPriorities': high_priority + medium_priority,
            'aiRecommendations': high_priority[:5] if high_priority else []
        }

        return jsonify(format_success_response(
            data=skill_gaps,
            message='Skill gaps retrieved successfully'
        )), 200

    except Exception as e:
        logger.error(f"Error fetching skill gaps: {str(e)}")
        return jsonify(format_error_response(
            'Failed to fetch skill gaps',
            500
        )), 500


@courses_bp.route('/enrollments', methods=['GET', 'POST'])
@jwt_required()
def handle_enrollments():
    """
    Get or create course enrollments.

    GET: Get user's course enrollments
    POST: Enroll in a course

    Returns:
        JSON response with enrollment data
    """
    try:
        user_id = get_jwt_identity()

        if request.method == 'GET':
            # Get enrollments from database
            from config.database import get_database
            db = get_database()
            enrollments_collection = db['course_enrollments']

            from bson import ObjectId
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)

            enrollments_cursor = enrollments_collection.find({'userId': user_id})
            enrollments = []

            for enrollment in enrollments_cursor:
                enrollments.append({
                    'id': str(enrollment['_id']),
                    'courseId': enrollment.get('courseId'),
                    'userId': str(enrollment.get('userId')),
                    'status': enrollment.get('status', 'active'),
                    'progress': enrollment.get('progress', 0),
                    'enrolledAt': enrollment.get('enrolledAt').isoformat() if enrollment.get('enrolledAt') else None
                })

            return jsonify(format_success_response(
                data={'enrollments': enrollments, 'total': len(enrollments)},
                message='Enrollments retrieved successfully'
            )), 200

        elif request.method == 'POST':
            data = request.get_json()

            if not data or 'courseId' not in data:
                return jsonify(format_error_response(
                    'courseId is required',
                    400
                )), 400

            # Save enrollment to database
            from config.database import get_database
            from bson import ObjectId
            from datetime import datetime

            db = get_database()
            enrollments_collection = db['course_enrollments']

            if isinstance(user_id, str):
                user_id_obj = ObjectId(user_id)
            else:
                user_id_obj = user_id

            # Check if already enrolled
            existing = enrollments_collection.find_one({
                'userId': user_id_obj,
                'courseId': data['courseId']
            })

            if existing:
                return jsonify(format_error_response(
                    'Already enrolled in this course',
                    409
                )), 409

            enrollment_data = {
                'courseId': data['courseId'],
                'userId': user_id_obj,
                'status': 'active',
                'progress': 0,
                'enrolledAt': datetime.utcnow()
            }

            result = enrollments_collection.insert_one(enrollment_data)

            enrollment = {
                'id': str(result.inserted_id),
                'courseId': data['courseId'],
                'userId': user_id,
                'status': 'active',
                'progress': 0,
                'enrolledAt': datetime.utcnow().isoformat()
            }

            return jsonify(format_success_response(
                data={'enrollment': enrollment},
                message='Enrolled successfully'
            )), 201

    except Exception as e:
        logger.error(f"Error handling enrollments: {str(e)}")
        return jsonify(format_error_response(
            'Failed to handle enrollment',
            500
        )), 500
