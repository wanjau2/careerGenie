"""
Google Jobs API Service (RapidAPI)
Fetches job listings from Google for Jobs via RapidAPI
"""

import os
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GoogleJobsAPI:
    """Service for fetching jobs from Google Jobs API on RapidAPI"""

    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.api_host = 'google-jobs-api.p.rapidapi.com'
        self.base_url = f'https://{self.api_host}'

        if not self.api_key:
            logger.warning("RAPIDAPI_KEY not found in environment variables")

    def search_jobs(
        self,
        query: str,
        location: str = "United States",
        page: int = 1,
        num_results: int = 10,
        date_posted: Optional[str] = None,
        job_type: Optional[str] = None,
        remote_jobs_only: bool = False
    ) -> List[Dict]:
        """
        Search for jobs using Google Jobs API

        Args:
            query: Job search query (e.g., "Python developer")
            location: Location to search (e.g., "New York, NY")
            page: Page number for pagination
            num_results: Number of results per page (max 50)
            date_posted: Filter by date ('today', 'week', 'month')
            job_type: Filter by type ('fulltime', 'parttime', 'contractor', 'intern')
            remote_jobs_only: Only return remote jobs

        Returns:
            List of job dictionaries
        """
        if not self.api_key:
            logger.error("Cannot search jobs: RAPIDAPI_KEY not configured")
            return []

        # Build query parameters
        params = {
            'q': query,
            'location': location,
            'page': str(page),
            'num_results': str(min(num_results, 50))  # API max is 50
        }

        # Add optional filters
        if date_posted:
            params['date_posted'] = date_posted

        if job_type:
            params['job_type'] = job_type

        if remote_jobs_only:
            params['remote_jobs_only'] = 'true'

        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        try:
            logger.info(f"Searching Google Jobs API: query='{query}', location='{location}'")

            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            jobs = data.get('jobs', [])
            logger.info(f"Google Jobs API returned {len(jobs)} jobs")

            return self._normalize_jobs(jobs)

        except requests.exceptions.Timeout:
            logger.error("Google Jobs API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Jobs API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Google Jobs API: {e}")
            return []

    def _normalize_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Normalize Google Jobs API response to standard format

        Args:
            jobs: Raw jobs from API

        Returns:
            Normalized job dictionaries
        """
        normalized = []

        for job in jobs:
            try:
                normalized_job = {
                    'id': job.get('job_id', ''),
                    'title': job.get('title', 'No Title'),
                    'company': job.get('company_name', 'Unknown Company'),
                    'location': self._parse_location(job),
                    'description': job.get('description', ''),
                    'salary': self._parse_salary(job),
                    'employmentType': self._parse_employment_type(job),
                    'datePosted': job.get('posted_at', ''),
                    'source': 'Google Jobs API',
                    'applyUrl': job.get('apply_link') or job.get('job_apply_link', ''),
                    'companyLogo': job.get('company_logo', ''),
                    'remote': self._is_remote(job),
                    'highlights': job.get('job_highlights', []),
                    'requiredSkills': self._extract_skills(job),
                    'experienceLevel': self._parse_experience_level(job),
                }

                normalized.append(normalized_job)

            except Exception as e:
                logger.warning(f"Failed to normalize job: {e}")
                continue

        return normalized

    def _parse_location(self, job: Dict) -> str:
        """Parse location from job data"""
        location = job.get('location', '')
        city = job.get('city', '')
        state = job.get('state', '')
        country = job.get('country', '')

        if location:
            return location

        parts = [p for p in [city, state, country] if p]
        return ', '.join(parts) if parts else 'Remote'

    def _parse_salary(self, job: Dict) -> Optional[str]:
        """Parse salary information"""
        salary_min = job.get('salary_min')
        salary_max = job.get('salary_max')
        salary_period = job.get('salary_period', 'year')

        if salary_min and salary_max:
            return f"${salary_min:,} - ${salary_max:,} per {salary_period}"
        elif salary_min:
            return f"${salary_min:,}+ per {salary_period}"
        elif salary_max:
            return f"Up to ${salary_max:,} per {salary_period}"

        # Try alternative salary field
        salary_text = job.get('salary', '')
        return salary_text if salary_text else None

    def _parse_employment_type(self, job: Dict) -> str:
        """Parse employment type"""
        job_type = job.get('job_type', '').lower()

        type_mapping = {
            'fulltime': 'Full-time',
            'full-time': 'Full-time',
            'parttime': 'Part-time',
            'part-time': 'Part-time',
            'contractor': 'Contract',
            'contract': 'Contract',
            'intern': 'Internship',
            'internship': 'Internship',
            'temporary': 'Temporary',
        }

        return type_mapping.get(job_type, 'Full-time')

    def _is_remote(self, job: Dict) -> bool:
        """Check if job is remote"""
        # Check explicit remote flag
        if job.get('is_remote') or job.get('remote_jobs_only'):
            return True

        # Check location for remote keywords
        location = job.get('location', '').lower()
        remote_keywords = ['remote', 'work from home', 'anywhere']

        return any(keyword in location for keyword in remote_keywords)

    def _extract_skills(self, job: Dict) -> List[str]:
        """Extract required skills from job"""
        skills = []

        # Check if skills are provided
        if 'required_skills' in job:
            skills.extend(job['required_skills'])

        # Try to extract from highlights
        highlights = job.get('job_highlights', [])
        for highlight in highlights:
            if isinstance(highlight, dict):
                title = highlight.get('title', '').lower()
                if 'qualification' in title or 'skill' in title:
                    items = highlight.get('items', [])
                    skills.extend(items)

        return skills[:10]  # Limit to top 10 skills

    def _parse_experience_level(self, job: Dict) -> str:
        """Parse experience level from job"""
        # Check if explicitly provided
        if 'experience_level' in job:
            return job['experience_level']

        # Try to infer from title
        title = job.get('title', '').lower()

        if any(word in title for word in ['senior', 'sr.', 'lead', 'principal', 'staff']):
            return 'Senior'
        elif any(word in title for word in ['junior', 'jr.', 'entry', 'associate']):
            return 'Entry Level'
        elif any(word in title for word in ['mid', 'intermediate']):
            return 'Mid Level'
        elif any(word in title for word in ['intern', 'internship']):
            return 'Internship'

        return 'Not Specified'

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific job

        Args:
            job_id: The job ID from search results

        Returns:
            Detailed job dictionary or None
        """
        if not self.api_key:
            logger.error("Cannot get job details: RAPIDAPI_KEY not configured")
            return None

        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        try:
            response = requests.get(
                f"{self.base_url}/job/{job_id}",
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get job details: {e}")
            return None
