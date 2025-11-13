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

# Comprehensive job categories covering ALL major fields
JOB_CATEGORIES = [
    # ========== TECHNOLOGY & ENGINEERING ==========
    # Software Development
    "Software Engineer", "Software Developer", "Full Stack Developer",
    "Frontend Developer", "Backend Developer", "Mobile Developer",
    "Web Developer", "Application Developer", "Systems Engineer",

    # Data & AI
    "Data Scientist", "Data Engineer", "Data Analyst",
    "Machine Learning Engineer", "AI Engineer", "Deep Learning Engineer",
    "Business Intelligence Analyst", "Analytics Manager",

    # DevOps & Infrastructure
    "DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer",
    "Systems Administrator", "Network Engineer", "Database Administrator",
    "Infrastructure Engineer", "Platform Engineer",

    # Security & Quality
    "Security Engineer", "Cybersecurity Analyst", "Information Security Manager",
    "QA Engineer", "Test Engineer", "Automation Engineer",

    # Specialized Tech
    "Blockchain Developer", "IoT Engineer", "Embedded Systems Engineer",
    "Game Developer", "AR/VR Developer", "Robotics Engineer",

    # ========== BUSINESS & MANAGEMENT ==========
    # Leadership
    "CEO", "CTO", "CFO", "COO", "VP Operations",
    "General Manager", "Director", "Team Lead",

    # Project & Product Management
    "Product Manager", "Project Manager", "Program Manager",
    "Scrum Master", "Agile Coach", "Product Owner",

    # Business Analysis
    "Business Analyst", "Management Consultant", "Strategy Consultant",
    "Operations Analyst", "Process Improvement Manager",

    # ========== SALES & MARKETING ==========
    # Sales
    "Sales Manager", "Account Manager", "Sales Representative",
    "Business Development Manager", "Sales Executive", "Inside Sales",
    "Account Executive", "Regional Sales Manager",

    # Marketing
    "Marketing Manager", "Digital Marketing Manager", "Brand Manager",
    "Content Marketing Manager", "Growth Marketing Manager",
    "Social Media Manager", "SEO Specialist", "Marketing Analyst",
    "Email Marketing Specialist", "Performance Marketing Manager",

    # ========== DESIGN & CREATIVE ==========
    "UX Designer", "UI Designer", "Product Designer",
    "Graphic Designer", "Visual Designer", "Motion Designer",
    "UX Researcher", "Creative Director", "Art Director",
    "Illustrator", "3D Designer", "Video Editor",

    # ========== HEALTHCARE & MEDICAL ==========
    # Clinical
    "Doctor", "Physician", "Surgeon", "Nurse",
    "Registered Nurse", "Nurse Practitioner", "Physician Assistant",
    "Pharmacist", "Dentist", "Optometrist",

    # Allied Health
    "Physical Therapist", "Occupational Therapist", "Speech Therapist",
    "Radiologic Technologist", "Medical Lab Technician",
    "Respiratory Therapist", "Dietitian", "Nutritionist",

    # Healthcare Administration
    "Healthcare Administrator", "Medical Office Manager",
    "Health Information Manager", "Clinical Research Coordinator",
    "Medical Billing Specialist", "Healthcare Consultant",

    # Mental Health
    "Psychologist", "Psychiatrist", "Counselor",
    "Social Worker", "Mental Health Therapist",

    # ========== HOSPITALITY & FOOD SERVICE ==========
    # Hotel Management
    "Hotel Manager", "Front Desk Manager", "Housekeeping Manager",
    "Revenue Manager", "Guest Services Manager", "Concierge",

    # Food & Beverage
    "Chef", "Executive Chef", "Sous Chef", "Cook",
    "Restaurant Manager", "Food Service Manager", "Catering Manager",
    "Bartender", "Waiter", "Server", "Barista",

    # Event Management
    "Event Manager", "Event Coordinator", "Wedding Planner",
    "Banquet Manager", "Conference Manager",

    # ========== FINANCE & ACCOUNTING ==========
    "Accountant", "Financial Analyst", "Finance Manager",
    "Controller", "Auditor", "Tax Accountant",
    "Investment Banker", "Financial Advisor", "Budget Analyst",
    "Payroll Specialist", "Bookkeeper", "Treasury Analyst",

    # ========== HUMAN RESOURCES ==========
    "HR Manager", "Recruiter", "Talent Acquisition Specialist",
    "HR Business Partner", "Compensation Analyst",
    "Training Manager", "Employee Relations Manager",
    "HR Generalist", "People Operations Manager",

    # ========== LEGAL ==========
    "Lawyer", "Attorney", "Legal Counsel", "Paralegal",
    "Legal Assistant", "Compliance Officer", "Contract Manager",

    # ========== EDUCATION & TRAINING ==========
    "Teacher", "Professor", "Instructor", "Tutor",
    "Training Manager", "Curriculum Developer",
    "Education Consultant", "School Administrator",
    "Academic Advisor", "Librarian",

    # ========== CUSTOMER SERVICE & SUPPORT ==========
    "Customer Service Representative", "Customer Support Specialist",
    "Customer Success Manager", "Technical Support Engineer",
    "Call Center Agent", "Help Desk Technician",

    # ========== OPERATIONS & LOGISTICS ==========
    "Operations Manager", "Supply Chain Manager", "Logistics Coordinator",
    "Warehouse Manager", "Procurement Manager", "Inventory Manager",
    "Transportation Manager", "Distribution Manager",

    # ========== MANUFACTURING & PRODUCTION ==========
    "Production Manager", "Plant Manager", "Manufacturing Engineer",
    "Quality Control Manager", "Maintenance Technician",
    "Production Supervisor", "Industrial Engineer",

    # ========== RETAIL & E-COMMERCE ==========
    "Store Manager", "Retail Manager", "Visual Merchandiser",
    "E-commerce Manager", "Retail Sales Associate",
    "Merchandising Manager", "Category Manager",

    # ========== REAL ESTATE & CONSTRUCTION ==========
    "Real Estate Agent", "Property Manager", "Leasing Consultant",
    "Construction Manager", "Civil Engineer", "Architect",
    "Project Engineer", "Estimator", "Site Supervisor",

    # ========== MEDIA & COMMUNICATIONS ==========
    "Content Writer", "Copywriter", "Technical Writer",
    "Journalist", "Editor", "Public Relations Manager",
    "Communications Manager", "Social Media Coordinator",

    # ========== SCIENCE & RESEARCH ==========
    "Research Scientist", "Lab Technician", "Biologist",
    "Chemist", "Environmental Scientist", "Research Associate",

    # ========== SKILLED TRADES ==========
    "Electrician", "Plumber", "HVAC Technician",
    "Mechanic", "Welder", "Carpenter", "Painter",

    # ========== TRANSPORTATION ==========
    "Driver", "Truck Driver", "Delivery Driver",
    "Pilot", "Flight Attendant", "Dispatcher",

    # ========== GOVERNMENT & PUBLIC SERVICE ==========
    "Policy Analyst", "Program Coordinator", "Public Administrator",
    "Urban Planner", "Emergency Management Specialist",

    # ========== NON-PROFIT & SOCIAL SERVICES ==========
    "Program Manager", "Grant Writer", "Community Outreach Coordinator",
    "Nonprofit Director", "Fundraising Manager",

    # ========== AGRICULTURE & ENVIRONMENT ==========
    "Agricultural Engineer", "Farm Manager", "Sustainability Consultant",
    "Environmental Consultant", "Conservation Specialist",

    # ========== ENTRY LEVEL & GENERAL ==========
    "Administrative Assistant", "Office Manager", "Executive Assistant",
    "Receptionist", "Data Entry Clerk", "Intern"
]


