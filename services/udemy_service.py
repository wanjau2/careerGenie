"""Udemy API Service - Fetch courses from Udemy via RapidAPI."""
import requests
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class UdemyService:
    """Service for interacting with Udemy via RapidAPI."""

    # Using Udemy Paid Courses for Free API from RapidAPI
    BASE_URL = "https://udemy-paid-courses-for-free-api.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Udemy service.

        Args:
            api_key: RapidAPI key for Udemy API
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'udemy-paid-courses-for-free-api.p.rapidapi.com'
            })

    def search_courses(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        price: Optional[str] = None
    ) -> Dict:
        """
        Search courses on Udemy.

        Args:
            query: Search query string
            category: Course category
            page: Page number for pagination
            page_size: Number of results per page
            price: Filter by price ('free' or 'paid')

        Returns:
            Dictionary containing course results
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for Udemy")
            return {
                'courses': [],
                'total': 0,
                'error': 'RapidAPI key not configured'
            }

        try:
            # Build search URL
            url = f"{self.BASE_URL}/rapidapi/courses/search"

            # Only add parameters that have values
            params = {
                'page': page,
                'page_size': min(page_size, 50)  # Limit to reasonable size
            }

            # The API requires at least a query parameter
            if query:
                params['query'] = query
            else:
                # If no query provided, search for popular topics
                params['query'] = 'programming'

            if category:
                params['category'] = category

            # Note: This API only returns free courses, so price param not needed

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return self._format_response(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Udemy API error: {str(e)}")
            return {
                'courses': [],
                'total': 0,
                'error': str(e)
            }

    def get_course_details(self, course_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific course.

        Args:
            course_id: Udemy course ID

        Returns:
            Dictionary containing course details
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for Udemy")
            return None

        try:
            url = f"{self.BASE_URL}/courses/{course_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            return self._format_course(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Udemy course details error: {str(e)}")
            return None

    def get_featured_courses(self, limit: int = 20) -> Dict:
        """
        Get featured/popular Udemy courses.

        Args:
            limit: Number of courses to return

        Returns:
            Dictionary containing course results
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for Udemy")
            return {
                'courses': [],
                'total': 0,
                'error': 'RapidAPI key not configured'
            }

        try:
            # Get popular courses
            url = f"{self.BASE_URL}/courses"
            params = {
                'page': 1,
                'page_size': limit,
                'ordering': 'most-reviewed'
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return self._format_response(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Udemy featured courses error: {str(e)}")
            return {
                'courses': [],
                'total': 0,
                'error': str(e)
            }

    def _format_response(self, data: Dict) -> Dict:
        """
        Format Udemy API response to standard format.

        Args:
            data: Raw API response

        Returns:
            Formatted response dictionary
        """
        courses = []

        # Handle different response formats
        # New API returns 'courses' key
        results = data.get('courses', data.get('results', []))
        if not results and isinstance(data, list):
            results = data

        for course in results:
            formatted_course = self._format_course(course)
            if formatted_course:
                courses.append(formatted_course)

        return {
            'courses': courses,
            'total': len(courses),
            'source': 'udemy'
        }

    def _format_course(self, course: Dict) -> Optional[Dict]:
        """
        Format a single Udemy course to standard format.

        Args:
            course: Raw course data from API

        Returns:
            Formatted course dictionary
        """
        try:
            # Extract course ID from URL or use name as fallback
            url = course.get('url', course.get('clean_url', ''))
            course_id = url.split('/')[-2] if url else course.get('name', '').replace(' ', '-')

            # Extract price information
            sale_price = float(course.get('sale_price_usd', 0))
            actual_price = float(course.get('actual_price_usd', 0))
            is_free = sale_price == 0.0
            price = f"${actual_price}" if actual_price > 0 else None

            # Default rating (API doesn't provide ratings)
            rating = 4.5

            # Extract image
            image = course.get('image', '')

            # Extract instructor name (not in API response, use default)
            instructor = 'Udemy Instructor'

            # Extract level (not in API response, use default)
            level = 'All Levels'

            # Extract headline/description
            description = course.get('description', 'No description available')
            # Clean up description
            if len(description) > 200:
                description = description[:200] + '...'

            # Extract category
            category = course.get('category', 'General')

            # Extract sale end date
            sale_end = course.get('sale_end', '')

            # Format the course object
            formatted = {
                'id': f"udemy_free_{course_id}",
                'title': course.get('name', 'Untitled Course').replace('100% OFF-', '').replace('100% OFF', '').strip(),
                'description': description,
                'provider': 'Udemy',
                'providerLogo': 'https://www.udemy.com/staticx/udemy/images/v7/logo-udemy.svg',
                'thumbnailImage': image,
                'duration': 'Self-paced',
                'level': level,
                'rating': rating,
                'reviewCount': 0,
                'learningOutcomes': [],
                'registrationUrl': url,
                'isFree': is_free,
                'price': price,
                'actualPrice': f"${actual_price}" if actual_price > 0 else None,
                'saleEnd': sale_end,
                'category': category,
                'skills': [],
                'certificateProvider': 'Udemy',
                'source': 'udemy_free',
                'instructor': instructor
            }

            return formatted

        except Exception as e:
            logger.error(f"Error formatting Udemy course: {str(e)}")
            return None

    def _parse_duration(self, content_info: str) -> str:
        """
        Parse content info to extract duration.

        Args:
            content_info: Content info string (e.g., "12 hours on-demand video")

        Returns:
            Formatted duration string
        """
        if not content_info:
            return 'Self-paced'

        # Try to extract hours
        if 'hour' in content_info.lower():
            parts = content_info.split()
            for i, part in enumerate(parts):
                if 'hour' in part.lower() and i > 0:
                    return f"{parts[i-1]} hours"

        return 'Self-paced'

    def get_categories(self) -> List[str]:
        """
        Get available course categories.

        Returns:
            List of category names
        """
        # Common Udemy categories
        return [
            'Development',
            'Business',
            'Finance & Accounting',
            'IT & Software',
            'Office Productivity',
            'Personal Development',
            'Design',
            'Marketing',
            'Lifestyle',
            'Photography & Video',
            'Health & Fitness',
            'Music',
            'Teaching & Academics'
        ]
