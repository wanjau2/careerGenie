"""
Celery Tasks for Course Cache Management
=========================================

Background tasks to:
- Refresh course cache daily
- Warm cache with popular queries
- Clean expired entries
- Monitor cache health

Schedule: Runs automatically via Celery Beat
"""

import logging
from celery import shared_task
from datetime import datetime

from services.course_cache import get_course_cache
from services.course_aggregation import CourseAggregationService

logger = logging.getLogger(__name__)


@shared_task(name='refresh_course_cache')
def refresh_course_cache():
    """
    Refresh course cache with fresh data.

    Runs daily to keep cache up-to-date.
    Fetches courses for popular queries and categories.

    Returns:
        Dictionary with refresh statistics
    """
    try:
        logger.info("=" * 80)
        logger.info("COURSE CACHE REFRESH - STARTED")
        logger.info("=" * 80)

        cache_service = get_course_cache()
        course_service = CourseAggregationService()

        # Popular queries to cache
        popular_queries = [
            # Programming
            {'type': 'search', 'query': 'Python', 'page_size': 50},
            {'type': 'search', 'query': 'JavaScript', 'page_size': 50},
            {'type': 'search', 'query': 'React', 'page_size': 30},
            {'type': 'search', 'query': 'Node.js', 'page_size': 30},
            {'type': 'search', 'query': 'Java', 'page_size': 30},

            # Data Science
            {'type': 'search', 'query': 'Machine Learning', 'page_size': 40},
            {'type': 'search', 'query': 'Data Science', 'page_size': 40},
            {'type': 'search', 'query': 'AI', 'page_size': 30},
            {'type': 'search', 'query': 'Data Analysis', 'page_size': 30},

            # Cloud & DevOps
            {'type': 'search', 'query': 'AWS', 'page_size': 30},
            {'type': 'search', 'query': 'Docker', 'page_size': 20},
            {'type': 'search', 'query': 'Kubernetes', 'page_size': 20},
            {'type': 'search', 'query': 'DevOps', 'page_size': 30},

            # Web Development
            {'type': 'search', 'query': 'Web Development', 'page_size': 50},
            {'type': 'search', 'query': 'Frontend', 'page_size': 30},
            {'type': 'search', 'query': 'Backend', 'page_size': 30},
            {'type': 'search', 'query': 'Full Stack', 'page_size': 30},

            # Mobile
            {'type': 'search', 'query': 'React Native', 'page_size': 20},
            {'type': 'search', 'query': 'Flutter', 'page_size': 20},
            {'type': 'search', 'query': 'iOS', 'page_size': 20},
            {'type': 'search', 'query': 'Android', 'page_size': 20},

            # Design
            {'type': 'search', 'query': 'UI/UX Design', 'page_size': 30},
            {'type': 'search', 'query': 'Figma', 'page_size': 20},
            {'type': 'search', 'query': 'Graphic Design', 'page_size': 30},

            # Business
            {'type': 'search', 'query': 'Project Management', 'page_size': 30},
            {'type': 'search', 'query': 'Product Management', 'page_size': 20},
            {'type': 'search', 'query': 'Business Analysis', 'page_size': 20},

            # Marketing
            {'type': 'search', 'query': 'Digital Marketing', 'page_size': 30},
            {'type': 'search', 'query': 'SEO', 'page_size': 20},
            {'type': 'search', 'query': 'Social Media Marketing', 'page_size': 20},

            # Categories
            {'type': 'search', 'category': 'Development', 'page_size': 50},
            {'type': 'search', 'category': 'Business', 'page_size': 40},
            {'type': 'search', 'category': 'Design', 'page_size': 30},

            # Free courses
            {'type': 'search', 'is_free': True, 'page_size': 50},

            # Featured
            {'type': 'featured', 'limit': 50},
        ]

        cached_count = 0
        failed_count = 0
        total_courses_cached = 0

        for query_config in popular_queries:
            try:
                cache_type = query_config.pop('type')
                logger.info(f"Caching: {cache_type} - {query_config}")

                # Fetch fresh data
                if cache_type == 'search':
                    result = course_service.search_courses(**query_config)
                elif cache_type == 'featured':
                    result = course_service.get_featured_courses(**query_config)
                else:
                    continue

                # Cache the result
                if result.get('courses'):
                    cache_service.set(cache_type, result, **query_config)
                    cached_count += 1
                    total_courses_cached += len(result['courses'])
                    logger.info(f"  ✓ Cached {len(result['courses'])} courses")
                else:
                    logger.warning(f"  ⚠ No courses found")
                    failed_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error caching query {query_config}: {str(e)}")
                failed_count += 1

        stats = {
            'refresh_time': datetime.utcnow().isoformat(),
            'queries_attempted': len(popular_queries),
            'queries_cached': cached_count,
            'queries_failed': failed_count,
            'total_courses_cached': total_courses_cached,
            'success_rate': (cached_count / len(popular_queries)) * 100
        }

        logger.info("=" * 80)
        logger.info("COURSE CACHE REFRESH - COMPLETED")
        logger.info(f"Queries Cached: {cached_count}/{len(popular_queries)}")
        logger.info(f"Total Courses: {total_courses_cached}")
        logger.info(f"Success Rate: {stats['success_rate']:.1f}%")
        logger.info("=" * 80)

        return stats

    except Exception as e:
        logger.error(f"Error in refresh_course_cache task: {str(e)}")
        return {
            'error': str(e),
            'refresh_time': datetime.utcnow().isoformat()
        }


