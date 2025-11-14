"""
SerpAPI Google Jobs Integration
Official API for Google for Jobs - more reliable than scraping
Free tier: 100 searches/month
"""

import os
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SerpAPIJobs:
    """
    Google Jobs API via SerpAPI
    https://serpapi.com/google-jobs-api

    Free tier: 100 searches/month
    Paid: $50/month for 5,000 searches
    """

    def __init__(self):
        self.api_key = os.getenv('SERPAPI_KEY') or os.getenv('SERPAPI_API_KEY')
        self.base_url = "https://serpapi.com/search"

        if not self.api_key:
            logger.warning("SERPAPI_KEY not found - SerpAPI will not be available")

    def search_jobs(
        self,
        query: str,
        location: str = "Nairobi, Kenya",
        num_results: int = 10,
        date_posted: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        chips: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for jobs using SerpAPI Google Jobs

        Args:
            query: Job search query (e.g., "Data Engineer")
            location: Location to search (e.g., "Nairobi, Kenya")
            num_results: Number of results to return
            date_posted: Filter by date ('today', 'week', 'month')
            job_type: Filter by type ('fulltime', 'parttime', 'contract', 'intern')
            experience_level: Filter by level ('entry_level', 'mid_level', 'senior_level')
            chips: Additional filter chips (e.g., "date_posted:today,employment_type:FULLTIME")

        Returns:
            List of job dictionaries in standard format
        """
        if not self.api_key:
            logger.error("Cannot search jobs: SERPAPI_KEY not configured")
            return []

        # Build query parameters for SerpAPI
        params = {
            'engine': 'google_jobs',
            'q': query,
            'location': location,
            'api_key': self.api_key,
            'hl': 'en',
            'gl': self._get_country_code(location),
            'num': min(num_results, 100)  # SerpAPI max per page
        }

        # Build chips parameter for filters
        filter_chips = []

        if date_posted:
            date_map = {
                'today': 'today',
                'week': 'week',
                'month': 'month',
                '3days': '3days'
            }
            if date_posted.lower() in date_map:
                filter_chips.append(f"date_posted:{date_map[date_posted.lower()]}")

        if job_type:
            type_map = {
                'fulltime': 'FULLTIME',
                'full-time': 'FULLTIME',
                'parttime': 'PARTTIME',
                'part-time': 'PARTTIME',
                'contract': 'CONTRACTOR',
                'contractor': 'CONTRACTOR',
                'intern': 'INTERN',
                'internship': 'INTERN'
            }
            job_type_normalized = type_map.get(job_type.lower(), job_type.upper())
            filter_chips.append(f"employment_type:{job_type_normalized}")

        if experience_level:
            level_map = {
                'entry': 'ENTRY_LEVEL',
                'entry_level': 'ENTRY_LEVEL',
                'junior': 'ENTRY_LEVEL',
                'mid': 'MID_LEVEL',
                'mid_level': 'MID_LEVEL',
                'senior': 'SENIOR_LEVEL',
                'senior_level': 'SENIOR_LEVEL'
            }
            level_normalized = level_map.get(experience_level.lower(), experience_level.upper())
            filter_chips.append(f"experience_level:{level_normalized}")

        # Add custom chips if provided
        if chips:
            filter_chips.append(chips)

        # Add chips to params
        if filter_chips:
            params['chips'] = ','.join(filter_chips)

        try:
            logger.info(f"🔍 Searching SerpAPI Google Jobs: '{query}' in '{location}'")
            if filter_chips:
                logger.info(f"   Filters: {', '.join(filter_chips)}")

            response = requests.get(
                self.base_url,
                params=params,
                timeout=15
            )

            if response.status_code == 401:
                logger.error("❌ SerpAPI: Invalid API key (401)")
                return []
            elif response.status_code == 429:
                logger.error("❌ SerpAPI: Rate limit exceeded (429)")
                return []
            elif response.status_code != 200:
                logger.error(f"❌ SerpAPI failed with status {response.status_code}")
                return []

            data = response.json()

            # Check for errors in response
            if 'error' in data:
                logger.error(f"❌ SerpAPI error: {data['error']}")
                return []

            # Extract jobs from response
            jobs_raw = data.get('jobs_results', [])

            if not jobs_raw:
                logger.warning(f"⚠️  No jobs found for query: '{query}' in '{location}'")
                return []

            # Normalize jobs to standard format
            jobs = self._normalize_jobs(jobs_raw)

            logger.info(f"✅ SerpAPI returned {len(jobs)} jobs")
            return jobs

        except requests.exceptions.Timeout:
            logger.error("❌ SerpAPI request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ SerpAPI request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected SerpAPI error: {str(e)}")
            return []

    def _normalize_jobs(self, jobs_raw: List[Dict]) -> List[Dict]:
        """
        Normalize SerpAPI job results to standard CareerGenie format

        Args:
            jobs_raw: Raw jobs from SerpAPI

        Returns:
            Normalized job dictionaries
        """
        normalized = []

        for job in jobs_raw:
            try:
                # Extract job details
                job_id = job.get('job_id', '')
                title = job.get('title', 'No Title')
                company_name = job.get('company_name', 'Unknown Company')
                location = job.get('location', 'Location Not Specified')
                description = job.get('description', '')

                # Extract additional details
                detected_extensions = job.get('detected_extensions', {})

                # Parse salary
                salary = self._parse_salary(detected_extensions)

                # Parse employment type
                employment_type = self._parse_employment_type(detected_extensions, job)

                # Parse experience level
                experience_level = self._parse_experience_level(job)

                # Build normalized job
                normalized_job = {
                    'id': job_id,
                    'title': title,
                    'company': {
                        'name': company_name,
                        'logo': job.get('thumbnail', None)
                    },
                    'location': {
                        'city': location,
                        'formatted': location,
                        'remote': 'remote' in location.lower() or 'work from home' in location.lower()
                    },
                    'description': description,
                    'salary': salary,
                    'employment': {
                        'type': employment_type,
                        'level': experience_level
                    },
                    'requirements': job.get('job_highlights', {}).get('Qualifications', []),
                    'benefits': job.get('job_highlights', {}).get('Benefits', []),
                    'responsibilities': job.get('job_highlights', {}).get('Responsibilities', []),
                    'postedAt': detected_extensions.get('posted_at', ''),
                    'source': 'Google Jobs (SerpAPI)',
                    'applyUrl': job.get('apply_options', [{}])[0].get('link', ''),
                    'isActive': True,
                    'metadata': {
                        'serpapi_job_id': job_id,
                        'extensions': job.get('extensions', [])
                    }
                }

                normalized.append(normalized_job)

            except Exception as e:
                logger.warning(f"Failed to normalize job: {str(e)}")
                continue

        return normalized

    def _parse_salary(self, detected_extensions: Dict) -> Optional[Dict]:
        """Parse salary information from detected extensions"""
        if 'salary' in detected_extensions:
            salary_text = detected_extensions['salary']

            # Try to extract min/max from salary text
            # Example: "$80,000 - $120,000 a year"
            import re
            numbers = re.findall(r'\$?([\d,]+)', salary_text)

            if len(numbers) >= 2:
                min_sal = int(numbers[0].replace(',', ''))
                max_sal = int(numbers[1].replace(',', ''))
                return {
                    'min': min_sal,
                    'max': max_sal,
                    'currency': '$',
                    'formatted': salary_text
                }
            elif len(numbers) == 1:
                amount = int(numbers[0].replace(',', ''))
                return {
                    'min': amount,
                    'max': None,
                    'currency': '$',
                    'formatted': salary_text
                }

        return None

    def _parse_employment_type(self, detected_extensions: Dict, job: Dict) -> str:
        """Parse employment type from job data"""
        # Check detected extensions first
        if 'schedule_type' in detected_extensions:
            schedule = detected_extensions['schedule_type'].lower()
            if 'full' in schedule:
                return 'Full-time'
            elif 'part' in schedule:
                return 'Part-time'
            elif 'contract' in schedule:
                return 'Contract'
            elif 'intern' in schedule:
                return 'Internship'

        # Check job title and description
        title_desc = (job.get('title', '') + ' ' + job.get('description', '')).lower()

        if 'part-time' in title_desc or 'part time' in title_desc:
            return 'Part-time'
        elif 'contract' in title_desc or 'contractor' in title_desc:
            return 'Contract'
        elif 'intern' in title_desc or 'internship' in title_desc:
            return 'Internship'

        return 'Full-time'

    def _parse_experience_level(self, job: Dict) -> str:
        """Parse experience level from job title and description"""
        title_desc = (job.get('title', '') + ' ' + job.get('description', '')).lower()

        if any(word in title_desc for word in ['senior', 'sr.', 'lead', 'principal', 'staff', 'expert']):
            return 'Senior'
        elif any(word in title_desc for word in ['junior', 'jr.', 'entry', 'entry-level', 'associate', 'graduate']):
            return 'Entry Level'
        elif any(word in title_desc for word in ['intern', 'internship', 'trainee']):
            return 'Internship'
        elif any(word in title_desc for word in ['mid', 'mid-level', 'intermediate']):
            return 'Mid Level'

        return 'Not Specified'

    def _get_country_code(self, location: str) -> str:
        """Get country code from location string"""
        location_lower = location.lower()

        # Common country mappings
        country_codes = {
            'kenya': 'ke',
            'nairobi': 'ke',
            'united states': 'us',
            'usa': 'us',
            'uk': 'gb',
            'united kingdom': 'gb',
            'canada': 'ca',
            'india': 'in',
            'australia': 'au',
            'germany': 'de',
            'france': 'fr',
            'nigeria': 'ng',
            'south africa': 'za',
            'ghana': 'gh',
            'uganda': 'ug',
            'tanzania': 'tz'
        }

        for country, code in country_codes.items():
            if country in location_lower:
                return code

        return 'us'  # Default to US

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific job

        Args:
            job_id: The SerpAPI job ID

        Returns:
            Detailed job dictionary or None
        """
        if not self.api_key:
            logger.error("Cannot get job details: SERPAPI_KEY not configured")
            return None

        params = {
            'engine': 'google_jobs_listing',
            'q': job_id,
            'api_key': self.api_key
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get job details: {str(e)}")
            return None
