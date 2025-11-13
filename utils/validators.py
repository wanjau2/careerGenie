"""Input validation utilities."""
import re
from email_validator import validate_email, EmailNotValidError
from werkzeug.datastructures import FileStorage


def validate_email_address(email):
    """
    Validate email address format.

    Args:
        email: Email address string

    Returns:
        tuple: (is_valid, normalized_email_or_error_message)
    """
    try:
        valid = validate_email(email, check_deliverability=False)
        return True, valid.normalized
    except EmailNotValidError as e:
        return False, str(e)


def validate_password(password):
    """
    Validate password strength.

    Requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit

    Args:
        password: Password string

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, None


def validate_phone_number(phone):
    """
    Validate phone number format.

    Args:
        phone: Phone number string

    Returns:
        tuple: (is_valid, error_message)
    """
    if not phone:
        return True, None  # Phone is optional

    # Remove common formatting characters
    clean_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)

    # Check if it's a valid format (10-15 digits, optionally starting with +)
    if re.match(r'^\+?\d{10,15}$', clean_phone):
        return True, None

    return False, "Invalid phone number format"


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present.

    Args:
        data: Dictionary of data
        required_fields: List of required field names

    Returns:
        tuple: (is_valid, missing_fields_or_none)
    """
    missing = [field for field in required_fields if field not in data or not data[field]]

    if missing:
        return False, missing

    return True, None


def validate_file_type(file, allowed_extensions):
    """
    Validate file type by extension.

    Args:
        file: FileStorage object or filename string
        allowed_extensions: Set of allowed extensions

    Returns:
        bool: True if valid, False otherwise
    """
    if isinstance(file, FileStorage):
        filename = file.filename
    else:
        filename = file

    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def validate_salary_range(min_salary, max_salary):
    """
    Validate salary range.

    Args:
        min_salary: Minimum salary
        max_salary: Maximum salary

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        min_sal = float(min_salary) if min_salary is not None else 0
        max_sal = float(max_salary) if max_salary is not None else float('inf')

        if min_sal < 0 or max_sal < 0:
            return False, "Salary values must be non-negative"

        if min_sal > max_sal:
            return False, "Minimum salary cannot be greater than maximum salary"

        return True, None
    except (ValueError, TypeError):
        return False, "Invalid salary values"


def validate_location(location_data):
    """
    Validate location data.

    Args:
        location_data: Dictionary with city, state, coordinates

    Returns:
        tuple: (is_valid, error_message)
    """
    if not location_data:
        return False, "Location data is required"

    if 'city' not in location_data or not location_data['city']:
        return False, "City is required"

    if 'state' not in location_data or not location_data['state']:
        return False, "State is required"

    # Validate coordinates if provided
    if 'coordinates' in location_data:
        coords = location_data['coordinates']
        if not isinstance(coords, list) or len(coords) != 2:
            return False, "Coordinates must be [latitude, longitude]"

        lat, lon = coords
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False, "Invalid coordinate values"

    return True, None


def sanitize_string(text, max_length=None):
    """
    Sanitize string input.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Remove leading/trailing whitespace
    sanitized = text.strip()

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_pagination_params(page, page_size, max_page_size=100):
    """
    Validate pagination parameters.

    Args:
        page: Page number
        page_size: Number of items per page
        max_page_size: Maximum allowed page size

    Returns:
        tuple: (is_valid, (validated_page, validated_page_size), error_message)
    """
    try:
        validated_page = max(1, int(page))
        validated_page_size = max(1, min(int(page_size), max_page_size))
        return True, (validated_page, validated_page_size), None
    except (ValueError, TypeError):
        return False, None, "Invalid pagination parameters"


def validate_user_profile_data(profile_data):
    """
    Validate user profile data.

    Args:
        profile_data: Dictionary of profile data

    Returns:
        tuple: (is_valid, error_message)
    """
    errors = []

    # Validate name fields
    if 'firstName' in profile_data:
        first_name = sanitize_string(profile_data['firstName'], 50)
        if not first_name:
            errors.append("First name cannot be empty")
        elif len(first_name) < 2:
            errors.append("First name must be at least 2 characters")

    if 'lastName' in profile_data:
        last_name = sanitize_string(profile_data['lastName'], 50)
        if not last_name:
            errors.append("Last name cannot be empty")
        elif len(last_name) < 2:
            errors.append("Last name must be at least 2 characters")

    # Validate phone
    if 'phone' in profile_data:
        is_valid, error = validate_phone_number(profile_data['phone'])
        if not is_valid:
            errors.append(error)

    # Validate salary expectations
    if 'expectedSalary' in profile_data:
        salary = profile_data['expectedSalary']
        if isinstance(salary, dict):
            is_valid, error = validate_salary_range(
                salary.get('min'),
                salary.get('max')
            )
            if not is_valid:
                errors.append(f"Salary: {error}")

    if errors:
        return False, "; ".join(errors)

    return True, None
