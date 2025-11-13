"""
Internships API Service
Provides active internship opportunities
"""
import os
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

class InternshipsService:
    """Service for fetching internship opportunities"""

    BASE_URL = "https://internships-api.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Internships service with API key"""
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'internships-api.p.rapidapi.com'
            })

    def get_active_internships(self, days: int = 7) -> Dict[str, Any]:
        """
        Get active internships posted in the last N days

        Args:
            days: Number of days (7, 14, 30)

        Returns:
            Dictionary containing internship listings
        """
        try:
            # API endpoint for active internships
            url = f"{self.BASE_URL}/active-jb-{days}d"

            print(f"🔍 Fetching active internships (last {days} days)")

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()

            if not data or isinstance(data, dict) and 'error' in data:
                print(f"⚠️ No internships found")
                return {'jobs': [], 'total': 0}

            # Handle different response formats
            if isinstance(data, list):
                jobs = self._format_internships(data)
            elif isinstance(data, dict) and 'data' in data:
                jobs = self._format_internships(data.get('data', []))
            elif isinstance(data, dict) and 'internships' in data:
                jobs = self._format_internships(data.get('internships', []))
            else:
                jobs = self._format_internships([data])

            print(f"✅ Found {len(jobs)} internships")
            return {
                'jobs': jobs,
                'total': len(jobs),
                'source': 'internships_api'
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ Internships API error: {str(e)}")
            return {'jobs': [], 'total': 0, 'error': str(e)}

    def search_internships(self, query: str = "", location: str = "") -> Dict[str, Any]:
        """
        Search internships with optional filters
        Note: This endpoint may not be available in the free tier

        Args:
            query: Search query
            location: Location filter

        Returns:
            Dictionary containing internship listings
        """
        try:
            url = f"{self.BASE_URL}/search"
            params = {}

            if query:
                params['query'] = query
            if location:
                params['location'] = location

            print(f"🔍 Searching internships: {query or 'all'} in {location or 'all locations'}")

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if not data:
                print(f"⚠️ No internships found")
                return {'jobs': [], 'total': 0}

            jobs = self._format_internships(data if isinstance(data, list) else data.get('data', []))

            print(f"✅ Found {len(jobs)} internships")
            return {
                'jobs': jobs,
                'total': len(jobs),
                'source': 'internships_api'
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ Internships search error: {str(e)}")
            # Fallback to active internships
            return self.get_active_internships()

    def _format_internships(self, internships: List[Dict]) -> List[Dict]:
        """Format internships to standardized job format"""
        formatted_jobs = []

        for internship in internships:
            try:
                formatted_job = {
                    'id': internship.get('id', internship.get('internshipId', '')),
                    'title': internship.get('title', internship.get('positionName', '')),
                    'company': internship.get('company', internship.get('companyName', '')),
                    'location': internship.get('location', internship.get('locations', '')),
                    'description': internship.get('description', ''),
                    'salary': self._format_stipend(internship),
                    'posted_date': internship.get('postedDate', internship.get('startDate', '')),
                    'job_type': 'Internship',
                    'url': internship.get('url', internship.get('applyUrl', '')),
                    'source': 'internships_api',
                    'duration': internship.get('duration', ''),
                    'start_date': internship.get('startDate', ''),
                    'application_deadline': internship.get('deadline', internship.get('applicationDeadline', '')),
                    'is_remote': internship.get('isRemote', False),
                    'perks': internship.get('perks', []),
                    'scraped_at': datetime.utcnow().isoformat()
                }

                formatted_jobs.append(formatted_job)

            except Exception as e:
                print(f"⚠️ Error formatting internship: {str(e)}")
                continue

        return formatted_jobs

    def _format_stipend(self, internship: Dict) -> Optional[str]:
        """Extract and format stipend/salary information"""
        stipend = internship.get('stipend', '')
        salary = internship.get('salary', '')

        if stipend:
            return f"Stipend: {stipend}"
        elif salary:
            return str(salary)
        elif internship.get('isPaid', False):
            return "Paid"
        elif internship.get('isUnpaid', False):
            return "Unpaid"

        return None
