"""
Additional Udemy Free Courses API Service
Alternative source for free Udemy courses
"""
import os
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

class UdemyFreeService:
    """Service for fetching free Udemy courses from paid-udemy-course-for-free API"""

    BASE_URL = "https://paid-udemy-course-for-free.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Udemy Free service with API key"""
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'paid-udemy-course-for-free.p.rapidapi.com'
            })

    def get_free_courses(self, page: int = 0, limit: int = 20) -> Dict[str, Any]:
        """
        Get free Udemy courses

        Args:
            page: Page number (starts from 0)
            limit: Number of courses to return

        Returns:
            Dictionary containing course listings
        """
        try:
            url = f"{self.BASE_URL}/"
            params = {'page': page}

            print(f"🔍 Fetching free Udemy courses (page {page})")

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if not data:
                print(f"⚠️ No courses found")
                return {'courses': [], 'total': 0}

            # Handle different response formats
            if isinstance(data, list):
                courses = self._format_courses(data)
            elif isinstance(data, dict) and 'courses' in data:
                courses = self._format_courses(data.get('courses', []))
            elif isinstance(data, dict) and 'data' in data:
                courses = self._format_courses(data.get('data', []))
            else:
                courses = self._format_courses([data])

            # Limit results
            courses = courses[:limit]

            print(f"✅ Found {len(courses)} free Udemy courses")
            return {
                'courses': courses,
                'total': len(courses),
                'source': 'udemy_free_alt'
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ Udemy Free API error: {str(e)}")
            return {'courses': [], 'total': 0, 'error': str(e)}

    def search_courses(self, query: str = "", page: int = 0, limit: int = 20) -> Dict[str, Any]:
        """
        Search for free Udemy courses
        Note: Search functionality may be limited in this API

        Args:
            query: Search query
            page: Page number
            limit: Number of results

        Returns:
            Dictionary containing course listings
        """
        try:
            # Try search endpoint first
            url = f"{self.BASE_URL}/search"
            params = {
                'query': query,
                'page': page
            }

            print(f"🔍 Searching free Udemy courses: {query}")

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            courses = self._format_courses(data if isinstance(data, list) else data.get('courses', []))
            courses = courses[:limit]

            print(f"✅ Found {len(courses)} courses")
            return {
                'courses': courses,
                'total': len(courses),
                'source': 'udemy_free_alt'
            }

        except requests.exceptions.RequestException:
            # Fallback to getting all courses and filtering
            print(f"⚠️ Search not available, fetching all courses")
            result = self.get_free_courses(page=page, limit=limit)

            # Filter by query if provided
            if query and result['courses']:
                query_lower = query.lower()
                filtered = [
                    c for c in result['courses']
                    if query_lower in c.get('title', '').lower() or
                       query_lower in c.get('description', '').lower()
                ]
                result['courses'] = filtered[:limit]
                result['total'] = len(filtered)

            return result

    def _format_courses(self, courses: List[Dict]) -> List[Dict]:
        """Format courses to standardized format"""
        formatted_courses = []

        for course in courses:
            try:
                formatted_course = {
                    'id': course.get('id', course.get('courseId', '')),
                    'title': course.get('title', course.get('name', '')),
                    'description': course.get('description', course.get('headline', '')),
                    'instructor': course.get('instructor', course.get('author', '')),
                    'url': course.get('url', course.get('courseUrl', '')),
                    'coupon_code': course.get('couponCode', course.get('code', '')),
                    'coupon_url': course.get('couponUrl', ''),
                    'discount': course.get('discount', '100'),
                    'original_price': course.get('originalPrice', course.get('price', '')),
                    'discounted_price': course.get('discountedPrice', '0'),
                    'thumbnail': course.get('image', course.get('thumbnail', '')),
                    'rating': course.get('rating', 0),
                    'reviews': course.get('reviews', course.get('numReviews', 0)),
                    'students': course.get('students', course.get('numSubscribers', 0)),
                    'duration': course.get('duration', ''),
                    'level': course.get('level', course.get('instructionalLevel', '')),
                    'language': course.get('language', course.get('locale', 'English')),
                    'category': course.get('category', ''),
                    'expires_at': course.get('expiresAt', course.get('expiry', '')),
                    'is_free': True,
                    'source': 'udemy_free_alt',
                    'scraped_at': datetime.utcnow().isoformat()
                }

                formatted_courses.append(formatted_course)

            except Exception as e:
                print(f"⚠️ Error formatting Udemy course: {str(e)}")
                continue

        return formatted_courses
