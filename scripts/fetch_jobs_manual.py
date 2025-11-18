#!/usr/bin/env python3
"""
Manual Job Fetching Script
==========================
Fallback script to fetch jobs manually when Celery is not running.
This script does exactly what the Celery tasks do, but can be run on-demand.

Usage:
    python scripts/fetch_jobs_manual.py --region kenya
    python scripts/fetch_jobs_manual.py --region all
    python scripts/fetch_jobs_manual.py --region usa --categories "Data Engineer,Software Engineer"
    python scripts/fetch_jobs_manual.py --cleanup  # Clean up old jobs
"""
import os
import sys
import argparse
import time
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config.database import get_database
from services.job_aggregator import JobAggregator

# Job locations by region
LOCATIONS = {
    "kenya": [
        "Nairobi, Kenya", "Mombasa, Kenya", "Kisumu, Kenya",
        "Nakuru, Kenya", "Eldoret, Kenya", "Remote, Kenya"
    ],
    "usa": [
        "New York, NY, USA", "San Francisco, CA, USA", "Austin, TX, USA",
        "Seattle, WA, USA", "Boston, MA, USA", "Chicago, IL, USA",
        "Los Angeles, CA, USA", "Denver, CO, USA", "Atlanta, GA, USA",
        "Miami, FL, USA", "Remote, USA"
    ],
    "europe": [
        "London, UK", "Berlin, Germany", "Paris, France",
        "Amsterdam, Netherlands", "Dublin, Ireland", "Barcelona, Spain",
        "Munich, Germany", "Stockholm, Sweden", "Copenhagen, Denmark",
        "Milan, Italy", "Remote, Europe"
    ],
    "asia": [
        "Singapore", "Tokyo, Japan", "Bangalore, India",
        "Mumbai, India", "Hong Kong", "Seoul, South Korea",
        "Shanghai, China", "Beijing, China", "Delhi, India",
        "Bangkok, Thailand", "Remote, Asia"
    ]
}

