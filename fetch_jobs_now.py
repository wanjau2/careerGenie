#!/usr/bin/env python3
"""
Quick job fetching script to populate database with fresh jobs.
Fetches from all 4 sources for key locations.
"""

import os
from services.job_aggregator import JobAggregator
from config.database import get_database
from datetime import datetime

def fetch_and_store_jobs():
    """Fetch jobs and store in database."""

    # Initialize
    aggregator = JobAggregator()
    db = get_database()

    print("=" * 60)
    print("Fetching Jobs from All Sources")
    print("=" * 60)
    print()

    # Key locations to fetch jobs for
    locations = [
        "Nairobi, Kenya",
        "Mombasa, Kenya",
        "New York, NY, USA",
        "San Francisco, CA, USA",
        "London, UK",
        "Berlin, Germany",
        "Singapore",
        "Tokyo, Japan"
    ]

    # Key job categories
    categories = [
        "Software Engineer",
        "Data Scientist",
        "Product Manager",
        "Marketing Manager",
        "Sales Representative"
    ]

    total_jobs_saved = 0
    total_duplicates = 0

    for location in locations:
        print(f"\n{'='*60}")
        print(f"Location: {location}")
        print('='*60)

        for category in categories:
            print(f"\n  Searching: {category} in {location}")

            try:
                # Fetch from all sources
                result = aggregator.search_all_sources(
                    query=category,
                    location=location,
                    limit_per_source=100  # 100 per source as requested
                )

                jobs = result.get('jobs', [])
                source_stats = result.get('source_stats', {})

                # Show what we got from each source
                print(f"    Retrieved from sources:")
                for source, count in source_stats.items():
                    print(f"      • {source}: {count} jobs")

                # Save jobs to database
                jobs_saved = 0
                duplicates = 0

                for job in jobs:
                    # Add metadata
                    job['is_active'] = True
                    job['scraped_at'] = datetime.utcnow()

                    # Try to insert, skip if duplicate
                    try:
                        db.jobs.insert_one(job)
                        jobs_saved += 1
                    except Exception as e:
                        if 'duplicate key' in str(e).lower():
                            duplicates += 1
                        else:
                            print(f"      Error saving job: {e}")

                total_jobs_saved += jobs_saved
                total_duplicates += duplicates

                print(f"    💾 Saved: {jobs_saved} new jobs, {duplicates} duplicates")

            except Exception as e:
                print(f"    ❌ Error: {str(e)}")

        print(f"\n  Subtotal for {location}: {total_jobs_saved} jobs saved")

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total new jobs saved: {total_jobs_saved}")
    print(f"Total duplicates skipped: {total_duplicates}")
    print()

    # Show database stats
    print("Database Statistics:")
    total = db.jobs.count_documents({})
    active = db.jobs.count_documents({'is_active': True})

    print(f"  Total jobs in database: {total}")
    print(f"  Active jobs: {active}")
    print()

    print("Jobs by source:")
    for source in ['jobs_search', 'linkedin', 'glassdoor', 'internships_api']:
        count = db.jobs.count_documents({'source': source, 'is_active': True})
        print(f"  • {source}: {count} active jobs")

    print("\n" + "=" * 60)
    print("✅ Job fetching complete!")
    print("=" * 60)

if __name__ == "__main__":
    # Set API key from environment
    if 'RAPIDAPI_KEY' not in os.environ:
        print("⚠️  Warning: RAPIDAPI_KEY not set in environment")
        print("   Trying to load from .env file...")
        from dotenv import load_dotenv
        load_dotenv()

    fetch_and_store_jobs()
