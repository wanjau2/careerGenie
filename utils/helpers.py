"""Helper utility functions."""
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
import string


def generate_random_token(length=32):
    """
    Generate a random secure token.

    Args:
        length: Length of the token

    Returns:
        str: Random token
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def serialize_document(document):
    """
    Serialize MongoDB document to JSON-friendly format.

    Args:
        document: MongoDB document

    Returns:
        dict: Serialized document
    """
    if not document:
        return None

    serialized = {}
    for key, value in document.items():
        if isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_document(value)
        elif isinstance(value, list):
            serialized[key] = [
                serialize_document(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            serialized[key] = value

    # Convert _id to id for cleaner API responses
    if '_id' in serialized:
        serialized['id'] = serialized.pop('_id')

    return serialized


def serialize_documents(documents):
    """
    Serialize list of MongoDB documents.

    Args:
        documents: List of MongoDB documents

    Returns:
        list: List of serialized documents
    """
    return [serialize_document(doc) for doc in documents]


def calculate_skip_limit(page, page_size):
    """
    Calculate skip and limit for pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        tuple: (skip, limit)
    """
    skip = (page - 1) * page_size
    return skip, page_size


def get_pagination_metadata(total_count, page, page_size):
    """
    Generate pagination metadata.

    Args:
        total_count: Total number of items
        page: Current page number
        page_size: Items per page

    Returns:
        dict: Pagination metadata
    """
    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0

    return {
        'page': page,
        'pageSize': page_size,
        'totalItems': total_count,
        'totalPages': total_pages,
        'hasNext': page < total_pages,
        'hasPrevious': page > 1
    }


def calculate_swipe_reset_date():
    """
    Calculate next swipe reset date (next day at midnight UTC).

    Returns:
        datetime: Reset date
    """
    tomorrow = datetime.utcnow() + timedelta(days=1)
    return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)


def is_swipe_limit_reached(swipes_used, swipe_limit):
    """
    Check if swipe limit has been reached.

    Args:
        swipes_used: Number of swipes used
        swipe_limit: Maximum swipes allowed (-1 for unlimited)

    Returns:
        bool: True if limit reached
    """
    if swipe_limit == -1:
        return False  # Unlimited

    return swipes_used >= swipe_limit


def should_reset_swipes(reset_date):
    """
    Check if swipes should be reset based on reset date.

    Args:
        reset_date: Scheduled reset date

    Returns:
        bool: True if should reset
    """
    if not reset_date:
        return True

    return datetime.utcnow() >= reset_date


def calculate_match_score(user_preferences, job_data):
    """
    Calculate match score between user preferences and job.

    Args:
        user_preferences: User preference data
        job_data: Job data

    Returns:
        float: Match score (0.0 to 1.0)
    """
    score = 0.0
    weights = {
        'job_type': 0.25,
        'industry': 0.20,
        'salary': 0.30,
        'location': 0.15,
        'skills': 0.10
    }

    # Job type match
    if user_preferences.get('jobTypes'):
        if job_data.get('employment', {}).get('type') in user_preferences['jobTypes']:
            score += weights['job_type']

    # Industry match
    if user_preferences.get('industries'):
        if job_data.get('company', {}).get('industry') in user_preferences['industries']:
            score += weights['industry']

    # Salary match
    user_salary = user_preferences.get('expectedSalary', {})
    job_salary = job_data.get('salary', {})
    if user_salary and job_salary:
        user_min = user_salary.get('min', 0)
        user_max = user_salary.get('max', float('inf'))
        job_min = job_salary.get('min', 0)
        job_max = job_salary.get('max', 0)

        # Check if salary ranges overlap
        if job_max >= user_min and job_min <= user_max:
            # Calculate overlap percentage
            overlap_min = max(user_min, job_min)
            overlap_max = min(user_max, job_max)
            overlap_pct = (overlap_max - overlap_min) / (user_max - user_min) if user_max > user_min else 1.0
            score += weights['salary'] * overlap_pct

    # Location match (simple city/state match for now)
    user_location = user_preferences.get('location', {})
    job_location = job_data.get('location', {})
    if user_location and job_location:
        if (user_location.get('city') == job_location.get('city') and
            user_location.get('state') == job_location.get('state')):
            score += weights['location']
        elif job_location.get('remote'):
            score += weights['location'] * 0.8  # Remote is almost as good

    # Skills match
    user_skills = set(user_preferences.get('skills', []))
    job_requirements = set(job_data.get('requirements', []))
    if user_skills and job_requirements:
        matching_skills = user_skills.intersection(job_requirements)
        skill_match_pct = len(matching_skills) / len(job_requirements) if job_requirements else 0
        score += weights['skills'] * skill_match_pct

    return min(score, 1.0)  # Cap at 1.0


def format_error_response(message, status_code=400, errors=None):
    """
    Format error response.

    Args:
        message: Error message
        status_code: HTTP status code
        errors: Additional error details

    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'error': message,
        'status': status_code
    }

    if errors:
        response['details'] = errors

    return response, status_code


def format_success_response(data=None, message=None, meta=None):
    """
    Format success response.

    Args:
        data: Response data
        message: Success message
        meta: Additional metadata

    Returns:
        dict: Response dictionary
    """
    response = {}

    if message:
        response['message'] = message

    if data is not None:
        response['data'] = data

    if meta:
        response['meta'] = meta

    return response


def is_valid_object_id(id_string):
    """
    Check if string is a valid MongoDB ObjectId.

    Args:
        id_string: String to check

    Returns:
        bool: True if valid ObjectId
    """
    try:
        ObjectId(id_string)
        return True
    except Exception:
        return False


def get_file_extension(filename):
    """
    Get file extension from filename.

    Args:
        filename: File name

    Returns:
        str: File extension (lowercase)
    """
    if not filename or '.' not in filename:
        return ''

    return filename.rsplit('.', 1)[1].lower()


def generate_unique_filename(original_filename, user_id, prefix=''):
    """
    Generate unique filename for uploads.

    Args:
        original_filename: Original file name
        user_id: User ID
        prefix: Optional prefix

    Returns:
        str: Unique filename
    """
    extension = get_file_extension(original_filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    random_string = generate_random_token(8)

    filename_parts = [prefix, str(user_id), timestamp, random_string]
    filename_parts = [part for part in filename_parts if part]  # Remove empty parts

    base_name = '_'.join(filename_parts)
    return f"{base_name}.{extension}" if extension else base_name
