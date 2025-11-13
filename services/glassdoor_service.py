"""
Glassdoor Real-Time API Service
Provides company data and interview details
"""
import os
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

class GlassdoorService:
    """Service for fetching data from Glassdoor Real-Time API"""

    BASE_URL = "https://glassdoor-real-time.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Glassdoor service with API key"""
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'glassdoor-real-time.p.rapidapi.com'
            })

    def search_jobs(self, query: str, location: str = "", num_pages: int = 1) -> Dict[str, Any]:
        """
        Search for jobs on Glassdoor

        Args:
            query: Job search query (e.g., "Software Engineer")
            location: Location filter (e.g., "New York, NY")
            num_pages: Number of pages to fetch (default: 1)

        Returns:
            Dictionary containing job listings
        """
        try:
            url = f"{self.BASE_URL}/jobs/search"

            params = {
                'query': query,
                'page': 1
            }

            if location:
                params['location'] = location

            print(f"🔍 Searching Glassdoor: {query} in {location or 'All locations'}")

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data or 'data' not in data:
                print(f"⚠️ No jobs found on Glassdoor")
                return {'jobs': [], 'total': 0}

            jobs = self._format_jobs(data.get('data', []))

            print(f"✅ Found {len(jobs)} jobs on Glassdoor")
            return {
                'jobs': jobs,
                'total': len(jobs),
                'source': 'glassdoor'
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ Glassdoor API error: {str(e)}")
            return {'jobs': [], 'total': 0, 'error': str(e)}

    def get_company_info(self, company_id: str) -> Dict[str, Any]:
        """
        Get detailed company information

        Args:
            company_id: Glassdoor company ID

        Returns:
            Dictionary containing company details
        """
        try:
            url = f"{self.BASE_URL}/companies/{company_id}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching company info: {str(e)}")
            return {'error': str(e)}

    def get_interview_details(self, interview_id: str) -> Dict[str, Any]:
        """
        Get interview details for a specific interview

        Args:
            interview_id: Interview ID

        Returns:
            Dictionary containing interview details
        """
        try:
            url = f"{self.BASE_URL}/companies/interview-details"
            params = {'interviewId': interview_id}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching interview details: {str(e)}")
            return {'error': str(e)}

    def _format_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Format Glassdoor jobs to standardized format"""
        formatted_jobs = []

        for job in jobs:
            try:
                formatted_job = {
                    'id': job.get('jobId', ''),
                    'title': job.get('jobTitle', job.get('title', '')),
                    'company': job.get('employer', {}).get('name', job.get('companyName', '')),
                    'location': job.get('location', ''),
                    'description': job.get('jobDescription', job.get('description', '')),
                    'salary': self._format_salary(job),
                    'posted_date': job.get('jobPostedDate', job.get('postedDate', '')),
                    'job_type': job.get('employmentType', 'Full-time'),
                    'url': job.get('jobUrl', ''),
                    'source': 'glassdoor',
                    'company_rating': job.get('employer', {}).get('rating', 0),
                    'company_logo': job.get('employer', {}).get('logo', ''),
                    'scraped_at': datetime.utcnow().isoformat()
                }

                formatted_jobs.append(formatted_job)

            except Exception as e:
                print(f"⚠️ Error formatting Glassdoor job: {str(e)}")
                continue

        return formatted_jobs

    def _format_salary(self, job: Dict) -> Optional[str]:
        """Extract and format salary information"""
        salary_info = job.get('salary', {})

        if not salary_info:
            return None

        min_salary = salary_info.get('min', '')
        max_salary = salary_info.get('max', '')
        currency = salary_info.get('currency', 'USD')

        if min_salary and max_salary:
            return f"{currency} {min_salary} - {max_salary}"
        elif min_salary:
            return f"{currency} {min_salary}+"
        elif max_salary:
            return f"Up to {currency} {max_salary}"

        return None
