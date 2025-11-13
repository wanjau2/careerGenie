"""Course Aggregation Service - Combine courses from multiple sources."""
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.coursera_service import CourseraService
from services.udemy_service import UdemyService
from services.udemy_free_service import UdemyFreeService

logger = logging.getLogger(__name__)


class CourseAggregationService:
    """Service for aggregating courses from multiple providers."""

    def __init__(self):
        """Initialize aggregation service with all providers."""
        self.coursera = CourseraService()
        self.udemy = UdemyService()
        self.udemy_free = UdemyFreeService()

    def search_courses(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        level: Optional[str] = None,
        is_free: Optional[bool] = None,
        sources: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Search courses across multiple platforms.

        Args:
            query: Search query string
            category: Course category filter
            level: Course difficulty level
            is_free: Filter for free courses
            sources: List of sources to search (coursera, udemy). If None, search all.
            page: Page number for pagination
            page_size: Number of results per page

        Returns:
            Dictionary containing aggregated course results
        """
        # Determine which sources to query
        active_sources = sources or ['coursera', 'udemy', 'udemy_free']

        all_courses = []
        errors = []

        # Use ThreadPoolExecutor to query sources in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}

            # Submit search tasks for each source
            if 'coursera' in active_sources:
                future = executor.submit(
                    self._search_coursera,
                    query, category, level, is_free, page_size
                )
                futures[future] = 'coursera'

            if 'udemy' in active_sources:
                future = executor.submit(
                    self._search_udemy,
                    query, category, level, is_free, page, page_size
                )
                futures[future] = 'udemy'

            if 'udemy_free' in active_sources:
                future = executor.submit(
                    self._search_udemy_free,
                    query, page, page_size
                )
                futures[future] = 'udemy_free'

            # Collect results as they complete
            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    if result.get('courses'):
                        all_courses.extend(result['courses'])
                    if result.get('error'):
                        errors.append({
                            'source': source,
                            'error': result['error']
                        })
                except Exception as e:
                    logger.error(f"Error fetching from {source}: {str(e)}")
                    errors.append({
                        'source': source,
                        'error': str(e)
                    })

        # Sort courses by rating and review count
        all_courses.sort(
            key=lambda x: (x.get('rating', 0) * 0.5 + (min(x.get('reviewCount', 0), 10000) / 10000) * 0.5),
            reverse=True
        )

        # Apply pagination to aggregated results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_courses = all_courses[start_idx:end_idx]

        return {
            'courses': paginated_courses,
            'total': len(all_courses),
            'page': page,
            'pageSize': page_size,
            'totalPages': (len(all_courses) + page_size - 1) // page_size,
            'sources': active_sources,
            'errors': errors if errors else None
        }

    def get_recommended_courses(
        self,
        skills: List[str],
        limit: int = 20
    ) -> Dict:
        """
        Get recommended courses based on user skills/interests.

        Args:
            skills: List of skills user wants to learn
            limit: Number of courses to return

        Returns:
            Dictionary containing recommended courses
        """
        # Build search query from skills
        query = ' '.join(skills[:3])  # Use top 3 skills

        return self.search_courses(
            query=query,
            page_size=limit
        )

    def get_course_details(self, course_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific course.

        Args:
            course_id: Course ID with source prefix (e.g., 'coursera_123', 'udemy_456')

        Returns:
            Dictionary containing course details
        """
        # Parse course ID to determine source
        if course_id.startswith('coursera_'):
            actual_id = course_id.replace('coursera_', '')
            return self.coursera.get_course_details(actual_id)

        elif course_id.startswith('udemy_'):
            actual_id = course_id.replace('udemy_', '')
            return self.udemy.get_course_details(actual_id)

        return None

    def get_all_categories(self) -> Dict:
        """
        Get all available categories from all sources.

        Returns:
            Dictionary mapping sources to their categories
        """
        return {
            'coursera': self.coursera.get_categories(),
            'udemy': self.udemy.get_categories(),
            'all': self._merge_categories()
        }

    def _search_coursera(
        self,
        query: Optional[str],
        category: Optional[str],
        level: Optional[str],
        is_free: Optional[bool],
        limit: int
    ) -> Dict:
        """Search Coursera for courses."""
        try:
            return self.coursera.search_courses(
                query=query,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Coursera search error: {str(e)}")
            return {'courses': [], 'total': 0, 'error': str(e)}

    def _search_udemy(
        self,
        query: Optional[str],
        category: Optional[str],
        level: Optional[str],
        is_free: Optional[bool],
        page: int,
        page_size: int
    ) -> Dict:
        """Search Udemy for courses."""
        try:
            price_filter = 'free' if is_free else None

            return self.udemy.search_courses(
                query=query,
                category=category,
                page=page,
                page_size=page_size,
                price=price_filter
            )
        except Exception as e:
            logger.error(f"Udemy search error: {str(e)}")
            return {'courses': [], 'total': 0, 'error': str(e)}

    def _search_udemy_free(
        self,
        query: Optional[str],
        page: int,
        page_size: int
    ) -> Dict:
        """Search Udemy Free (alternative API) for courses."""
        try:
            if query:
                return self.udemy_free.search_courses(
                    query=query,
                    page=page,
                    limit=page_size
                )
            else:
                return self.udemy_free.get_free_courses(
                    page=page,
                    limit=page_size
                )
        except Exception as e:
            logger.error(f"Udemy Free API search error: {str(e)}")
            return {'courses': [], 'total': 0, 'error': str(e)}

    def _merge_categories(self) -> List[str]:
        """
        Merge and deduplicate categories from all sources.

        Returns:
            List of unique category names
        """
        all_categories = set()

        all_categories.update(self.coursera.get_categories())
        all_categories.update(self.udemy.get_categories())

        return sorted(list(all_categories))

    def get_featured_courses(self, limit: int = 20) -> Dict:
        """
        Get featured courses from all sources.

        Args:
            limit: Number of courses to return per source

        Returns:
            Dictionary containing featured courses
        """
        all_courses = []
        errors = []

        # Get featured from each source
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(self.coursera.search_courses, limit=limit): 'coursera',
                executor.submit(self.udemy.get_featured_courses, limit=limit): 'udemy'
            }

            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    if result.get('courses'):
                        all_courses.extend(result['courses'])
                    if result.get('error'):
                        errors.append({
                            'source': source,
                            'error': result['error']
                        })
                except Exception as e:
                    logger.error(f"Error fetching featured from {source}: {str(e)}")
                    errors.append({
                        'source': source,
                        'error': str(e)
                    })

        # Sort by rating
        all_courses.sort(
            key=lambda x: x.get('rating', 0),
            reverse=True
        )

        # Limit total results
        all_courses = all_courses[:limit]

        return {
            'courses': all_courses,
            'total': len(all_courses),
            'errors': errors if errors else None
        }
