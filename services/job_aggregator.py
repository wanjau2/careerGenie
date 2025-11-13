"""
Job Aggregation Service
Combines jobs from multiple sources: JSearch, LinkedIn, Glassdoor, Internships
"""
import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.jobs_search_api import JobsSearchAPIService
from services.linkedin_jobs_service import LinkedInJobsService
from services.glassdoor_service import GlassdoorService
from services.internships_service import InternshipsService

class JobAggregator:
    """Aggregates job listings from multiple sources"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize all job services"""
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.jobs_search = JobsSearchAPIService(api_key=self.api_key)
        self.linkedin = LinkedInJobsService(api_key=self.api_key)
        self.glassdoor = GlassdoorService(api_key=self.api_key)
        self.internships = InternshipsService(api_key=self.api_key)

    def search_all_sources(
        self,
        query: str,
        location: str = "",
        sources: Optional[List[str]] = None,
        limit_per_source: int = 20
    ) -> Dict[str, Any]:
        """
        Search jobs across all enabled sources in parallel

        Args:
            query: Job search query
            location: Location filter
            sources: List of sources to search (default: all)
            limit_per_source: Maximum results per source

        Returns:
            Dictionary with aggregated job listings
        """
        if sources is None:
            sources = ['jobs_search', 'linkedin', 'glassdoor', 'internships']

        print(f"\n🔍 Searching jobs across {len(sources)} sources...")
        print(f"   Query: {query}")
        print(f"   Location: {location or 'All locations'}")

        all_jobs = []
        source_stats = {}
        errors = []

        # Prepare search tasks
        tasks = []

        with ThreadPoolExecutor(max_workers=4) as executor:
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
        for source, count in source_stats.items():
            print(f"   • {source}: {count} jobs")
        print(f"   Total: {len(all_jobs)} jobs ({len(unique_jobs)} unique)")

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
            company = job.get('company', '').lower().strip()
            key = f"{title}::{company}"

            if key not in seen and title and company:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def get_jobs_by_source(self, source: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get jobs from a specific source

        Args:
            source: Source name (jobs_search, linkedin, glassdoor, internships)
            limit: Maximum number of results

        Returns:
            Dictionary with job listings
        """
        if source == 'jobs_search':
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