@app.task(name='tasks.job_fetching_tasks.fetch_global_jobs')
def fetch_global_jobs():
    """
    Fetch jobs for all regions - runs daily at 2 AM
    With intelligent rate limiting: 20-second delays to avoid 429 errors
    """
    import time
    import random

    print(f"[{datetime.now()}] Starting global job fetching with rate limiting...")
    print(f"Total categories: {len(JOB_CATEGORIES)}")
    print(f"Total locations: {sum(len(locs) for locs in LOCATIONS.values())}")
    print(f"Estimated duration: 6-8 hours (with 20s delays)")
    print()

    aggregator = JobAggregator()
    db = get_database()
    jobs_collection = db['jobs']

    total_saved = 0
    total_searches = 0
    failed_searches = 0

    for region, locations in LOCATIONS.items():
        print(f"\n📍 Region: {region}")

        for location in locations:
            for category in JOB_CATEGORIES:  # ALL 260 categories per location
                total_searches += 1

                try:
                    # Add delay BEFORE each search to respect rate limits
                    # Random delay between 15-25 seconds to avoid patterns
                    delay = random.uniform(15, 25)
                    print(f"\n   [{total_searches}/{len(JOB_CATEGORIES) * sum(len(locs) for locs in LOCATIONS.values())}] Waiting {delay:.1f}s before searching: {category} in {location}")
                    time.sleep(delay)

                    result = aggregator.search_all_sources(
                        query=category,
                        location=location,
                        limit_per_source=100  # 100 jobs per source (4 sources)
                    )

                    jobs = result.get('jobs', [])

                    # Save jobs to database
                    saved_count = 0
                    for job in jobs:
                        job_hash = f"{job.get('title', '').lower()}::{job.get('company', '').lower()}::{job.get('location', '').lower()}"

                        if not jobs_collection.find_one({'job_hash': job_hash}):
                            job['job_hash'] = job_hash
                            job['scraped_at'] = datetime.utcnow()
                            job['is_active'] = True
                            jobs_collection.insert_one(job)
                            saved_count += 1
                            total_saved += 1

                    print(f"   ✅ {category} in {location}: {len(jobs)} jobs retrieved, {saved_count} new jobs saved")

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

    print(f"\n✅ Global job fetching complete. Saved {total_saved} new jobs.")
    return {'total_saved': total_saved, 'timestamp': datetime.now().isoformat()}


@app.task(name='tasks.job_fetching_tasks.fetch_kenya_jobs')
def fetch_kenya_jobs():
    """
    Fetch jobs for Kenya only - runs twice daily
    Priority region for frequent updates
    """
    print(f"[{datetime.now()}] Starting Kenya job fetching...")

    aggregator = JobAggregator()
    db = get_database()
    jobs_collection = db['jobs']

    total_saved = 0

    for location in LOCATIONS['Kenya']:
        for category in JOB_CATEGORIES:
            try:
                result = aggregator.search_all_sources(
                    query=category,
                    location=location,
                    limit_per_source=100  # Fetch 100 jobs per source
                )

                jobs = result.get('jobs', [])

                for job in jobs:
                    job_hash = f"{job.get('title', '').lower()}::{job.get('company', '').lower()}::{job.get('location', '').lower()}"

                    if not jobs_collection.find_one({'job_hash': job_hash}):
                        job['job_hash'] = job_hash
                        job['scraped_at'] = datetime.utcnow()
                        job['is_active'] = True
                        jobs_collection.insert_one(job)
                        total_saved += 1

                print(f"   ✅ {category} in {location}: {len(jobs)} jobs")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
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
