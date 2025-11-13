#!/usr/bin/env python3
"""
Migration script to add source field to existing jobs
and mark them as active if they're recent.
"""

from config.database import get_database
from datetime import datetime, timedelta

def migrate_jobs():
    """Add source field to existing jobs and mark recent ones as active."""
    db = get_database()

    print("=" * 50)
    print("Job Database Migration")
    print("=" * 50)
    print()

    # Get current stats
    total_jobs = db.jobs.count_documents({})
    jobs_with_source = db.jobs.count_documents({'source': {'$exists': True}})
    jobs_without_source = db.jobs.count_documents({'source': {'$exists': False}})

    print(f"Current Database State:")
    print(f"  Total jobs: {total_jobs}")
    print(f"  Jobs with source: {jobs_with_source}")
    print(f"  Jobs without source: {jobs_without_source}")
    print()

    if jobs_without_source == 0:
        print("✅ All jobs already have source field!")
        return

    # Set default source for jobs without source field
    # These are from the old Jobs Search API
    print(f"Setting default source='jobs_search' for {jobs_without_source} jobs...")

    result = db.jobs.update_many(
        {'source': {'$exists': False}},
        {'$set': {'source': 'jobs_search'}}
    )

    print(f"✅ Updated {result.modified_count} jobs with source field")
    print()

    # Mark recent jobs (last 30 days) as active
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    print(f"Marking jobs from last 30 days as active...")

    active_result = db.jobs.update_many(
        {
            'scraped_at': {'$gte': thirty_days_ago},
            'is_active': False
        },
        {'$set': {'is_active': True}}
    )

    print(f"✅ Marked {active_result.modified_count} recent jobs as active")
    print()

    # Get updated stats
    print("Updated Database State:")
    total_active = db.jobs.count_documents({'is_active': True})
    total_inactive = db.jobs.count_documents({'is_active': False})

    print(f"  Total jobs: {total_jobs}")
    print(f"  Active jobs: {total_active}")
    print(f"  Inactive jobs: {total_inactive}")
    print()

    # Show jobs by source
    print("Jobs by source:")
    for source in ['jobs_search', 'linkedin', 'glassdoor', 'internships_api']:
        count = db.jobs.count_documents({'source': source, 'is_active': True})
        print(f"  {source}: {count} active jobs")

    print()
    print("=" * 50)
    print("Migration Complete!")
    print("=" * 50)

if __name__ == "__main__":
    migrate_jobs()
