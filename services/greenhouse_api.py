"""
Greenhouse Job Board API Service
Fetch jobs from companies using Greenhouse ATS
FREE - No API key required for public job boards
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GreenhouseService:
    """
    Service for fetching jobs from Greenhouse Job Board API
    https://developers.greenhouse.io/job-board.html

    FREE - No authentication required for public job listings
    """

    def __init__(self):
        self.base_url = "https://boards-api.greenhouse.io/v1/boards"
        self.headers = {
            'User-Agent': 'CareerGenie Job Aggregator',
            'Accept': 'application/json'
        }

        # List of popular companies using Greenhouse
        # You can add more board tokens from companies' career pages
        self.board_tokens = [
            'airbnb',
            'uber',
            'stripe',
            'gitlab',
            'shopify',
            'twitch',
            'reddit',
            'coinbase',
            'databricks',
            'cloudflare',
            'mongodb',
            'segment',
            'grammarly',
            'figma',
            'notion',
            'airtable',
            'ramp',
            'plaid',
            'scale',
            'affirm',
            'brex',
            'gusto',
            'snyk',
            'attentive',
            'convoy',
            'lattice',
            'amplitude',
            'mixpanel',
            'benchling',
            'checkr'
        ]

    def search_jobs(
        self,
        query: str = "",
        location: str = "",
        num_results: int = 10,
        board_tokens: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search jobs across multiple Greenhouse job boards

        Args:
            query: Job title or keyword to filter (client-side filtering)
            location: Location filter (client-side filtering)
            num_results: Maximum number of results
            board_tokens: List of company board tokens (default: use predefined list)

        Returns:
            List of normalized job dictionaries
        """
        tokens_to_search = board_tokens or self.board_tokens
        all_jobs = []

        logger.info(f"🏢 Searching {len(tokens_to_search)} Greenhouse job boards...")

        for token in tokens_to_search:
            try:
                jobs = self._fetch_jobs_from_board(token)

                # Filter jobs by query and location (client-side)
                filtered_jobs = self._filter_jobs(jobs, query, location)
                all_jobs.extend(filtered_jobs)

                if len(all_jobs) >= num_results:
                    break

            except Exception as e:
                logger.debug(f"Failed to fetch from {token}: {str(e)}")
                continue

        logger.info(f"✅ Greenhouse returned {len(all_jobs[:num_results])} jobs")
        return all_jobs[:num_results]

    def _fetch_jobs_from_board(self, board_token: str) -> List[Dict]:
        """
        Fetch all jobs from a specific Greenhouse job board

        Args:
            board_token: Company's board token

        Returns:
            List of job dictionaries
        """
        url = f"{self.base_url}/{board_token}/jobs"

        params = {
            'content': 'true'  # Get full job descriptions
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                return []

            data = response.json()
            jobs_raw = data.get('jobs', [])

            # Normalize jobs
            normalized_jobs = []
            for job in jobs_raw:
                normalized = self._normalize_job(job, board_token)
                if normalized:
                    normalized_jobs.append(normalized)

            return normalized_jobs

        except requests.exceptions.RequestException as e:
            logger.debug(f"Request failed for {board_token}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching from {board_token}: {str(e)}")
            return []

    def _normalize_job(self, job: Dict, board_token: str) -> Optional[Dict]:
        """
        Normalize Greenhouse job data to CareerGenie format

        Args:
            job: Raw job data from Greenhouse
            board_token: Company board token

        Returns:
            Normalized job dictionary
        """
        try:
            # Extract location info
            location_data = job.get('location', {})
            location_name = location_data.get('name', '') if isinstance(location_data, dict) else str(location_data)

            # Parse location
            location_parts = location_name.split(',') if location_name else []
            city = location_parts[0].strip() if len(location_parts) > 0 else location_name
            state = location_parts[1].strip() if len(location_parts) > 1 else None

            # Check if remote
            is_remote = 'remote' in location_name.lower() or 'anywhere' in location_name.lower()

            # Extract departments
            departments = job.get('departments', [])
            department_names = [d.get('name') for d in departments if isinstance(d, dict) and d.get('name')]

            # Extract offices
            offices = job.get('offices', [])
            office_names = [o.get('name') for o in offices if isinstance(o, dict) and o.get('name')]

            # Build normalized job
            normalized = {
                'id': f"greenhouse_{job.get('id')}",
                'title': job.get('title', 'No Title'),
                'company': {
                    'name': board_token.replace('-', ' ').title(),
                    'logo': None,
                    'website': f"https://{board_token}.com"
                },
                'location': {
                    'city': city,
                    'state': state,
                    'formatted': location_name,
                    'remote': is_remote,
                    'coordinates': None
                },
                'description': job.get('content', '') or '',
                'employment': {
                    'type': self._infer_employment_type(job),
                    'level': self._infer_experience_level(job),
                    'department': department_names[0] if department_names else None
                },
                'requirements': [],
                'responsibilities': [],
                'benefits': [],
                'salary': None,
                'postedAt': job.get('updated_at', ''),
                'source': 'Greenhouse',
                'applyUrl': job.get('absolute_url', ''),
                'isActive': True,
                'metadata': {
                    'greenhouse_id': job.get('id'),
                    'board_token': board_token,
                    'departments': department_names,
                    'offices': office_names,
                    'internal_job_id': job.get('internal_job_id')
                }
            }

            return normalized

        except Exception as e:
            logger.warning(f"Failed to normalize Greenhouse job: {str(e)}")
            return None

    def _filter_jobs(self, jobs: List[Dict], query: str, location: str) -> List[Dict]:
        """
        Filter jobs by query and location (client-side filtering)

        Args:
            jobs: List of normalized job dictionaries
            query: Job title/keyword filter
            location: Location filter

        Returns:
            Filtered list of jobs
        """
        filtered = jobs

        # Filter by query
        if query:
            query_lower = query.lower()
            filtered = [
                job for job in filtered
                if query_lower in job.get('title', '').lower() or
                   query_lower in job.get('description', '').lower()
            ]

        # Filter by location
        if location:
            location_lower = location.lower()
            filtered = [
                job for job in filtered
                if location_lower in job.get('location', {}).get('formatted', '').lower() or
                   location_lower in job.get('location', {}).get('city', '').lower() or
                   job.get('location', {}).get('remote', False)
            ]

        return filtered

    def _infer_employment_type(self, job: Dict) -> str:
        """Infer employment type from job data"""
        title = job.get('title', '').lower()
        content = job.get('content', '').lower()

        if 'intern' in title or 'internship' in content:
            return 'Internship'
        elif 'contract' in title or 'contractor' in content:
            return 'Contract'
        elif 'part-time' in title or 'part time' in content:
            return 'Part-time'
        else:
            return 'Full-time'

    def _infer_experience_level(self, job: Dict) -> str:
        """Infer experience level from job data"""
        title = job.get('title', '').lower()
        content = job.get('content', '').lower()

        if any(word in title for word in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director']):
            return 'Senior'
        elif any(word in title for word in ['junior', 'jr.', 'entry', 'associate', 'graduate']):
            return 'Entry Level'
        elif any(word in title for word in ['intern', 'internship']):
            return 'Internship'
        else:
            return 'Mid Level'

    def add_board_token(self, token: str):
        """
        Add a new company board token to search

        Args:
            token: Company's Greenhouse board token
        """
        if token not in self.board_tokens:
            self.board_tokens.append(token)

    def get_board_tokens(self) -> List[str]:
        """Get list of all board tokens being searched"""
        return self.board_tokens.copy()
