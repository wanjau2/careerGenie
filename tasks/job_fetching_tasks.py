"""
Celery tasks for automated job fetching
Run daily to keep job database fresh
"""
from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_database
from services.job_aggregator import JobAggregator

# Initialize Celery
app = Celery(
    'job_fetching',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Celery configuration
app.conf.update(
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'fetch-global-jobs-daily': {
            'task': 'tasks.job_fetching_tasks.fetch_global_jobs',
            'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
        },
        'fetch-kenya-jobs-twice-daily': {
            'task': 'tasks.job_fetching_tasks.fetch_kenya_jobs',
            'schedule': crontab(hour='2,14', minute=0),  # Run at 2 AM and 2 PM
        },
    }
)

# Job locations by region - Expanded for 200+ jobs per field per country
LOCATIONS = {
    "Kenya": [
        "Nairobi, Kenya", "Mombasa, Kenya", "Kisumu, Kenya",
        "Nakuru, Kenya", "Eldoret, Kenya", "Remote, Kenya"
    ],
    "USA": [
        "New York, NY, USA", "San Francisco, CA, USA", "Austin, TX, USA",
        "Seattle, WA, USA", "Boston, MA, USA", "Chicago, IL, USA",
        "Los Angeles, CA, USA", "Denver, CO, USA", "Atlanta, GA, USA",
        "Miami, FL, USA", "Remote, USA"
    ],
    "Europe": [
        "London, UK", "Berlin, Germany", "Paris, France",
        "Amsterdam, Netherlands", "Dublin, Ireland", "Barcelona, Spain",
        "Munich, Germany", "Stockholm, Sweden", "Copenhagen, Denmark",
        "Milan, Italy", "Remote, Europe"
    ],
    "Asia": [
        "Singapore", "Tokyo, Japan", "Bangalore, India",
        "Mumbai, India", "Hong Kong", "Seoul, South Korea",
        "Shanghai, China", "Beijing, China", "Delhi, India",
        "Bangkok, Thailand", "Remote, Asia"
    ]
}

