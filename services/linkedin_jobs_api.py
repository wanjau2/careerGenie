"""LinkedIn Jobs API Service - Fetch jobs from LinkedIn via RapidAPI."""
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LinkedInJobsService:
    """Service for fetching jobs from LinkedIn via RapidAPI."""

    # Using LinkedIn Job Search API from RapidAPI
    BASE_URL = "https://linkedin-job-search-api.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LinkedIn Jobs service.

        Args:
            api_key: RapidAPI key
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'linkedin-job-search-api.p.rapidapi.com'
            })

    def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search jobs on LinkedIn.

        Args:
            query: Search query (job title, keywords)
            location: Location filter
            filters: Additional filters
            limit: Maximum number of results

        Returns:
            List of normalized job dictionaries
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for LinkedIn Jobs")
            return []

        try:
            url = f"{self.BASE_URL}/search"

            params = {
                'query': query,
                'limit': min(limit, 50)
            }

            if location:
                params['location'] = location

            # Apply filters if provided
            if filters:
                if filters.get('remote'):
                    params['remoteFilter'] = 'remote'
                if filters.get('date_posted'):
                    # Map to LinkedIn's date filters
                    date_map = {
                        'today': 'past-24-hours',
                        '3days': 'past-week',
                        'week': 'past-week',
                        'month': 'past-month'
                    }
                    params['datePosted'] = date_map.get(filters['date_posted'], 'any-time')

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Normalize jobs to standard format
            jobs = []
            for job in data.get('jobs', data.get('data', [])):
                normalized_job = self._normalize_job(job)
                if normalized_job:
                    jobs.append(normalized_job)

            return jobs

        except requests.exceptions.RequestException as e:
            logger.error(f"LinkedIn Jobs API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in LinkedIn Jobs API: {str(e)}")
            return []

    def _normalize_job(self, job: Dict) -> Optional[Dict]:
        """
        Normalize LinkedIn job data to standard format.

        Args:
            job: Raw job data from API

        Returns:
            Normalized job dictionary
        """
        try:
            # Extract location data
            location_str = job.get('location', '')
            location_parts = location_str.split(',') if location_str else []

            city = location_parts[0].strip() if len(location_parts) > 0 else None
            state = location_parts[1].strip() if len(location_parts) > 1 else None
            country = location_parts[-1].strip() if len(location_parts) > 0 else None

            # Extract salary if available
            salary_str = job.get('salary', '')
            salary_min = None
            salary_max = None

            if salary_str and '-' in salary_str:
                try:
                    parts = salary_str.replace('$', '').replace(',', '').split('-')
                    salary_min = int(parts[0].strip())
                    salary_max = int(parts[1].split()[0].strip()) if len(parts) > 1 else None
                except:
                    pass

            # Determine if remote
            is_remote = 'remote' in location_str.lower() or job.get('workplaceType', '').lower() == 'remote'

            # Extract employment type
            employment_type = job.get('employmentType', '')
            if employment_type:
                employment_type = employment_type.upper().replace('-', '').replace(' ', '')

            # Build normalized job
            normalized = {
                'title': job.get('title', job.get('jobTitle')),
                'company': {
                    'name': job.get('companyName', job.get('company', {}).get('name')),
                    'logo': job.get('companyLogo', job.get('company', {}).get('logo')),
                    'website': job.get('companyUrl'),
                    'industry': job.get('industry', job.get('company', {}).get('industry'))
                },
                'description': job.get('description', job.get('jobDescription', '')),
                'requirements': [],
                'responsibilities': [],
                'qualifications': [],
                'salary': {
                    'min': salary_min,
                    'max': salary_max,
                    'currency': 'USD',
                    'period': 'YEAR'
                },
                'location': {
                    'city': city,
                    'state': state,
                    'country': country,
                    'remote': is_remote,
                    'coordinates': None
                },
                'employment': {
                    'type': employment_type if employment_type else None,
                    'level': job.get('seniorityLevel'),
                    'department': job.get('function')
                },
                'benefits': [],
                'applicationDeadline': None,
                'postedAt': self._parse_date(job.get('postedAt', job.get('postedDate'))),
                'isActive': True,
                'source': 'linkedin',
                'externalId': job.get('jobId', job.get('id')),
                'applyLink': job.get('jobUrl', job.get('applyUrl', job.get('url'))),
                'publisher': 'LinkedIn',
                'metadata': {
                    'applicantCount': job.get('applicantCount'),
                    'workplaceType': job.get('workplaceType'),
                    'companySize': job.get('companySize')
                }
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing LinkedIn job: {str(e)}")
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
            try:
                # Try relative dates
                if 'hour' in date_str or 'minute' in date_str or 'day' in date_str:
                    return datetime.utcnow()
                return datetime.utcnow()
            except:
                return datetime.utcnow()

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific job.

        Args:
            job_id: LinkedIn job ID

        Returns:
            Normalized job dictionary
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for LinkedIn Jobs")
            return None

        try:
            url = f"{self.BASE_URL}/job-details"
            params = {'jobId': job_id}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return self._normalize_job(data)

        except Exception as e:
            logger.error(f"LinkedIn job details error: {str(e)}")
            return None
