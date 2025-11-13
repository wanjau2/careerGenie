#!/usr/bin/env python3
"""
Global Job Fetching Script
Fetches 300+ jobs for Kenya, USA, European countries, and Asian countries
Uses the new job aggregation service with all sources
"""
import os
import sys
import time
from datetime import datetime
from typing import List, Dict
from config.database import get_database
from services.job_aggregator import JobAggregator

# Job categories to search
JOB_CATEGORIES = [
    "Software Engineer",
    "Data Scientist",
    "Data Engineer",
    "Product Manager",
    "Marketing Manager",
    "Business Analyst",
    "Sales Representative",
    "Customer Success",
    "UX Designer",
    "Full Stack Developer",
    "Backend Developer",
    "Frontend Developer",
    "DevOps Engineer",
    "Cloud Architect",
    "Machine Learning Engineer"
]

# Target locations by region
LOCATIONS = {
    "Kenya": [
        "Nairobi, Kenya",
        "Mombasa, Kenya",
        "Kisumu, Kenya",
        "Kenya"
    ],
    "USA": [
        "New York, NY, USA",
        "San Francisco, CA, USA",
        "Austin, TX, USA",
        "Seattle, WA, USA",
        "Boston, MA, USA",
        "Chicago, IL, USA",
        "Los Angeles, CA, USA",
        "Remote, USA",
        "United States"
    ],
    "Europe": [
        "London, UK",
        "Berlin, Germany",
        "Paris, France",
        "Amsterdam, Netherlands",
        "Dublin, Ireland",
        "Barcelona, Spain",
        "Stockholm, Sweden",
        "Copenhagen, Denmark",
        "Remote, Europe"
    ],
    "Asia": [
        "Singapore",
        "Tokyo, Japan",
        "Bangalore, India",
        "Mumbai, India",
        "Hong Kong",
        "Seoul, South Korea",
        "Remote, Asia"
    ]
}

class GlobalJobFetcher:
    """Fetches jobs globally across multiple regions and sources"""

    def __init__(self):
        """Initialize job aggregator and database"""
        self.aggregator = JobAggregator()
        self.db = get_database()
        self.jobs_collection = self.db['jobs']
        self.stats = {
            'total_fetched': 0,
            'total_saved': 0,
            'duplicates': 0,
            'errors': 0,
            'by_region': {},
            'by_source': {}
        }

    def fetch_all_regions(self, target_per_region: int = 300):
        """
        Fetch jobs for all regions

        Args:
            target_per_region: Target number of jobs per region
        """
        print("=" * 70)
        print("GLOBAL JOB FETCHING STARTED")
        print("=" * 70)
        print(f"Target: {target_per_region} jobs per region")
        print(f"Regions: {list(LOCATIONS.keys())}")
        print(f"Job Sources: Jobs Search API, LinkedIn, Glassdoor, Internships")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        for region, locations in LOCATIONS.items():
            print(f"\n{'='*70}")
            print(f"REGION: {region}")
            print(f"{'='*70}")

            region_jobs = self.fetch_region(region, locations, target_per_region)
            self.stats['by_region'][region] = len(region_jobs)

            print(f"\n✅ {region}: Fetched {len(region_jobs)} jobs")
            time.sleep(2)  # Rate limiting between regions

        self.print_final_summary()

    def fetch_region(self, region: str, locations: List[str], target: int) -> List[Dict]:
        """Fetch jobs for a specific region"""
        all_jobs = []
        jobs_per_location = target // len(locations)

        for location in locations:
            print(f"\n📍 Location: {location}")
            location_jobs = self.fetch_location(location, jobs_per_location)
            all_jobs.extend(location_jobs)

            if len(all_jobs) >= target:
                print(f"   ✅ Target reached for {region}: {len(all_jobs)} jobs")
                break

            time.sleep(1)  # Rate limiting between locations

        return all_jobs

    def fetch_location(self, location: str, target: int) -> List[Dict]:
        """Fetch jobs for a specific location across multiple categories"""
        all_jobs = []
        categories_to_try = min(5, len(JOB_CATEGORIES))  # Try 5 categories per location

        for i, category in enumerate(JOB_CATEGORIES[:categories_to_try]):
            try:
                print(f"   🔍 Searching: {category}")

                # Use job aggregator to search all sources with limit=100
                result = self.aggregator.search_all_sources(
                    query=category,
                    location=location,
                    limit_per_source=100  # Fetch 100 jobs per source
                )

                jobs = result.get('jobs', [])
                source_stats = result.get('source_stats', {})

                # Track source statistics
                for source, count in source_stats.items():
                    if source not in self.stats['by_source']:
                        self.stats['by_source'][source] = 0
                    self.stats['by_source'][source] += count

                if jobs:
                    saved_count = self.save_jobs(jobs)
                    all_jobs.extend(jobs)
                    self.stats['total_fetched'] += len(jobs)
                    self.stats['total_saved'] += saved_count

                    print(f"      ✅ Found {len(jobs)} jobs ({saved_count} new)")
                else:
                    print(f"      ⚠️ No jobs found")

                time.sleep(0.5)  # Rate limiting between searches

            except Exception as e:
                print(f"      ❌ Error: {str(e)}")
                self.stats['errors'] += 1
                continue

        return all_jobs

    def save_jobs(self, jobs: List[Dict]) -> int:
        """
        Save jobs to database with duplicate detection

        Args:
            jobs: List of job dictionaries

        Returns:
            Number of jobs actually saved (excluding duplicates)
        """
        saved_count = 0

        for job in jobs:
            try:
                # Create unique identifier
                job_hash = self._create_job_hash(job)

                # Check if job already exists
                existing = self.jobs_collection.find_one({'job_hash': job_hash})

                if existing:
                    self.stats['duplicates'] += 1
                    continue

                # Add metadata
                job['job_hash'] = job_hash
                job['scraped_at'] = datetime.utcnow()
                job['is_active'] = True

                # Insert into database
                self.jobs_collection.insert_one(job)
                saved_count += 1

            except Exception as e:
                print(f"      ⚠️ Error saving job: {str(e)}")
                continue

        return saved_count

    def _create_job_hash(self, job: Dict) -> str:
        """Create unique hash for job based on title, company, location"""
        title = job.get('title', '').lower().strip()
        company = job.get('company', '').lower().strip()
        location = job.get('location', '').lower().strip()
        return f"{title}::{company}::{location}"

    def print_final_summary(self):
        """Print final statistics"""
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)

        print(f"\n📊 Total Statistics:")
        print(f"   • Total Jobs Fetched: {self.stats['total_fetched']}")
        print(f"   • New Jobs Saved: {self.stats['total_saved']}")
        print(f"   • Duplicates Skipped: {self.stats['duplicates']}")
        print(f"   • Errors Encountered: {self.stats['errors']}")

        print(f"\n🌍 By Region:")
        for region, count in self.stats['by_region'].items():
            print(f"   • {region}: {count} jobs")

        print(f"\n🔗 By Source:")
        for source, count in self.stats['by_source'].items():
            print(f"   • {source}: {count} jobs")

        # Get total jobs in database
        total_in_db = self.jobs_collection.count_documents({})
        print(f"\n💾 Total Jobs in Database: {total_in_db}")

        print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)


def main():
    """Main execution function"""
    try:
        fetcher = GlobalJobFetcher()
        fetcher.fetch_all_regions(target_per_region=300)
        print("\n✅ Global job fetching completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