# COMPREHENSIVE JOB CATEGORIES - GLOBAL ALL INDUSTRIES
JOB_CATEGORIES = [
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


@app.task(name='tasks.job_fetching_tasks.fetch_global_jobs')
def fetch_global_jobs():
    """
    Fetch 200+ jobs per category across all regions - runs daily at 2 AM
    Strategy: Fetch from multiple locations per category to reach 200+ jobs
    With intelligent rate limiting: 15-25 second delays to avoid 429 errors
    """
    import time
    import random

    print(f"[{datetime.now()}] Starting global job fetching with rate limiting...")
    print(f"📊 Total categories: {len(JOB_CATEGORIES)} (ALL industries - Tech, Business, Healthcare, etc.)")
    print(f"📍 Total locations: {sum(len(locs) for locs in LOCATIONS.values())} across 4 regions")
    print(f"🎯 Goal: 200+ jobs per category")
    print(f"⏱️  Estimated duration: 8-12 hours (with 15-25s delays)")
    print(f"🌍 This is a GLOBAL job platform - fetching jobs for everyone!")
    print()

    aggregator = JobAggregator()
    db = get_database()
    jobs_collection = db['jobs']

    total_saved = 0
    total_searches = 0
    failed_searches = 0

    # NEW STRATEGY: For each category, fetch from ALL locations until we have 200+ jobs
    for category_index, category in enumerate(JOB_CATEGORIES, 1):
        print(f"\n{'='*70}")
        print(f"📋 CATEGORY {category_index}/{len(JOB_CATEGORIES)}: {category}")
        print(f"{'='*70}")

        category_jobs_count = 0
        category_target = 200

        # Fetch from all regions for this category
        for region, locations in LOCATIONS.items():
            if category_jobs_count >= category_target:
                print(f"   ✅ Target reached ({category_jobs_count} jobs), moving to next category")
                break

            for location in locations:
                if category_jobs_count >= category_target:
                    break

                total_searches += 1

                try:
                    # Add delay BEFORE each search to respect rate limits
                    delay = random.uniform(15, 25)
                    print(f"\n   [{category_jobs_count}/{category_target}] Waiting {delay:.1f}s before: {location}")
                    time.sleep(delay)

                    result = aggregator.search_all_sources(
                        query=category,
                        location=location,
                        limit_per_source=100  # 100 jobs per source (4 sources = 400 potential)
                    )

                    jobs = result.get('jobs', [])

                    # Save jobs to database
                    saved_count = 0
                    for job in jobs:
                        job_hash = f"{job.get('title', '').lower()}::{job.get('company', {}).get('name', '').lower()}::{job.get('location', {}).get('formatted', '').lower()}"

                        if not jobs_collection.find_one({'job_hash': job_hash}):
                            job['job_hash'] = job_hash
                            job['scrapedAt'] = datetime.utcnow()
                            job['isActive'] = True
                            job['category'] = category  # Tag with category
                            jobs_collection.insert_one(job)
                            saved_count += 1
                            total_saved += 1
                            category_jobs_count += 1

                    print(f"   ✅ {len(jobs)} fetched, {saved_count} new saved | Category total: {category_jobs_count}")

                except Exception as e:
                    error_msg = str(e)
                    failed_searches += 1

                    # Handle rate limiting errors specially
                    if "429" in error_msg:
                        print(f"   ⚠️  Rate limit hit! Waiting 60 seconds...")
                        time.sleep(60)
                    else:
                        print(f"   ❌ Error: {error_msg}")

                    continue

        print(f"\n   📊 {category}: {category_jobs_count} jobs saved")

    print(f"\n{'='*70}")
    print(f"✅ Global job fetching complete!")
    print(f"💾 Total new jobs saved: {total_saved}")
    print(f"📊 Total searches: {total_searches}")
    print(f"❌ Failed searches: {failed_searches}")
    print(f"{'='*70}")

    return {'total_saved': total_saved, 'timestamp': datetime.now().isoformat()}


@app.task(name='tasks.job_fetching_tasks.fetch_kenya_jobs')
def fetch_kenya_jobs():
    """
    Fetch 200+ jobs per category for Kenya - runs twice daily
    Priority region for frequent updates with 200+ jobs per category
    """
    import time
    import random

    print(f"[{datetime.now()}] Starting Kenya job fetching...")
    print(f"🎯 Goal: 200+ jobs per category for Kenya")
    print(f"📊 Categories: {len(JOB_CATEGORIES)}")
    print()

    aggregator = JobAggregator()
    db = get_database()
    jobs_collection = db['jobs']

    total_saved = 0
    kenya_locations = LOCATIONS['Kenya']

    # Fetch 200+ jobs per category
    for category_index, category in enumerate(JOB_CATEGORIES, 1):
        print(f"\n[{category_index}/{len(JOB_CATEGORIES)}] 📋 {category}")

        category_jobs_count = 0
        category_target = 200

        for location in kenya_locations:
            if category_jobs_count >= category_target:
                print(f"   ✅ Target reached ({category_jobs_count} jobs)")
                break

            try:
                # Small delay to avoid rate limits
                delay = random.uniform(10, 20)
                time.sleep(delay)

                result = aggregator.search_all_sources(
                    query=category,
                    location=location,
                    limit_per_source=100  # 100 per source × 4 sources = 400 potential
                )

                jobs = result.get('jobs', [])
                saved_count = 0

                for job in jobs:
                    job_hash = f"{job.get('title', '').lower()}::{job.get('company', {}).get('name', '').lower()}::{job.get('location', {}).get('formatted', '').lower()}"

                    if not jobs_collection.find_one({'job_hash': job_hash}):
                        job['job_hash'] = job_hash
                        job['scrapedAt'] = datetime.utcnow()
                        job['isActive'] = True
                        job['category'] = category
                        job['region'] = 'Kenya'
                        jobs_collection.insert_one(job)
                        saved_count += 1
                        total_saved += 1
                        category_jobs_count += 1

                print(f"   {location}: {saved_count} new | Total: {category_jobs_count}")

            except Exception as e:
                print(f"   ❌ Error in {location}: {str(e)}")
                continue

    print(f"\n✅ Kenya job fetching complete. Saved {total_saved} new jobs.")
    return {'total_saved': total_saved, 'timestamp': datetime.now().isoformat()}


@app.task(name='tasks.job_fetching_tasks.cleanup_old_jobs')
def cleanup_old_jobs(days_old=30):
    """
    Mark jobs older than N days as inactive
    Runs weekly to keep database clean
    """
    from datetime import timedelta

    db = get_database()
    jobs_collection = db['jobs']

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    result = jobs_collection.update_many(
        {
            'scraped_at': {'$lt': cutoff_date},
            'is_active': True
        },
        {
            '$set': {'is_active': False}
        }
    )

    print(f"✅ Marked {result.modified_count} old jobs as inactive")
    return {'deactivated': result.modified_count}


# Add cleanup task to schedule
app.conf.beat_schedule['cleanup-old-jobs-weekly'] = {
    'task': 'tasks.job_fetching_tasks.cleanup_old_jobs',
    'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Every Sunday at 3 AM
}


if __name__ == '__main__':
    # Test the tasks
    print("Testing job fetching tasks...")
    print("\n1. Testing Kenya jobs fetch:")
    result = fetch_kenya_jobs()
    print(f"Result: {result}")

    print("\n2. Testing cleanup:")
    result = cleanup_old_jobs(days_old=30)
    print(f"Result: {result}")