# COMPREHENSIVE JOB CATEGORIES - GLOBAL ALL INDUSTRIES
# This ensures we fetch jobs across ALL sectors, not just tech
DEFAULT_CATEGORIES = [
    # ========== TECH & IT ==========
    "Software Engineer", "Software Developer", "Web Developer",
    "Frontend Developer", "Backend Developer", "Full Stack Developer",
    "Mobile App Developer", "Android Developer", "iOS Developer",
    "DevOps Engineer", "Cloud Engineer", "Data Scientist",
    "Data Analyst", "Machine Learning Engineer", "AI Engineer",
    "Database Administrator", "System Administrator", "Network Engineer",
    "Cybersecurity Analyst", "QA Engineer", "QA Tester",
    "Product Manager", "Product Owner", "UI/UX Designer",
    "UX Researcher", "IT Support Specialist", "IT Technician",
    "Solutions Architect", "Business Intelligence Analyst",
    "Computer Technician", "Game Developer", "Blockchain Developer",
    "Salesforce Administrator", "SAP Consultant", "ERP Consultant",
    "IT Project Manager", "Technical Writer", "Scrum Master",
    "Agile Coach",

    # ========== BUSINESS, FINANCE & MANAGEMENT ==========
    "Accountant", "Auditor", "Financial Analyst",
    "Business Analyst", "Operations Manager", "Project Manager",
    "Entrepreneur", "CEO", "COO", "CFO",
    "Procurement Officer", "Logistics Manager", "Supply Chain Manager",
    "Credit Analyst", "Investment Analyst", "Risk Analyst",
    "Bank Teller", "Loan Officer", "Relationship Manager",
    "Compliance Officer", "Economist", "Management Consultant",
    "HR Manager", "HR Officer", "Recruiter",
    "Talent Acquisition Specialist", "Administrative Assistant",
    "Executive Assistant", "Office Manager", "Payroll Officer",

    # ========== SALES, MARKETING & CUSTOMER SERVICE ==========
    "Sales Executive", "Sales Representative", "Sales Manager",
    "Marketing Manager", "Digital Marketer", "Social Media Manager",
    "Content Writer", "Copywriter", "SEO Specialist",
    "SEM Specialist", "Brand Manager", "Growth Manager",
    "Customer Service Representative", "Call Center Agent",
    "Customer Success Manager", "Account Manager",
    "Key Account Manager", "Telemarketer",

    # ========== CREATIVE, MEDIA & DESIGN ==========
    "Graphic Designer", "Video Editor", "Photographer",
    "Videographer", "Animator", "Motion Graphics Designer",
    "Illustrator", "Creative Director", "Sound Engineer",
    "Music Producer", "Art Director", "Fashion Designer",
    "Interior Designer", "Content Creator", "Influencer",
    "Editor", "Journalist", "TV Presenter",

    # ========== ENGINEERING & TECHNICAL FIELDS ==========
    "Mechanical Engineer", "Electrical Engineer", "Civil Engineer",
    "Structural Engineer", "Chemical Engineer", "Petroleum Engineer",
    "Aerospace Engineer", "Industrial Engineer", "Automotive Engineer",
    "Mechatronics Engineer", "Biomedical Engineer",
    "Environmental Engineer", "CAD Designer", "Architect",
    "Quantity Surveyor", "Surveyor",

    # ========== HEALTH & MEDICAL ==========
    "Doctor", "Nurse", "Pharmacist",
    "Lab Technician", "Radiologist", "Psychologist",
    "Therapist", "Surgeon", "Nutritionist",
    "Dentist", "Dental Assistant", "Optometrist",
    "Physiotherapist", "Clinical Officer", "Medical Assistant",

    # ========== EDUCATION ==========
    "Teacher", "Lecturer", "Professor",
    "Tutor", "Academic Advisor", "Curriculum Developer",
    "Librarian", "Researcher", "Instructional Designer",

    # ========== LAW, GOVERNMENT & ADMINISTRATION ==========
    "Lawyer", "Advocate", "Paralegal",
    "Legal Assistant", "Judge", "Legal Counsel",
    "Policy Analyst", "Government Officer", "Diplomat",
    "Customs Officer", "Immigration Officer",
    "Public Relations Officer", "Security Officer",

    # ========== HOSPITALITY, FOOD & TRAVEL ==========
    "Chef", "Cook", "Waiter",
    "Bartender", "Hotel Manager", "Housekeeper",
    "Tour Guide", "Travel Agent", "Event Planner",
    "Event Coordinator", "Receptionist",

    # ========== FIELD, LABOUR & GENERAL WORK ==========
    "Driver", "Mechanic", "Electrician",
    "Plumber", "Carpenter", "Mason",
    "Welder", "Technician", "Security Guard",
    "Cleaner", "Gardener", "Warehouse Worker",
    "Forklift Operator",

    # ========== OTHER COMMON MODERN ROLES ==========
    "Virtual Assistant", "Freelancer", "Data Entry Clerk",
    "Research Assistant", "Business Development Manager",
    "Community Manager", "Operations Coordinator",
    "E-commerce Manager", "Product Designer",
    "Marketplace Specialist", "Fulfillment Associate",
    "Online Tutor", "Fleet Manager", "Assistant"
]


