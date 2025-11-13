"""Careerjet API Service - Fetch jobs from Careerjet."""
import logging
from datetime import datetime
from typing import Dict, List, Optional

try:
    from careerjet_api import CareerjetAPIClient
    CAREERJET_AVAILABLE = True
except ImportError:
    CAREERJET_AVAILABLE = False
    CareerjetAPIClient = None

logger = logging.getLogger(__name__)


class CareerjetService:
    """Service for fetching jobs from Careerjet API."""

    def __init__(self, locale: str = 'en_US'):
        """
        Initialize Careerjet service.

        Args:
            locale: Locale for job searches (e.g., en_US, en_GB, en_IN, etc.)
        """
        if not CAREERJET_AVAILABLE:
            logger.warning("careerjet-api-client not installed. Install with: pip install careerjet-api-client")
            self.client = None
            return

        try:
            self.client = CareerjetAPIClient(locale)
            self.locale = locale
        except Exception as e:
            logger.error(f"Failed to initialize Careerjet client: {str(e)}")
            self.client = None

    def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search jobs on Careerjet.

        Args:
            query: Search query (job title, keywords)
            location: Location filter (e.g., "New York", "London, UK")
            filters: Additional filters
            limit: Maximum number of results (max 99)

        Returns:
            List of normalized job dictionaries
        """
        if not self.client:
            logger.warning("Careerjet client not available")
            return []

        try:
            # Build search parameters
            params = {
                'keywords': query,
                'pagesize': min(limit, 99),  # Careerjet max is 99
                'page': 1
            }

            if location:
                params['location'] = location

            # Apply filters if provided
            if filters:
                if filters.get('remote'):
                    params['keywords'] += ' remote'

                if filters.get('employment_types'):
                    # Add employment type to keywords
                    job_types = filters['employment_types']
                    if isinstance(job_types, list) and job_types:
                        params['keywords'] += f" {' OR '.join(job_types)}"

                # Careerjet supports sorting
                if filters.get('sort'):
                    params['sort'] = filters['sort']  # 'relevance', 'date', 'salary'
                else:
                    params['sort'] = 'relevance'

                # Contract type and contract period
                if filters.get('contracttype'):
                    params['contracttype'] = filters['contracttype']  # 'p' (permanent), 'c' (contract), 't' (temporary)

                if filters.get('contractperiod'):
                    params['contractperiod'] = filters['contractperiod']  # 'f' (full-time), 'p' (part-time)

            # Make API call
            result = self.client.search(params)

            if not result or result.get('type') != 'JOBS':
                logger.warning(f"Careerjet API returned no results or error: {result}")
                return []

            # Normalize jobs to standard format
            jobs = []
            for job in result.get('jobs', []):
                normalized_job = self._normalize_job(job)
                if normalized_job:
                    jobs.append(normalized_job)

            return jobs

        except Exception as e:
            logger.error(f"Careerjet API error: {str(e)}")
            return []

    def _normalize_job(self, job: Dict) -> Optional[Dict]:
        """
        Normalize Careerjet job data to standard format.

        Args:
            job: Raw job data from Careerjet API

        Returns:
            Normalized job dictionary
        """
        try:
            # Extract location data
            location_str = job.get('locations', '')
            location_parts = location_str.split(',') if location_str else []

            city = location_parts[0].strip() if len(location_parts) > 0 else None
            state = location_parts[1].strip() if len(location_parts) > 1 else None
            country = location_parts[-1].strip() if len(location_parts) > 0 else None

            # Parse salary if available
            salary_str = job.get('salary', '')
            salary_min = None
            salary_max = None

            if salary_str:
                try:
                    # Parse strings like "$50,000 - $70,000"
                    parts = salary_str.replace('$', '').replace(',', '').replace('£', '').replace('€', '').strip().split('-')
                    if len(parts) >= 1:
                        salary_min = int(''.join(filter(str.isdigit, parts[0])))
                    if len(parts) >= 2:
                        salary_max = int(''.join(filter(str.isdigit, parts[1])))
                except:
                    pass

            # Determine if remote
            description = job.get('description', '').lower()
            is_remote = 'remote' in description or 'work from home' in description

            # Build normalized job
            normalized = {
                'title': job.get('title'),
                'company': {
                    'name': job.get('company'),
                    'logo': None,
                    'website': job.get('site'),
                    'industry': None
                },
                'description': job.get('description', ''),
                'requirements': [],
                'responsibilities': [],
                'qualifications': [],
                'salary': {
                    'min': salary_min,
                    'max': salary_max,
                    'currency': self._get_currency_from_locale(),
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
                    'type': None,
                    'level': None,
                    'department': None
                },
                'benefits': [],
                'applicationDeadline': None,
                'postedAt': self._parse_date(job.get('date')),
                'isActive': True,
                'source': 'careerjet',
                'externalId': None,  # Careerjet doesn't provide unique ID
                'applyLink': job.get('url'),
                'publisher': 'Careerjet',
                'metadata': {
                    'site': job.get('site')
                }
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing Careerjet job: {str(e)}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string from Careerjet (relative format like "3 days ago")

        Returns:
            datetime object
        """
        if not date_str:
            return datetime.utcnow()

        try:
            # Careerjet returns relative dates like "3 days ago", "1 hour ago"
            # For simplicity, return current time
            # Could implement relative date parsing if needed
            return datetime.utcnow()
        except:
            return datetime.utcnow()

    def _get_currency_from_locale(self) -> str:
        """
        Get currency code based on locale.

        Returns:
            Currency code (USD, GBP, EUR, etc.)
        """
        currency_map = {
            'en_US': 'USD',
            'en_GB': 'GBP',
            'en_CA': 'CAD',
            'en_AU': 'AUD',
            'en_IN': 'INR',
            'fr_FR': 'EUR',
            'de_DE': 'EUR',
            'es_ES': 'EUR',
            'it_IT': 'EUR',
            'pt_BR': 'BRL',
            'ja_JP': 'JPY',
            'zh_CN': 'CNY'
        }
        return currency_map.get(self.locale, 'USD')

    def get_available_locales(self) -> List[str]:
        """
        Get list of available Careerjet locales.

        Returns:
            List of locale codes
        """
        return [
            'en_US',  # United States
            'en_GB',  # United Kingdom
            'en_CA',  # Canada
            'en_AU',  # Australia
            'en_IN',  # India
            'en_IE',  # Ireland
            'en_NZ',  # New Zealand
            'en_ZA',  # South Africa
            'fr_FR',  # France
            'de_DE',  # Germany
            'es_ES',  # Spain
            'it_IT',  # Italy
            'pt_BR',  # Brazil
            'ja_JP',  # Japan
            'zh_CN',  # China
            'ru_RU',  # Russia
            'pl_PL',  # Poland
            'nl_NL',  # Netherlands
        ]
