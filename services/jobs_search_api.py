"""JOBS SEARCH API Service - Multi-platform job aggregator via RapidAPI."""
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class JobsSearchAPIService:
    """Service for fetching jobs from multiple platforms via JOBS SEARCH API."""

    # Using JOBS SEARCH API from RapidAPI (aggregates LinkedIn, Indeed, ZipRecruiter)
    BASE_URL = "https://jobs-search-api.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize JOBS SEARCH API service.

        Args:
            api_key: RapidAPI key
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY_JOBS_SEARCH')
        if not self.api_key:
            self.api_key = os.getenv('RAPIDAPI_KEY')  # Fallback to main key

        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'jobs-search-api.p.rapidapi.com'
            })

    def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search jobs across multiple platforms.

        Args:
            query: Search query (job title, keywords)
            location: Location filter
            filters: Additional filters
            limit: Maximum number of results

        Returns:
            List of normalized job dictionaries
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for JOBS SEARCH API")
            return []

        try:
            url = f"{self.BASE_URL}/search"

            params = {
                'query': query,
                'num_pages': 1,
                'page': 1
            }

            if location:
                params['location'] = location

            # Apply filters if provided
            if filters:
                if filters.get('remote'):
                    params['remote_jobs_only'] = 'true'
                if filters.get('date_posted'):
                    params['date_posted'] = filters['date_posted']
                if filters.get('employment_types'):
                    params['employment_types'] = ','.join(filters['employment_types'])

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Normalize jobs to standard format
            jobs = []
            for job in data.get('data', data.get('jobs', []))[:limit]:
                normalized_job = self._normalize_job(job)
                if normalized_job:
                    jobs.append(normalized_job)

            return jobs

        except requests.exceptions.RequestException as e:
            logger.error(f"JOBS SEARCH API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in JOBS SEARCH API: {str(e)}")
            return []

    def _normalize_job(self, job: Dict) -> Optional[Dict]:
        """
        Normalize job data to standard format.

        Args:
            job: Raw job data from API

        Returns:
            Normalized job dictionary
        """
        try:
            # Extract location data
            city = job.get('job_city')
            state = job.get('job_state')
            country = job.get('job_country', 'USA')

            # Extract salary
            salary_min = job.get('job_min_salary')
            salary_max = job.get('job_max_salary')
            salary_currency = job.get('job_salary_currency', 'USD')
            salary_period = job.get('job_salary_period', 'YEAR')

            # Determine if remote
            is_remote = job.get('job_is_remote', False)

            # Extract employment type
            job_type = job.get('job_employment_type', '')
            if job_type:
                job_type = job_type.upper().replace('-', '').replace(' ', '')

            # Extract highlights
            highlights = job.get('job_highlights', {})
            responsibilities = highlights.get('Responsibilities', []) if highlights else []
            qualifications = highlights.get('Qualifications', []) if highlights else []

            # Build normalized job
            normalized = {
                'title': job.get('job_title'),
                'company': {
                    'name': job.get('employer_name'),
                    'logo': job.get('employer_logo'),
                    'website': job.get('employer_website'),
                    'industry': None
                },
                'description': job.get('job_description', ''),
                'requirements': job.get('job_required_skills', []),
                'responsibilities': responsibilities,
                'qualifications': qualifications,
                'salary': {
                    'min': salary_min,
                    'max': salary_max,
                    'currency': salary_currency,
                    'period': salary_period.upper() if salary_period else 'YEAR'
                },
                'location': {
                    'city': city,
                    'state': state,
                    'country': country,
                    'remote': is_remote,
                    'coordinates': [
                        job.get('job_latitude'),
                        job.get('job_longitude')
                    ] if job.get('job_latitude') else None
                },
                'employment': {
                    'type': job_type if job_type else None,
                    'level': None,
                    'department': None
                },
                'benefits': job.get('job_benefits', []),
                'applicationDeadline': None,
                'postedAt': self._parse_date(job.get('job_posted_at_datetime_utc')),
                'isActive': True,
                'source': job.get('job_publisher', 'jobs_search_api').lower().replace(' ', '_'),
                'externalId': job.get('job_id'),
                'applyLink': job.get('job_apply_link'),
                'publisher': job.get('job_publisher'),
                'metadata': {
                    'googleJobId': job.get('job_google_link'),
                    'applyQualityScore': job.get('job_apply_quality_score'),
                    'naicsCode': job.get('job_naics_code'),
                    'naicsName': job.get('job_naics_name')
                }
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing JOBS SEARCH API job: {str(e)}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string

        Returns:
            datetime object
        """
        if not date_str:
            return datetime.utcnow()

        try:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.utcnow()
