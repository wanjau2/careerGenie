"""
LinkedIn Jobs API Service (jobs-api14)
Provides LinkedIn job listings with advanced filtering
"""
import os
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

class LinkedInJobsService:
    """Service for fetching jobs from LinkedIn via jobs-api14"""

    BASE_URL = "https://jobs-api14.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize LinkedIn Jobs service with API key"""
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'jobs-api14.p.rapidapi.com'
            })

    def search_jobs(
        self,
        query: str,
        location: str = "Worldwide",
        experience_levels: Optional[List[str]] = None,
        workplace_types: Optional[List[str]] = None,
        date_posted: str = "month",
        employment_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for jobs on LinkedIn

        Args:
            query: Job search query (e.g., "Software Engineer")
            location: Location filter (default: "Worldwide")
            experience_levels: List of experience levels (intern, entry, associate, midSenior, director)
            workplace_types: List of workplace types (remote, hybrid, onSite)
            date_posted: Date filter (any, day, week, month)
            employment_types: List of employment types (fulltime, parttime, contractor, intern, temporary)
            limit: Maximum number of results

        Returns:
            Dictionary containing job listings
        """
        try:
            url = f"{self.BASE_URL}/v2/linkedin/search"

            # Default values
            if experience_levels is None:
                experience_levels = ['entry', 'associate', 'midSenior']
            if workplace_types is None:
                workplace_types = ['remote', 'hybrid', 'onSite']
            if employment_types is None:
                employment_types = ['fulltime', 'parttime', 'contractor']

            params = {
                'query': query,
                'location': location,
                'experienceLevels': ';'.join(experience_levels),
                'workplaceTypes': ';'.join(workplace_types),
                'datePosted': date_posted,
                'employmentTypes': ';'.join(employment_types)
            }

            print(f"🔍 Searching LinkedIn: {query} in {location}")

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if not data or 'jobs' not in data:
                print(f"⚠️ No jobs found on LinkedIn")
                return {'jobs': [], 'total': 0}

            jobs = self._format_jobs(data.get('jobs', []))[:limit]

            print(f"✅ Found {len(jobs)} jobs on LinkedIn")
            return {
                'jobs': jobs,
                'total': len(jobs),
                'source': 'linkedin'
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ LinkedIn API error: {str(e)}")
            return {'jobs': [], 'total': 0, 'error': str(e)}

    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed job information

        Args:
            job_id: LinkedIn job ID

        Returns:
            Dictionary containing job details
        """
        try:
            url = f"{self.BASE_URL}/v2/linkedin/job/{job_id}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching job details: {str(e)}")
            return {'error': str(e)}

    def _format_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Format LinkedIn jobs to standardized format"""
        formatted_jobs = []

        for job in jobs:
            try:
                formatted_job = {
                    'id': job.get('jobId', job.get('id', '')),
                    'title': job.get('title', ''),
                    'company': job.get('company', {}).get('name', job.get('companyName', '')),
                    'location': job.get('location', ''),
                    'description': job.get('description', ''),
                    'salary': self._format_salary(job),
                    'posted_date': job.get('postedAt', job.get('listedAt', '')),
                    'job_type': job.get('employmentType', job.get('type', 'Full-time')),
                    'url': job.get('url', job.get('jobUrl', '')),
                    'source': 'linkedin',
                    'experience_level': job.get('experienceLevel', ''),
                    'workplace_type': job.get('workplaceType', ''),
                    'applies': job.get('totalApplicants', 0),
                    'company_logo': job.get('company', {}).get('logo', ''),
                    'company_url': job.get('company', {}).get('url', ''),
                    'scraped_at': datetime.utcnow().isoformat()
                }

                formatted_jobs.append(formatted_job)

            except Exception as e:
                print(f"⚠️ Error formatting LinkedIn job: {str(e)}")
                continue

        return formatted_jobs

    def _format_salary(self, job: Dict) -> Optional[str]:
        """Extract and format salary information"""
        salary_min = job.get('salaryMin', '')
        salary_max = job.get('salaryMax', '')
        salary_currency = job.get('salaryCurrency', 'USD')

        if salary_min and salary_max:
            return f"{salary_currency} {salary_min} - {salary_max}"
        elif salary_min:
            return f"{salary_currency} {salary_min}+"
        elif salary_max:
            return f"Up to {salary_currency} {salary_max}"
        elif job.get('salary'):
            return str(job.get('salary'))

        return None
