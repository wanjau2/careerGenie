"""Job aggregation service - fetch jobs from multiple sources."""
import os
import requests
from datetime import datetime
import hashlib
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from services.careerjet_api import CareerjetService
from services.jobs_search_api import JobsSearchAPIService
from services.linkedin_jobs_api import LinkedInJobsService
from services.indeed_jobs_api import IndeedJobsService
from services.google_jobs_api import GoogleJobsAPI
from services.google_jobs_direct import GoogleJobsDirect  # FREE - No API key needed!
from services.serpapi_jobs import SerpAPIJobs  # BEST - Official Google Jobs API

logger = logging.getLogger(__name__)


class JobAggregationService:
    """Aggregate jobs from multiple sources (APIs) with Redis caching."""

    def __init__(self):
        """Initialize job aggregation service with all providers."""
        # JSearch API (Google for Jobs aggregator)
        self.jsearch_api_key = os.getenv('JSEARCH_API_KEY')
        self.jsearch_host = os.getenv('JSEARCH_API_HOST', 'jsearch.p.rapidapi.com')

        # Initialize SerpAPI (BEST - Official Google Jobs API)
        self.serpapi_jobs = SerpAPIJobs()

        # Initialize FREE Google Jobs Direct (no API key needed - fallback)
        self.google_jobs_direct = GoogleJobsDirect()

        # Initialize all API services
        self.careerjet_service = CareerjetService()
        self.jobs_search_service = JobsSearchAPIService()
        self.linkedin_service = LinkedInJobsService()
        self.indeed_service = IndeedJobsService()

        # Initialize Redis cache
        self.cache = self._init_cache()

    def _init_cache(self):
        """Initialize Redis cache connection."""
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            cache = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            cache.ping()
            logger.info("Redis cache connected successfully")
            return cache
        except Exception as e:
            logger.warning(f"Redis cache not available: {str(e)}. Running without cache.")
            return None

    def search_jobs(self, query, location=None, filters=None, sources=None, limit=20, use_cache=True):
        """
        Search for jobs across all sources in parallel with caching.

        Args:
            query: Search query (job title, keywords)
            location: Location filter
            filters: Additional filters (remote, salary, etc.)
            sources: List of sources to search. If None, search all available.
            limit: Number of results per source
            use_cache: Whether to use cached results (default: True)

        Returns:
            list: Aggregated job listings
        """
        # Generate cache key
        cache_key = self._generate_cache_key(query, location, filters, sources, limit)

        # Try to get from cache first
        if use_cache and self.cache:
            cached_jobs = self._get_from_cache(cache_key)
            if cached_jobs:
                logger.info(f"Returning {len(cached_jobs)} jobs from cache")
                return cached_jobs

        # Determine which sources to query
        # Prioritize BEST sources: SerpAPI > Free Scraping > RapidAPI
        active_sources = sources or ['serpapi', 'google_direct', 'careerjet', 'jsearch', 'jobs_search', 'linkedin', 'indeed']

        all_jobs = []
        errors = []

        # Use ThreadPoolExecutor to query sources in parallel
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {}

            # PRIORITY 1: SerpAPI (BEST - Official Google Jobs API, 100 free/month)
            if 'serpapi' in active_sources:
                future = executor.submit(
                    self.serpapi_jobs.search_jobs,
                    query, location, limit
                )
                futures[future] = 'serpapi'

            # PRIORITY 2: Free Google Jobs Direct (NO API KEY - Fallback if SerpAPI fails)
            if 'google_direct' in active_sources:
                future = executor.submit(
                    self.google_jobs_direct.search_jobs,
                    query, location, limit
                )
                futures[future] = 'google_direct'

            # PRIORITY 3: JSearch (requires API key, may hit rate limits)
            if 'jsearch' in active_sources and self.jsearch_api_key:
                future = executor.submit(
                    self._fetch_from_jsearch,
                    query, location, filters
                )
                futures[future] = 'jsearch'

            if 'careerjet' in active_sources:
                future = executor.submit(
                    self.careerjet_service.search_jobs,
                    query, location, filters, limit
                )
                futures[future] = 'careerjet'

            if 'jobs_search' in active_sources:
                future = executor.submit(
                    self.jobs_search_service.search_jobs,
                    query, location, filters, limit
                )
                futures[future] = 'jobs_search'

            if 'linkedin' in active_sources:
                future = executor.submit(
                    self.linkedin_service.search_jobs,
                    query, location, filters, limit
                )
                futures[future] = 'linkedin'

            if 'indeed' in active_sources:
                future = executor.submit(
                    self.indeed_service.search_jobs,
                    query, location, filters, limit
                )
                futures[future] = 'indeed'

            # Collect results as they complete
            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_jobs.extend(result)
                        logger.info(f"Fetched {len(result)} jobs from {source}")
                except Exception as e:
                    logger.error(f"Error fetching from {source}: {str(e)}")
                    errors.append({
                        'source': source,
                        'error': str(e)
                    })

        # Deduplicate jobs
        unique_jobs = self._deduplicate_jobs(all_jobs)

        logger.info(f"Total unique jobs after deduplication: {len(unique_jobs)} from {len(active_sources)} sources")

        # Cache the results (TTL: 1 hour)
        if use_cache and self.cache and unique_jobs:
            self._save_to_cache(cache_key, unique_jobs, ttl=3600)

        return unique_jobs

    def _generate_cache_key(self, query, location, filters, sources, limit):
        """Generate a unique cache key for the search parameters."""
        key_parts = [
            query or '',
            location or '',
            json.dumps(filters or {}, sort_keys=True),
            json.dumps(sources or [], sort_keys=True),
            str(limit)
        ]
        key_string = '|'.join(key_parts)
        return f"jobs:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_from_cache(self, cache_key):
        """Get cached job results."""
        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
        return None

    def _save_to_cache(self, cache_key, jobs, ttl=3600):
        """Save job results to cache with TTL (default: 1 hour)."""
        try:
            # Convert datetime objects to strings for JSON serialization
            serialized_jobs = []
            for job in jobs:
                job_copy = job.copy()
                if 'postedAt' in job_copy and isinstance(job_copy['postedAt'], datetime):
                    job_copy['postedAt'] = job_copy['postedAt'].isoformat()
                serialized_jobs.append(job_copy)

            self.cache.setex(cache_key, ttl, json.dumps(serialized_jobs))
            logger.info(f"Cached {len(jobs)} jobs with TTL {ttl}s")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")

    def _fetch_from_jsearch(self, query, location=None, filters=None):
        """
        Fetch jobs from JSearch API (RapidAPI).

        Args:
            query: Search query
            location: Location string
            filters: Filter dict

        Returns:
            list: Job listings from JSearch
        """
        if not self.jsearch_api_key:
            print("Warning: JSEARCH_API_KEY not set. Skipping JSearch API.")
            return []

        try:
            url = f"https://{self.jsearch_host}/search"

            # Build query parameters
            params = {
                'query': query,
                'page': 1,
                'num_pages': 1
            }

            if location:
                params['query'] += f" in {location}"

            if filters:
                if filters.get('remote'):
                    params['remote_jobs_only'] = True
                if filters.get('date_posted'):
                    params['date_posted'] = filters['date_posted']  # all, today, 3days, week, month
                if filters.get('employment_types'):
                    params['employment_types'] = ','.join(filters['employment_types'])

            headers = {
                'X-RapidAPI-Key': self.jsearch_api_key,
                'X-RapidAPI-Host': self.jsearch_host
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Normalize JSearch data to our format
            jobs = []
            for job in data.get('data', []):
                normalized_job = self._normalize_jsearch_job(job)
                jobs.append(normalized_job)

            return jobs

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from JSearch API: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in JSearch API: {e}")
            return []

    def _normalize_jsearch_job(self, job):
        """
        Normalize JSearch job data to our standard format.

        Args:
            job: Raw job data from JSearch API

        Returns:
            dict: Normalized job data
        """
        return {
            'title': job.get('job_title'),
            'company': {
                'name': job.get('employer_name'),
                'logo': job.get('employer_logo'),
                'website': job.get('employer_website'),
                'industry': None  # Not provided by JSearch
            },
            'description': job.get('job_description'),
            'requirements': job.get('job_required_skills', []),
            'responsibilities': job.get('job_highlights', {}).get('Responsibilities', []),
            'qualifications': job.get('job_highlights', {}).get('Qualifications', []),
            'salary': {
                'min': job.get('job_min_salary'),
                'max': job.get('job_max_salary'),
                'currency': job.get('job_salary_currency', 'USD'),
                'period': job.get('job_salary_period', 'YEAR')
            },
            'location': {
                'city': job.get('job_city'),
                'state': job.get('job_state'),
                'country': job.get('job_country'),
                'remote': job.get('job_is_remote', False),
                'coordinates': [
                    job.get('job_latitude'),
                    job.get('job_longitude')
                ] if job.get('job_latitude') else None
            },
            'employment': {
                'type': job.get('job_employment_type'),  # FULLTIME, PARTTIME, CONTRACTOR, INTERN
                'level': None,  # Not provided
                'department': None
            },
            'benefits': job.get('job_benefits', []),
            'applicationDeadline': None,  # Not provided by JSearch
            'postedAt': datetime.fromisoformat(job['job_posted_at_datetime_utc'].replace('Z', '+00:00')) if job.get('job_posted_at_datetime_utc') else datetime.utcnow(),
            'isActive': True,
            'source': 'jsearch',
            'externalId': job.get('job_id'),
            'applyLink': job.get('job_apply_link'),
            'publisher': job.get('job_publisher'),
            # Additional metadata
            'metadata': {
                'googleJobId': job.get('job_google_link'),
                'jobApplyQuality': job.get('job_apply_quality_score'),
                'naicsCode': job.get('job_naics_code'),
                'naicsName': job.get('job_naics_name'),
                'occupationalCategories': job.get('job_occupational_categories', [])
            }
        }

    def _deduplicate_jobs(self, jobs):
        """
        Remove duplicate job listings.

        Args:
            jobs: List of job dicts

        Returns:
            list: Deduplicated jobs
        """
        seen = set()
        unique_jobs = []

        for job in jobs:
            # Create a hash based on title + company + location
            job_signature = self._create_job_signature(job)

            if job_signature not in seen:
                seen.add(job_signature)
                unique_jobs.append(job)

        return unique_jobs

    def _create_job_signature(self, job):
        """
        Create a unique signature for a job posting.

        Args:
            job: Job dict

        Returns:
            str: Unique job signature (hash)
        """
        # Combine key fields to create signature
        title = (job.get('title') or '').lower().strip()
        company = (job.get('company', {}).get('name') or '').lower().strip()
        city = (job.get('location', {}).get('city') or '').lower().strip()
        state = (job.get('location', {}).get('state') or '').lower().strip()

        signature_string = f"{title}|{company}|{city}|{state}"

        # Return hash of signature
        return hashlib.md5(signature_string.encode()).hexdigest()

    def fetch_job_details(self, job_id, source='jsearch'):
        """
        Fetch detailed information for a specific job.

        Args:
            job_id: External job ID
            source: Source platform (jsearch, indeed, etc.)

        Returns:
            dict: Detailed job information
        """
        if source == 'jsearch':
            return self._fetch_jsearch_job_details(job_id)

        return {'error': f'Unsupported source: {source}'}

    def _fetch_jsearch_job_details(self, job_id):
        """Fetch detailed job info from JSearch."""
        if not self.jsearch_api_key:
            return {'error': 'JSEARCH_API_KEY not set'}

        try:
            url = f"https://{self.jsearch_host}/job-details"

            params = {
                'job_id': job_id
            }

            headers = {
                'X-RapidAPI-Key': self.jsearch_api_key,
                'X-RapidAPI-Host': self.jsearch_host
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                return self._normalize_jsearch_job(data['data'][0])

            return {'error': 'Job not found'}

        except Exception as e:
            return {'error': f'Failed to fetch job details: {str(e)}'}

    def get_available_sources(self) -> List[str]:
        """
        Get list of available job sources.

        Returns:
            List of source names
        """
        sources = []

        if self.jsearch_api_key:
            sources.append('jsearch')

        if self.careerjet_service.client:
            sources.append('careerjet')

        if self.jobs_search_service.api_key:
            sources.append('jobs_search')

        if self.linkedin_service.api_key:
            sources.append('linkedin')

        if self.indeed_service.api_key:
            sources.append('indeed')

        return sources if sources else ['jsearch']  # Default to jsearch

    def clear_cache(self, cache_key=None):
        """
        Clear cached job results.

        Args:
            cache_key: Specific cache key to clear. If None, clears all job caches.
        """
        if not self.cache:
            logger.warning("Cache not available")
            return

        try:
            if cache_key:
                self.cache.delete(cache_key)
                logger.info(f"Cleared cache key: {cache_key}")
            else:
                # Clear all job-related caches
                keys = self.cache.keys('jobs:*')
                if keys:
                    self.cache.delete(*keys)
                    logger.info(f"Cleared {len(keys)} job cache keys")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.cache:
            return {'enabled': False}

        try:
            keys = self.cache.keys('jobs:*')
            total_size = sum([len(self.cache.get(key) or '') for key in keys])

            return {
                'enabled': True,
                'total_keys': len(keys),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {'enabled': True, 'error': str(e)}