def fetch_jobs_for_region(region_name, categories=None, delay_range=(15, 25), limit_per_source=100, jobs_per_category=200):
    """
    Fetch jobs for a specific region with 200+ jobs per category.

    Args:
        region_name: Region name (kenya, usa, europe, asia, all)
        categories: List of job categories (default: DEFAULT_CATEGORIES)
        delay_range: Tuple of (min, max) seconds to delay between requests
        limit_per_source: Max jobs per source API
        jobs_per_category: Target number of jobs per category (default: 200)

    Returns:
        dict: Statistics about the fetch operation
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES

    # Handle 'all' region
    regions_to_fetch = {}
    if region_name.lower() == 'all':
        regions_to_fetch = LOCATIONS
    else:
        region_key = region_name.lower()
        if region_key not in LOCATIONS:
            print(f"❌ Invalid region: {region_name}")
            print(f"   Available regions: {', '.join(LOCATIONS.keys())}, all")
            return None
        regions_to_fetch = {region_key: LOCATIONS[region_key]}

    print("=" * 70)
    print("🚀 MANUAL JOB FETCHING SCRIPT - 200+ JOBS PER CATEGORY")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Regions: {', '.join(regions_to_fetch.keys())}")
    print(f"📋 Categories: {len(categories)}")
    print(f"🎯 Target: {jobs_per_category} jobs per category")
    print(f"⏱️  Delay: {delay_range[0]}-{delay_range[1]}s between requests")
    print(f"🔢 Limit: {limit_per_source} jobs per source per request")
    print("=" * 70)

    aggregator = JobAggregator()
    db = get_database()
    jobs_collection = db['jobs']

    total_saved = 0
    total_searches = 0
    failed_searches = 0
    start_time = datetime.now()

    # NEW STRATEGY: Fetch per category across all locations until target is reached
    for category_index, category in enumerate(categories, 1):
        print(f"\n{'='*70}")
        print(f"📋 CATEGORY {category_index}/{len(categories)}: {category}")
        print(f"{'='*70}")

        category_jobs_count = 0

        # Fetch from all regions for this category
        for region, locations in regions_to_fetch.items():
            if category_jobs_count >= jobs_per_category:
                print(f"   ✅ Target reached ({category_jobs_count} jobs), moving to next category")
                break

            print(f"\n   📍 Region: {region}")

            for location in locations:
                if category_jobs_count >= jobs_per_category:
                    break

                total_searches += 1

                try:
                    # Add delay to respect rate limits
                    delay = random.uniform(*delay_range)
                    print(f"   [{category_jobs_count}/{jobs_per_category}] ⏳ {delay:.1f}s before: {location}")
                    time.sleep(delay)

                    # Fetch jobs
                    result = aggregator.search_all_sources(
                        query=category,
                        location=location,
                        limit_per_source=limit_per_source
                    )

                    jobs = result.get('jobs', [])

                    # Save to database
                    saved_count = 0
                    for job in jobs:
                        # Create unique hash
                        job_hash = f"{job.get('title', '').lower()}::{job.get('company', {}).get('name', '').lower()}::{job.get('location', {}).get('formatted', '').lower()}"

                        # Check if job already exists
                        if not jobs_collection.find_one({'job_hash': job_hash}):
                            job['job_hash'] = job_hash
                            job['scrapedAt'] = datetime.utcnow()
                            job['isActive'] = True
                            job['category'] = category
                            job['region'] = region
                            # Keep the source field from the job (already set by aggregator)
                            # Don't overwrite it with source_stats
                            jobs_collection.insert_one(job)
                            saved_count += 1
                            total_saved += 1
                            category_jobs_count += 1

                    print(f"   ✅ {len(jobs)} fetched, {saved_count} new | Category total: {category_jobs_count}")

                except Exception as e:
                    error_msg = str(e)
                    failed_searches += 1

                    # Handle rate limiting
                    if "429" in error_msg:
                        print(f"   ⚠️  Rate limit! Waiting 60s...")
                        time.sleep(60)
                    else:
                        print(f"   ❌ Error: {error_msg[:100]}")

        print(f"\n   📊 {category}: {category_jobs_count} jobs saved")

    # Summary
    duration = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Total searches: {total_searches}")
    print(f"❌ Failed searches: {failed_searches}")
    print(f"💾 New jobs saved: {total_saved}")
    print(f"⏱️  Duration: {duration}")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return {
        'total_searches': total_searches,
        'failed_searches': failed_searches,
        'total_saved': total_saved,
        'duration': str(duration),
        'timestamp': datetime.now().isoformat()
    }


def cleanup_old_jobs(days_old=30):
    """
    Mark jobs older than N days as inactive.

    Args:
        days_old: Number of days after which jobs are considered old

    Returns:
        dict: Cleanup statistics
    """
    print("=" * 70)
    print("🧹 CLEANUP OLD JOBS")
    print("=" * 70)
    print(f"📅 Marking jobs older than {days_old} days as inactive...")

    db = get_database()
    jobs_collection = db['jobs']

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    result = jobs_collection.update_many(
        {
            'scrapedAt': {'$lt': cutoff_date},
            'isActive': True
        },
        {
            '$set': {'isActive': False, 'deactivatedAt': datetime.utcnow()}
        }
    )

    print(f"✅ Marked {result.modified_count} jobs as inactive")
    print("=" * 70)

    return {
        'deactivated': result.modified_count,
        'cutoff_date': cutoff_date.isoformat(),
        'timestamp': datetime.now().isoformat()
    }


def show_stats():
    """Display current database statistics."""
    db = get_database()
    jobs_collection = db['jobs']

    total_jobs = jobs_collection.count_documents({})
    active_jobs = jobs_collection.count_documents({'isActive': True})
    inactive_jobs = jobs_collection.count_documents({'isActive': False})

    # Jobs by city
    city_pipeline = [
        {'$match': {'isActive': True}},
        {'$group': {'_id': '$location.city', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    cities = list(jobs_collection.aggregate(city_pipeline))

    # Jobs by category (based on title keywords)
    category_keywords = {
        'Data Engineer': ['data engineer'],
        'Data Analyst': ['data analyst'],
        'Software Engineer': ['software engineer', 'software developer'],
        'Machine Learning': ['machine learning', 'ml engineer', 'ai engineer'],
        'Business Intelligence': ['business intelligence', 'bi analyst', 'bi developer'],
        'DevOps': ['devops', 'cloud engineer', 'sre'],
        'Product Manager': ['product manager'],
    }

    category_counts = {}
    for category, keywords in category_keywords.items():
        regex_pattern = '|'.join(keywords)
        count = jobs_collection.count_documents({
            'title': {'$regex': regex_pattern, '$options': 'i'},
            'isActive': True
        })
        if count > 0:
            category_counts[category] = count

    print("=" * 70)
    print("📊 DATABASE STATISTICS")
    print("=" * 70)
    print(f"Total jobs: {total_jobs}")
    print(f"Active jobs: {active_jobs}")
    print(f"Inactive jobs: {inactive_jobs}")

    print(f"\n📍 Top cities:")
    for city_doc in cities:
        city = city_doc['_id'] or 'Unknown'
        count = city_doc['count']
        print(f"  • {city}: {count}")

    if category_counts:
        print(f"\n💼 Jobs by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {category}: {count}")

    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manual job fetching script - fallback for Celery tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch jobs for Kenya
  python scripts/fetch_jobs_manual.py --region kenya

  # Fetch jobs for all regions (takes 6-8 hours!)
  python scripts/fetch_jobs_manual.py --region all

  # Fetch specific categories for USA
  python scripts/fetch_jobs_manual.py --region usa --categories "Data Engineer,Software Engineer"

  # Quick fetch with minimal delay (use carefully to avoid rate limits)
  python scripts/fetch_jobs_manual.py --region kenya --quick

  # Clean up old jobs
  python scripts/fetch_jobs_manual.py --cleanup

  # Show database statistics
  python scripts/fetch_jobs_manual.py --stats
        """
    )

    parser.add_argument('--region', type=str, choices=['kenya', 'usa', 'europe', 'asia', 'all'],
                        help='Region to fetch jobs for')
    parser.add_argument('--categories', type=str,
                        help='Comma-separated list of job categories')
    parser.add_argument('--quick', action='store_true',
                        help='Use shorter delays (5-10s) - use carefully!')
    parser.add_argument('--cleanup', action='store_true',
                        help='Clean up old jobs (mark as inactive)')
    parser.add_argument('--cleanup-days', type=int, default=30,
                        help='Days after which jobs are considered old (default: 30)')
    parser.add_argument('--stats', action='store_true',
                        help='Show database statistics')
    parser.add_argument('--limit', type=int, default=100,
                        help='Limit jobs per source (default: 100)')
    parser.add_argument('--jobs-per-category', type=int, default=200,
                        help='Target jobs per category (default: 200)')

    args = parser.parse_args()

    # Show stats
    if args.stats:
        show_stats()
        return

    # Cleanup
    if args.cleanup:
        cleanup_old_jobs(args.cleanup_days)
        return

    # Fetch jobs
    if not args.region:
        parser.print_help()
        print("\n❌ Error: Either --region, --cleanup, or --stats is required")
        sys.exit(1)

    # Parse categories
    categories = None
    if args.categories:
        categories = [cat.strip() for cat in args.categories.split(',')]

    # Set delay range
    delay_range = (5, 10) if args.quick else (15, 25)

    # Fetch jobs
    result = fetch_jobs_for_region(
        args.region,
        categories=categories,
        delay_range=delay_range,
        limit_per_source=args.limit,
        jobs_per_category=args.jobs_per_category
    )

    if result:
        print(f"\n✅ Job fetching completed successfully!")
        print(f"💾 Saved {result['total_saved']} new jobs to database")


if __name__ == '__main__':
    main()
