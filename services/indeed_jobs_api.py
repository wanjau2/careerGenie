"""Indeed Jobs API Service - Fetch jobs from Indeed via RapidAPI."""
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IndeedJobsService:
    """Service for fetching jobs from Indeed via RapidAPI."""

    # Using Indeed Jobs Scraper API from RapidAPI
    BASE_URL = "https://indeed-jobs-scraper-api.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Indeed Jobs service.

        Args:
            api_key: RapidAPI key
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'indeed-jobs-scraper-api.p.rapidapi.com'
            })

    def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search jobs on Indeed.

        Args:
            query: Search query (job title, keywords)
            location: Location filter
            filters: Additional filters
            limit: Maximum number of results

        Returns:
            List of normalized job dictionaries
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for Indeed Jobs")
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
                    params['remoteOnly'] = 'true'
                if filters.get('date_posted'):
                    # Map to Indeed's date filters
                    date_map = {
                        'today': '1',
                        '3days': '3',
                        'week': '7',
                        'month': '30'
                    }
                    params['fromage'] = date_map.get(filters['date_posted'], '30')
                if filters.get('employment_types'):
                    # Indeed uses jt parameter for job types
                    params['jt'] = ','.join(filters['employment_types']).lower()

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Normalize jobs to standard format
            jobs = []
            for job in data.get('jobs', data.get('results', data.get('data', []))):
                normalized_job = self._normalize_job(job)
                if normalized_job:
                    jobs.append(normalized_job)

            return jobs

        except requests.exceptions.RequestException as e:
            logger.error(f"Indeed Jobs API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Indeed Jobs API: {str(e)}")
            return []

    def _normalize_job(self, job: Dict) -> Optional[Dict]:
        """
        Normalize Indeed job data to standard format.

        Args:
            job: Raw job data from API

        Returns:
            Normalized job dictionary
        """
        try:
            # Extract location data
            location_str = job.get('location', job.get('formattedLocation', ''))
            location_parts = location_str.split(',') if location_str else []

            city = location_parts[0].strip() if len(location_parts) > 0 else None
            state = location_parts[1].strip() if len(location_parts) > 1 else None
            country = job.get('country', 'USA')

            # Extract salary
            salary_min = job.get('salary_min', job.get('salaryMin'))
            salary_max = job.get('salary_max', job.get('salaryMax'))
            salary_str = job.get('salary', job.get('salarySnippet', {}).get('text', ''))

            # Try to parse salary from string if not provided
            if not salary_min and salary_str:
                try:
                    # Parse strings like "$50,000 - $70,000 a year"
                    parts = salary_str.replace('$', '').replace(',', '').replace('a year', '').replace('per year', '').strip().split('-')
                    if len(parts) >= 1:
                        salary_min = int(''.join(filter(str.isdigit, parts[0])))
                    if len(parts) >= 2:
                        salary_max = int(''.join(filter(str.isdigit, parts[1])))
                except:
                    pass

            # Determine if remote
            is_remote = job.get('isRemote', False) or 'remote' in location_str.lower()

            # Extract employment type
            job_type = job.get('jobType', job.get('employmentType', ''))
            if job_type:
                job_type = job_type.upper().replace('-', '').replace(' ', '')

            # Extract company info
            company_name = job.get('company', job.get('companyName', ''))
            company_logo = job.get('companyLogo', job.get('company_logo'))
            company_rating = job.get('companyRating')

            # Build normalized job
            normalized = {
                'title': job.get('title', job.get('jobTitle', '')),
                'company': {
                    'name': company_name,
                    'logo': company_logo,
                    'website': job.get('companyUrl'),
                    'industry': None,
                    'rating': company_rating
                },
                'description': job.get('description', job.get('snippet', '')),
                'requirements': job.get('requirements', []),
                'responsibilities': [],
                'qualifications': job.get('qualifications', []),
                'salary': {
                    'min': salary_min,
                    'max': salary_max,
                    'currency': job.get('currency', 'USD'),
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
                    'type': job_type if job_type else None,
                    'level': None,
                    'department': None
                },
                'benefits': job.get('benefits', []),
                'applicationDeadline': None,
                'postedAt': self._parse_date(job.get('postedAt', job.get('date', job.get('formattedRelativeTime')))),
                'isActive': True,
                'source': 'indeed',
                'externalId': job.get('jobKey', job.get('id', job.get('key'))),
                'applyLink': job.get('link', job.get('url', job.get('jobUrl'))),
                'publisher': 'Indeed',
                'metadata': {
                    'sponsored': job.get('sponsored', False),
                    'companyRating': company_rating,
                    'reviewCount': job.get('reviewCount'),
                    'urgentlyHiring': job.get('urgentlyHiring', False)
                }
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing Indeed job: {str(e)}")
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
                # Handle relative dates
                if 'day' in str(date_str).lower() or 'hour' in str(date_str).lower() or 'just posted' in str(date_str).lower():
                    return datetime.utcnow()
                return datetime.utcnow()
            except:
                return datetime.utcnow()

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific job.

        Args:
            job_id: Indeed job key

        Returns:
            Normalized job dictionary
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured for Indeed Jobs")
            return None

        try:
            url = f"{self.BASE_URL}/job-details"
            params = {'jobKey': job_id}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return self._normalize_job(data)

        except Exception as e:
            logger.error(f"Indeed job details error: {str(e)}")
            return None