@shared_task(name='warm_course_cache')
def warm_course_cache():
    """
    Warm cache with frequently accessed queries.

    Similar to refresh but can be run on-demand.
    Useful after cache invalidation or app deployment.

    Returns:
        Dictionary with warming statistics
    """
    try:
        logger.info("Warming course cache...")

        # Use the same queries as refresh
        result = refresh_course_cache()

        logger.info(f"Cache warming completed: {result.get('queries_cached', 0)} queries")
        return result

    except Exception as e:
        logger.error(f"Error warming cache: {str(e)}")
        return {'error': str(e)}


@shared_task(name='clean_expired_cache')
def clean_expired_cache():
    """
    Clean expired cache entries.

    Note: MongoDB TTL index auto-deletes, but this ensures immediate cleanup.
    Runs every 6 hours.

    Returns:
        Number of entries deleted
    """
    try:
        logger.info("Cleaning expired course cache entries...")

        cache_service = get_course_cache()
        deleted_count = cache_service.clear_expired()

        logger.info(f"Cleaned {deleted_count} expired cache entries")
        return {
            'deleted_count': deleted_count,
            'cleaned_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error cleaning expired cache: {str(e)}")
        return {'error': str(e), 'deleted_count': 0}


@shared_task(name='cache_health_check')
def cache_health_check():
    """
    Monitor cache health and performance.

    Tracks:
    - Cache hit rate
    - Cache size
    - Popular queries
    - API call savings

    Runs every hour.

    Returns:
        Cache health statistics
    """
    try:
        logger.info("Running cache health check...")

        cache_service = get_course_cache()
        stats = cache_service.get_statistics()

        logger.info(f"Cache Health:")
        logger.info(f"  Active Entries: {stats.get('active_entries', 0)}")
        logger.info(f"  Total Hits: {stats.get('total_hits', 0)}")
        logger.info(f"  Hit Rate: {stats.get('hit_rate', 0):.2f}%")

        # Log warning if cache is unhealthy
        if stats.get('active_entries', 0) < 10:
            logger.warning("⚠️ Low cache entries! Consider running refresh task.")

        if stats.get('hit_rate', 0) < 50:
            logger.warning("⚠️ Low cache hit rate! Cache may need optimization.")

        return stats

    except Exception as e:
        logger.error(f"Error in cache health check: {str(e)}")
        return {'error': str(e)}


@shared_task(name='invalidate_course_cache')
def invalidate_course_cache(cache_type: str = None):
    """
    Invalidate (clear) course cache.

    Args:
        cache_type: Type of cache to invalidate (None = all)

    Returns:
        Number of entries deleted
    """
    try:
        logger.info(f"Invalidating course cache: {cache_type or 'ALL'}")

        cache_service = get_course_cache()
        deleted_count = cache_service.invalidate(cache_type)

        logger.info(f"Invalidated {deleted_count} cache entries")
        return {
            'deleted_count': deleted_count,
            'invalidated_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return {'error': str(e), 'deleted_count': 0}
