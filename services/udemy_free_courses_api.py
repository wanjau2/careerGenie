"""
Udemy Paid Courses for Free API Service (RapidAPI)
Fetches free Udemy courses (normally paid) via RapidAPI
"""

import os
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class UdemyFreeCoursesAPI:
    """Service for fetching free Udemy courses from RapidAPI"""

    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.api_host = 'udemy-paid-courses-for-free-api.p.rapidapi.com'
        self.base_url = f'https://{self.api_host}'

        if not self.api_key:
            logger.warning("RAPIDAPI_KEY not found in environment variables")

    def get_free_courses(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Dict]:
        """
        Get free Udemy courses (normally paid)

        Args:
            category: Filter by category (e.g., 'Development', 'Business', 'Design')
            search: Search query for courses
            page: Page number for pagination
            page_size: Number of results per page

        Returns:
            List of free course dictionaries
        """
        if not self.api_key:
            logger.error("Cannot fetch courses: RAPIDAPI_KEY not configured")
            return []

        # Build query parameters
        params = {
            'page': str(page),
            'page_size': str(page_size)
        }

        if category:
            params['category'] = category

        if search:
            params['search'] = search

        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        try:
            logger.info(f"Fetching free Udemy courses: category={category}, search={search}")

            response = requests.get(
                f"{self.base_url}/api/courses",
                params=params,
                headers=headers,
                timeout=15
            )

            response.raise_for_status()
            data = response.json()

            courses = data.get('courses', data.get('data', []))
            logger.info(f"Udemy Free Courses API returned {len(courses)} courses")

            return self._normalize_courses(courses)

        except requests.exceptions.Timeout:
            logger.error("Udemy Free Courses API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Udemy Free Courses API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Udemy Free Courses API: {e}")
            return []

    def get_latest_courses(self, limit: int = 20) -> List[Dict]:
        """
        Get latest free courses

        Args:
            limit: Number of courses to return

        Returns:
            List of latest free course dictionaries
        """
        if not self.api_key:
            logger.error("Cannot fetch courses: RAPIDAPI_KEY not configured")
            return []

        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        try:
            logger.info(f"Fetching latest {limit} free Udemy courses")

            response = requests.get(
                f"{self.base_url}/api/latest",
                params={'limit': str(limit)},
                headers=headers,
                timeout=15
            )

            response.raise_for_status()
            data = response.json()

            courses = data.get('courses', data.get('data', []))
            logger.info(f"Fetched {len(courses)} latest courses")

            return self._normalize_courses(courses)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch latest courses: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching latest courses: {e}")
            return []

    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search free courses by keyword

        Args:
            keyword: Search keyword (e.g., 'Python', 'JavaScript', 'Marketing')
            limit: Number of results

        Returns:
            List of matching course dictionaries
        """
        return self.get_free_courses(search=keyword, page_size=limit)

    def get_courses_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Get free courses by category

        Args:
            category: Category name
            limit: Number of results

        Returns:
            List of course dictionaries in category
        """
        return self.get_free_courses(category=category, page_size=limit)

    def _normalize_courses(self, courses: List[Dict]) -> List[Dict]:
        """
        Normalize API response to standard course format

        Args:
            courses: Raw courses from API

        Returns:
            Normalized course dictionaries
        """
        normalized = []

        for course in courses:
            try:
                normalized_course = {
                    'id': course.get('id') or course.get('course_id', ''),
                    'title': course.get('title', 'Untitled Course'),
                    'provider': 'Udemy',
                    'description': course.get('description', '')[:500],  # Limit description
                    'thumbnailImage': course.get('image') or course.get('thumbnail', ''),
                    'duration': self._parse_duration(course),
                    'level': self._parse_level(course),
                    'rating': float(course.get('rating', 0)),
                    'reviewCount': int(course.get('reviews', 0)),
                    'studentCount': int(course.get('students', 0)),
                    'price': 'Free',
                    'originalPrice': course.get('original_price', '$199.99'),
                    'isFree': True,
                    'category': course.get('category', 'General'),
                    'language': course.get('language', 'English'),
                    'registrationUrl': course.get('url') or course.get('coupon_url', ''),
                    'providerLogo': 'https://www.udemy.com/staticx/udemy/images/v7/logo-udemy.svg',
                    'instructor': course.get('instructor') or course.get('author', 'Unknown'),
                    'lastUpdated': course.get('last_updated', ''),
                    'learningOutcomes': self._extract_outcomes(course),
                    'couponCode': course.get('coupon_code', ''),
                    'expiryDate': course.get('expiry_date', ''),
                    'source': 'Udemy Free Courses API',
                    'isFeatured': course.get('is_bestseller', False),
                }

                normalized.append(normalized_course)

            except Exception as e:
                logger.warning(f"Failed to normalize course: {e}")
                continue

        return normalized

    def _parse_duration(self, course: Dict) -> str:
        """Parse course duration"""
        duration = course.get('duration')

        if duration:
            # If duration is in seconds
            if isinstance(duration, (int, float)):
                hours = duration / 3600
                if hours < 1:
                    return f"{int(duration / 60)} minutes"
                return f"{hours:.1f} hours"

            # If duration is already a string
            return str(duration)

        # Try content length
        content_length = course.get('content_length')
        if content_length:
            return content_length

        # Default
        lectures = course.get('lectures', 0)
        if lectures:
            return f"{lectures} lectures"

        return "Self-paced"

    def _parse_level(self, course: Dict) -> str:
        """Parse course level"""
        level = course.get('level', '').lower()

        level_mapping = {
            'beginner': 'Beginner',
            'all levels': 'All Levels',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced',
            'expert': 'Advanced',
        }

        for key, value in level_mapping.items():
            if key in level:
                return value

        return 'All Levels'

    def _extract_outcomes(self, course: Dict) -> List[str]:
        """Extract learning outcomes"""
        outcomes = []

        # Check for what_you_will_learn
        learn = course.get('what_you_will_learn', [])
        if isinstance(learn, list):
            outcomes.extend(learn[:5])  # Limit to 5
        elif isinstance(learn, str):
            outcomes.append(learn)

        # Check for objectives
        objectives = course.get('objectives', [])
        if isinstance(objectives, list):
            outcomes.extend(objectives[:5])

        # If no outcomes, create generic ones
        if not outcomes:
            title = course.get('title', '')
            outcomes = [
                f"Master {title}",
                "Build practical skills",
                "Learn from industry experts",
                "Get certificate of completion"
            ]

        return outcomes[:5]  # Return max 5 outcomes

    def get_categories(self) -> List[str]:
        """
        Get available course categories

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
            'Teaching & Academics',
        ]

    def get_trending_courses(self, limit: int = 10) -> List[Dict]:
        """
        Get trending free courses

        Args:
            limit: Number of courses

        Returns:
            List of trending course dictionaries
        """
        if not self.api_key:
            return []

        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        try:
            response = requests.get(
                f"{self.base_url}/api/trending",
                params={'limit': str(limit)},
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                courses = data.get('courses', data.get('data', []))
                return self._normalize_courses(courses)

        except Exception as e:
            logger.warning(f"Could not fetch trending courses: {e}")

        # Fallback to latest courses
        return self.get_latest_courses(limit)
