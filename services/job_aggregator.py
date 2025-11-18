"""
Job Aggregation Service
Combines jobs from multiple sources: Google Jobs (FREE), SerpAPI, LinkedIn, Glassdoor, and more
ENHANCED: Now includes FREE web scraping sources!
"""
import os
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all available job sources
from services.jobs_search_api import JobsSearchAPIService
from services.linkedin_jobs_service import LinkedInJobsService
from services.glassdoor_service import GlassdoorService
from services.internships_service import InternshipsService

# NEW: Free and enhanced sources
try:
    from services.google_jobs_direct import GoogleJobsDirect
    GOOGLE_JOBS_AVAILABLE = True
except ImportError:
    GOOGLE_JOBS_AVAILABLE = False

try:
    from services.serpapi_jobs import SerpAPIJobs
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

try:
    from services.careerjet_rest_api import CareerjetRestService
    CAREERJET_AVAILABLE = True
except ImportError:
    CAREERJET_AVAILABLE = False

try:
    from services.greenhouse_api import GreenhouseService
    GREENHOUSE_AVAILABLE = True
except ImportError:
    GREENHOUSE_AVAILABLE = False

logger = logging.getLogger(__name__)

class JobAggregator:
    """Aggregates job listings from multiple sources including FREE sources"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize all job services"""
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')

        # Original RapidAPI sources (may have issues)
        self.jobs_search = JobsSearchAPIService(api_key=self.api_key)
        self.linkedin = LinkedInJobsService(api_key=self.api_key)
        self.glassdoor = GlassdoorService(api_key=self.api_key)
        self.internships = InternshipsService(api_key=self.api_key)

        # NEW: Free Google Jobs Direct (NO API KEY NEEDED!)
        if GOOGLE_JOBS_AVAILABLE:
            self.google_jobs = GoogleJobsDirect()
            logger.info("✅ Google Jobs Direct (FREE) initialized")
        else:
            self.google_jobs = None
            logger.warning("⚠️ Google Jobs Direct not available")

        # NEW: SerpAPI (Official Google Jobs API - 100 free/month)
        if SERPAPI_AVAILABLE:
            self.serpapi = SerpAPIJobs()
            logger.info("✅ SerpAPI initialized")
        else:
            self.serpapi = None
            logger.warning("⚠️ SerpAPI not available")

        # NEW: Careerjet REST API (Python 3 compatible)
        if CAREERJET_AVAILABLE:
            self.careerjet = CareerjetRestService(locale='en_KE')  # Kenya locale
            logger.info("✅ Careerjet REST API initialized")
        else:
            self.careerjet = None
            logger.warning("⚠️ Careerjet not available")

        # NEW: Greenhouse (FREE - no API key needed!)
        if GREENHOUSE_AVAILABLE:
            self.greenhouse = GreenhouseService()
            logger.info("✅ Greenhouse (FREE) initialized")
        else:
            self.greenhouse = None
            logger.warning("⚠️ Greenhouse not available")

    def search_all_sources(
        self,
        query: str,
        location: str = "",
        sources: Optional[List[str]] = None,
        limit_per_source: int = 20
    ) -> Dict[str, Any]:
        """
        Search jobs across ALL enabled sources in parallel (including FREE sources)

        Args:
            query: Job search query
            location: Location filter
            sources: List of sources to search (default: all available)
            limit_per_source: Maximum results per source

        Returns:
            Dictionary with aggregated job listings
        """
        # Auto-detect available sources if not specified
        if sources is None:
            sources = []
            # PRIORITY 1: Free sources (no API key needed)
            if self.google_jobs:
                sources.append('google_jobs')
            if self.greenhouse:
                sources.append('greenhouse')
            # PRIORITY 2: SerpAPI (100 free/month)
            if self.serpapi:
                sources.append('serpapi')
            # PRIORITY 3: Careerjet
            if self.careerjet:
                sources.append('careerjet')
            # PRIORITY 4: RapidAPI sources (may have issues)
            sources.extend(['jobs_search', 'linkedin', 'glassdoor', 'internships'])

        print(f"\n🔍 Searching jobs across {len(sources)} sources...")
        print(f"   Query: {query}")
        print(f"   Location: {location or 'All locations'}")
        print(f"   Sources: {', '.join(sources)}")

        all_jobs = []
        source_stats = {}
        errors = []

        # Prepare search tasks
        tasks = []

        with ThreadPoolExecutor(max_workers=8) as executor:  # Increased from 4 to 8
            # NEW: Google Jobs Direct (FREE - highest priority)
            if 'google_jobs' in sources and self.google_jobs:
                tasks.append(
                    executor.submit(
                        self._search_google_jobs,
                        query, location, limit_per_source
                    )
                )

            # NEW: Greenhouse (FREE - no API key needed)
            if 'greenhouse' in sources and self.greenhouse:
                tasks.append(
                    executor.submit(
                        self._search_greenhouse,
                        query, location, limit_per_source
                    )
                )

            # NEW: SerpAPI (Official Google Jobs API)
            if 'serpapi' in sources and self.serpapi:
                tasks.append(
                    executor.submit(
                        self._search_serpapi,
                        query, location, limit_per_source
                    )
                )

            # NEW: Careerjet
            if 'careerjet' in sources and self.careerjet:
                tasks.append(
                    executor.submit(
                        self._search_careerjet,
                        query, location, limit_per_source
                    )
                )

            # Original RapidAPI sources
            if 'jobs_search' in sources:
                tasks.append(
                    executor.submit(
                        self._search_jobs_search,
                        query, location, limit_per_source
                    )
                )

            if 'linkedin' in sources:
                tasks.append(
                    executor.submit(
                        self._search_linkedin,
                        query, location, limit_per_source
                    )
                )

            if 'glassdoor' in sources:
                tasks.append(
                    executor.submit(
                        self._search_glassdoor,
                        query, location, limit_per_source
                    )
                )

            if 'internships' in sources:
                tasks.append(
                    executor.submit(
                        self._search_internships,
                        query, location, limit_per_source
                    )
                )

            # Collect results
            for future in as_completed(tasks):
                try:
                    result = future.result()
                    source = result.get('source', 'unknown')
                    jobs = result.get('jobs', [])

                    source_stats[source] = len(jobs)
                    all_jobs.extend(jobs)

                    if 'error' in result:
                        errors.append(f"{source}: {result['error']}")

                except Exception as e:
                    print(f"❌ Error in aggregation: {str(e)}")
                    errors.append(str(e))

        # Remove duplicates based on title + company
        unique_jobs = self._remove_duplicates(all_jobs)

        print(f"\n✅ Aggregation complete:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            icon = "🆓" if source in ['google_jobs', 'greenhouse', 'serpapi', 'careerjet'] else "💰"
            print(f"   {icon} {source}: {count} jobs")
        print(f"   📊 Total: {len(all_jobs)} jobs ({len(unique_jobs)} unique)")
        if errors:
            print(f"   ⚠️ Errors: {len(errors)}")

        return {
            'jobs': unique_jobs,
            'total': len(unique_jobs),
            'source_stats': source_stats,
            'errors': errors if errors else None
        }

    def _search_jobs_search(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search Jobs Search API"""
        try:
            jobs = self.jobs_search.search_jobs(query=query, location=location, limit=limit)
            # Jobs Search API returns a list, not a dict
            if isinstance(jobs, list):
                return {
                    'source': 'jobs_search',
                    'jobs': jobs
                }
            return {
                'source': 'jobs_search',
                'jobs': []
            }
        except Exception as e:
            print(f"❌ Jobs Search API error: {str(e)}")
            return {'source': 'jobs_search', 'jobs': [], 'error': str(e)}

    def _search_linkedin(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search LinkedIn Jobs API"""
        try:
            result = self.linkedin.search_jobs(
                query=query,
                location=location if location else "Worldwide",
                limit=limit
            )
            return {
                'source': 'linkedin',
                'jobs': result.get('jobs', [])
            }
        except Exception as e:
            print(f"❌ LinkedIn error: {str(e)}")
            return {'source': 'linkedin', 'jobs': [], 'error': str(e)}

    def _search_glassdoor(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search Glassdoor API"""
        try:
            result = self.glassdoor.search_jobs(query=query, location=location)
            jobs = result.get('jobs', [])[:limit]
            return {
                'source': 'glassdoor',
                'jobs': jobs
            }
        except Exception as e:
            print(f"❌ Glassdoor error: {str(e)}")
            return {'source': 'glassdoor', 'jobs': [], 'error': str(e)}

    def _search_internships(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search Internships API"""
        try:
            # Internships API may not support query/location filters
            result = self.internships.search_internships(query=query, location=location)
            jobs = result.get('jobs', [])[:limit]
            return {
                'source': 'internships',
                'jobs': jobs
            }
        except Exception as e:
            print(f"❌ Internships error: {str(e)}")
            return {'source': 'internships', 'jobs': [], 'error': str(e)}

    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title + company"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            # Create unique key from title and company
            title = job.get('title', '').lower().strip()

            # Handle both string and dict company formats
            company_data = job.get('company', {})
            if isinstance(company_data, dict):
                company = company_data.get('name', '').lower().strip()
            else:
                company = str(company_data).lower().strip()

            key = f"{title}::{company}"

            if key not in seen and title and company:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def _search_google_jobs(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search Google Jobs Direct (FREE - no API key needed)"""
        try:
            jobs = self.google_jobs.search_jobs(query=query, location=location, num_results=limit)
            return {
                'source': 'google_jobs',
                'jobs': jobs if isinstance(jobs, list) else []
            }
        except Exception as e:
            print(f"❌ Google Jobs error: {str(e)}")
            return {'source': 'google_jobs', 'jobs': [], 'error': str(e)}

    def _search_serpapi(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search SerpAPI (Official Google Jobs API)"""
        try:
            jobs = self.serpapi.search_jobs(query=query, location=location, num_results=limit)
            return {
                'source': 'serpapi',
                'jobs': jobs if isinstance(jobs, list) else []
            }
        except Exception as e:
            print(f"❌ SerpAPI error: {str(e)}")
            return {'source': 'serpapi', 'jobs': [], 'error': str(e)}

    def _search_careerjet(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search Careerjet API"""
        try:
            jobs = self.careerjet.search_jobs(query=query, location=location, limit=limit)
            return {
                'source': 'careerjet',
                'jobs': jobs if isinstance(jobs, list) else []
            }
        except Exception as e:
            print(f"❌ Careerjet error: {str(e)}")
            return {'source': 'careerjet', 'jobs': [], 'error': str(e)}

    def _search_greenhouse(self, query: str, location: str, limit: int) -> Dict[str, Any]:
        """Search Greenhouse Job Boards (FREE - no API key needed)"""
        try:
            jobs = self.greenhouse.search_jobs(query=query, location=location, num_results=limit)
            return {
                'source': 'greenhouse',
                'jobs': jobs if isinstance(jobs, list) else []
            }
        except Exception as e:
            print(f"❌ Greenhouse error: {str(e)}")
            return {'source': 'greenhouse', 'jobs': [], 'error': str(e)}

    def get_jobs_by_source(self, source: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get jobs from a specific source

        Args:
            source: Source name (google_jobs, serpapi, careerjet, jobs_search, linkedin, glassdoor, internships)
            limit: Maximum number of results

        Returns:
            Dictionary with job listings
        """
        if source == 'google_jobs' and self.google_jobs:
            jobs = self.google_jobs.search_jobs(query="", num_results=limit)
            return {'jobs': jobs if isinstance(jobs, list) else [], 'total': len(jobs) if isinstance(jobs, list) else 0}
        elif source == 'serpapi' and self.serpapi:
            jobs = self.serpapi.search_jobs(query="", num_results=limit)
            return {'jobs': jobs if isinstance(jobs, list) else [], 'total': len(jobs) if isinstance(jobs, list) else 0}
        elif source == 'careerjet' and self.careerjet:
            jobs = self.careerjet.search_jobs(query="", limit=limit)
            return {'jobs': jobs if isinstance(jobs, list) else [], 'total': len(jobs) if isinstance(jobs, list) else 0}
        elif source == 'jobs_search':
            jobs = self.jobs_search.search_jobs(query="", limit=limit)
            return {'jobs': jobs if isinstance(jobs, list) else [], 'total': len(jobs) if isinstance(jobs, list) else 0}
        elif source == 'linkedin':
            return self.linkedin.search_jobs(query="", limit=limit)
        elif source == 'glassdoor':
            return self.glassdoor.search_jobs(query="")
        elif source == 'internships':
            return self.internships.get_active_internships()
        else:
            return {'jobs': [], 'total': 0, 'error': 'Invalid source'}
