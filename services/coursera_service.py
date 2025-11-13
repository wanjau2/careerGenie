"""Coursera API Service - Fetch courses from Coursera Catalog API."""
import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CourseraService:
    """Service for interacting with Coursera Catalog API."""

    BASE_URL = "https://api.coursera.org/api"
    CATALOG_URL = "https://api.coursera.org/api/courses.v1"

    def __init__(self):
        """Initialize Coursera service."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CareerGenie/1.0'
        })

    def search_courses(
        self,
        query: Optional[str] = None,
        limit: int = 20,
        start: int = 0,
        fields: Optional[str] = None
    ) -> Dict:
        """
        Search courses on Coursera.

        Args:
            query: Search query string
            limit: Number of results to return (max 100)
            start: Starting index for pagination
            fields: Comma-separated list of fields to include

        Returns:
            Dictionary containing course results
        """
        try:
            params = {
                'start': start,
                'limit': min(limit, 100)  # Coursera max is 100
            }

            if query:
                params['q'] = 'search'
                params['query'] = query

            # Include common fields
            if not fields:
                fields = 'id,name,slug,description,workload,photoUrl,partnerIds,primaryLanguages,subtitleLanguages,partners.v1(name,logo)'

            params['fields'] = fields

            response = self.session.get(
                self.CATALOG_URL,
                params=params,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            return self._format_response(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Coursera API error: {str(e)}")
            return {
                'courses': [],
                'total': 0,
                'error': str(e)
            }

    def get_course_details(self, course_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific course.

        Args:
            course_id: Coursera course ID

        Returns:
            Dictionary containing course details
        """
        try:
            url = f"{self.CATALOG_URL}/{course_id}"
            params = {
                'fields': 'id,name,slug,description,workload,photoUrl,partnerIds,primaryLanguages,subtitleLanguages,partners.v1(name,logo)'
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'elements' in data and len(data['elements']) > 0:
                return self._format_course(data['elements'][0])

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Coursera course details error: {str(e)}")
            return None

    def _format_response(self, data: Dict) -> Dict:
        """
        Format Coursera API response to standard format.

        Args:
            data: Raw API response

        Returns:
            Formatted response dictionary
        """
        courses = []

        if 'elements' in data:
            for course in data['elements']:
                formatted_course = self._format_course(course)
                if formatted_course:
                    courses.append(formatted_course)

        return {
            'courses': courses,
            'total': len(courses),
            'source': 'coursera'
        }

    def _format_course(self, course: Dict) -> Optional[Dict]:
        """
        Format a single Coursera course to standard format.

        Args:
            course: Raw course data from API

        Returns:
            Formatted course dictionary
        """
        try:
            course_id = course.get('id', '')
            slug = course.get('slug', course_id)

            # Extract partner information
            partner_name = 'Coursera'
            if 'partners' in course and len(course['partners']) > 0:
                partner_name = course['partners'][0].get('name', 'Coursera')

            # Build course URL
            course_url = f"https://www.coursera.org/learn/{slug}"

            # Extract thumbnail
            thumbnail = course.get('photoUrl', '')
            if not thumbnail:
                thumbnail = 'https://d3njjcbhbojbot.cloudfront.net/api/utilities/v1/imageproxy/https://coursera-course-photos.s3.amazonaws.com/default.png'

            # Extract workload
            workload = course.get('workload', '4-6 weeks')

            # Extract languages
            languages = course.get('primaryLanguages', [])
            language = languages[0] if languages else 'English'

            # Description
            description = course.get('description', 'No description available')

            # Format the course object
            formatted = {
                'id': f"coursera_{course_id}",
                'title': course.get('name', 'Untitled Course'),
                'description': description,
                'provider': 'Coursera',
                'providerLogo': 'https://upload.wikimedia.org/wikipedia/commons/e/e5/Coursera_logo.PNG',
                'thumbnailImage': thumbnail,
                'duration': workload,
                'level': 'Intermediate',  # Coursera doesn't always provide this
                'rating': 4.5,  # Default rating
                'reviewCount': 0,
                'learningOutcomes': [],
                'registrationUrl': course_url,
                'isFree': True,  # Many Coursera courses are free to audit
                'price': None,
                'category': '',
                'skills': [],
                'certificateProvider': partner_name,
                'source': 'coursera',
                'language': language
            }

            return formatted

        except Exception as e:
            logger.error(f"Error formatting Coursera course: {str(e)}")
            return None

    def get_categories(self) -> List[str]:
        """
        Get available course categories.

        Returns:
            List of category names
        """
        # Common Coursera categories
        return [
            'Computer Science',
            'Business',
            'Data Science',
            'Information Technology',
            'Language Learning',
            'Health',
            'Personal Development',
            'Physical Science and Engineering',
            'Social Sciences',
            'Arts and Humanities',
            'Math and Logic'
        ]
