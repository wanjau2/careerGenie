"""
Careerjet REST API Service (Python 3 Compatible)
Uses the new Careerjet v4 REST API directly
https://www.careerjet.com/partners/api/
"""

import requests
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CareerjetRestService:
    """
    Python 3 compatible Careerjet service using v4 REST API
    Requires: user_ip and user_agent for API compliance
    """

    def __init__(self, affiliate_id: Optional[str] = None, locale: str = 'en_US'):
        """
        Initialize Careerjet REST API service

        Args:
            affiliate_id: Your Careerjet affiliate ID (optional)
            locale: Locale code (e.g., en_US, en_GB, en_KE)
        """
        self.base_url = "https://public.api.careerjet.net/search"
        self.affiliate_id = affiliate_id or os.getenv('CAREERJET_AFFILIATE_ID', '')
        self.locale = locale

        # Get server IP for API requirement
        self.server_ip = os.getenv('SERVER_IP', '197.232.159.231')

        logger.info(f"Careerjet REST API initialized (locale: {locale}, IP: {self.server_ip})")

    def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20,
        contract_type: Optional[str] = None,
        work_hours: Optional[str] = None,
        sort: str = 'relevance'
    ) -> List[Dict]:
        """
        Search jobs using Careerjet REST API v4

        Args:
            query: Job search keywords
            location: Location (city, region, country)
            limit: Number of results (max 99)
            contract_type: 'p' (permanent), 'c' (contract), 't' (temporary), 'i' (intern)
            work_hours: 'f' (full-time), 'p' (part-time)
            sort: 'relevance', 'date', or 'salary'

        Returns:
            List of normalized job dictionaries
        """
        try:
            # Build API parameters
            params = {
                'locale_code': self.locale,
                'keywords': query,
                'user_ip': self.server_ip,
                'user_agent': 'Mozilla/5.0 (compatible; CareerGenie/1.0)',
                'affid': self.affiliate_id,
                'page': 1,
                'pagesize': min(limit, 99),  # Max 99 per page
                'sort': sort
            }

            if location:
                params['location'] = location

            if contract_type:
                params['contracttype'] = contract_type

            if work_hours:
                params['contractperiod'] = work_hours

            logger.info(f"Searching Careerjet: '{query}' in '{location or 'any location'}'")

            # Make API request
            response = requests.get(
                self.base_url,
                params=params,
                timeout=15
            )

            if response.status_code == 403:
                logger.error("Careerjet API 403: Check IP address is whitelisted")
                return []
            elif response.status_code == 400:
                logger.error(f"Careerjet API 400: {response.text}")
                return []
            elif response.status_code != 200:
                logger.error(f"Careerjet API failed with status {response.status_code}")
                return []

            data = response.json()

            # Check response type
            if data.get('type') != 'JOBS':
                logger.warning(f"Careerjet returned type: {data.get('type')}")
                if data.get('type') == 'ERROR':
                    logger.error(f"Careerjet error: {data.get('error')}")
                return []

            # Extract and normalize jobs
            jobs_raw = data.get('jobs', [])

            if not jobs_raw:
                logger.info(f"No jobs found for: '{query}' in '{location}'")
                return []

            jobs = self._normalize_jobs(jobs_raw)

            logger.info(f"✅ Careerjet returned {len(jobs)} jobs")
            return jobs

        except requests.exceptions.Timeout:
            logger.error("Careerjet API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Careerjet API request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Careerjet error: {str(e)}")
            return []

    def _normalize_jobs(self, jobs_raw: List[Dict]) -> List[Dict]:
        """
        Normalize Careerjet jobs to CareerGenie format

        Args:
            jobs_raw: Raw jobs from Careerjet API

        Returns:
            List of normalized job dictionaries
        """
        normalized = []

        for job in jobs_raw:
            try:
                # Parse location
                location_str = job.get('locations', '')
                location_parts = [p.strip() for p in location_str.split(',') if p.strip()]

                city = location_parts[0] if len(location_parts) > 0 else None
                country = location_parts[-1] if len(location_parts) > 0 else None

                # Parse salary
                salary_str = job.get('salary', '')
                salary_data = self._parse_salary(salary_str)

                # Check if remote
                description = job.get('description', '').lower()
                title_lower = job.get('title', '').lower()
                is_remote = 'remote' in description or 'remote' in title_lower

                # Build normalized job
                normalized_job = {
                    'id': f"careerjet_{job.get('url', '').split('/')[-1] if job.get('url') else ''}",
                    'title': job.get('title', 'No Title'),
                    'company': {
                        'name': job.get('company', 'Company Not Listed'),
                        'logo': None,
                        'website': job.get('site'),
                    },
                    'location': {
                        'city': city,
                        'country': country,
                        'formatted': location_str,
                        'remote': is_remote,
                        'coordinates': None
                    },
                    'description': job.get('description', ''),
                    'salary': salary_data,
                    'employment': {
                        'type': self._infer_job_type(job),
                        'level': self._infer_experience_level(job),
                    },
                    'requirements': [],
                    'responsibilities': [],
                    'benefits': [],
                    'postedAt': self._parse_date(job.get('date')),
                    'applyUrl': job.get('url'),
                    'source': 'Careerjet',
                    'isActive': True,
                    'metadata': {
                        'careerjet_site': job.get('site'),
                    }
                }

                normalized.append(normalized_job)

            except Exception as e:
                logger.warning(f"Failed to normalize Careerjet job: {str(e)}")
                continue

        return normalized

    def _parse_salary(self, salary_str: str) -> Optional[Dict]:
        """Parse salary string to structured format"""
        if not salary_str or salary_str.strip() == '':
            return None

        try:
            import re
            # Remove currency symbols and extract numbers
            numbers = re.findall(r'[\d,]+', salary_str.replace(',', ''))

            if len(numbers) >= 2:
                min_sal = int(numbers[0])
                max_sal = int(numbers[1])
                return {
                    'min': min_sal,
                    'max': max_sal,
                    'currency': 'USD' if '$' in salary_str else 'KES' if 'KES' in salary_str or 'Ksh' in salary_str else 'USD',
                    'period': 'YEAR',
                    'formatted': salary_str
                }
            elif len(numbers) == 1:
                amount = int(numbers[0])
                return {
                    'min': amount,
                    'max': None,
                    'currency': 'USD' if '$' in salary_str else 'KES' if 'KES' in salary_str or 'Ksh' in salary_str else 'USD',
                    'period': 'YEAR',
                    'formatted': salary_str
                }
        except:
            pass

        return None

    def _infer_job_type(self, job: Dict) -> str:
        """Infer employment type from job data"""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        if 'intern' in title or 'internship' in description:
            return 'Internship'
        elif 'contract' in title or 'contractor' in description:
            return 'Contract'
        elif 'part-time' in title or 'part time' in description:
            return 'Part-time'
        else:
            return 'Full-time'

    def _infer_experience_level(self, job: Dict) -> str:
        """Infer experience level from job data"""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        if any(word in title for word in ['senior', 'sr.', 'lead', 'principal', 'director']):
            return 'Senior'
        elif any(word in title for word in ['junior', 'jr.', 'entry', 'associate', 'graduate']):
            return 'Entry Level'
        elif any(word in title for word in ['intern', 'internship']):
            return 'Internship'
        else:
            return 'Mid Level'

    def _parse_date(self, date_str: Optional[str]) -> str:
        """Parse relative date string (e.g., '3 days ago')"""
        if not date_str:
            return datetime.utcnow().isoformat()

        # Careerjet returns relative dates
        # For simplicity, return current time
        # You could parse "3 days ago" if needed
        return datetime.utcnow().isoformat()

    def get_available_locales(self) -> List[str]:
        """Get list of available Careerjet locales"""
        return [
            'en_US',  # United States
            'en_GB',  # United Kingdom
            'en_CA',  # Canada
            'en_AU',  # Australia
            'en_IN',  # India
            'en_KE',  # Kenya
            'en_NG',  # Nigeria
            'en_ZA',  # South Africa
            'en_GH',  # Ghana
            'en_UG',  # Uganda
            'en_TZ',  # Tanzania
            'en_IE',  # Ireland
            'en_NZ',  # New Zealand
            'fr_FR',  # France
            'de_DE',  # Germany
            'es_ES',  # Spain
            'it_IT',  # Italy
            'pt_BR',  # Brazil
        ]
