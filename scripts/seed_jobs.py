"""Seed database with sample jobs for testing."""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from models.job import Job
from datetime import datetime, timedelta


def create_sample_jobs():
    """Create sample job postings."""

    sample_jobs = [
        {
            "title": "Senior Software Engineer",
            "company": {
                "name": "TechCorp Inc",
                "logo": None,
                "website": "https://techcorp.com",
                "size": "1000-5000",
                "industry": "Technology"
            },
            "description": "We're looking for a Senior Software Engineer to join our growing team. You'll work on cutting-edge projects using modern technologies and help shape the future of our platform.",
            "requirements": [
                "5+ years of software development experience",
                "Strong proficiency in Python and JavaScript",
                "Experience with React and Node.js",
                "Knowledge of cloud platforms (AWS, GCP, or Azure)",
                "Excellent problem-solving skills"
            ],
            "responsibilities": [
                "Design and implement scalable backend services",
                "Collaborate with cross-functional teams",
                "Mentor junior developers",
                "Participate in code reviews and architecture discussions"
            ],
            "salary": {
                "min": 120000,
                "max": 180000,
                "currency": "USD",
                "type": "annual"
            },
            "location": {
                "city": "San Francisco",
                "state": "CA",
                "remote": True,
                "coordinates": [37.7749, -122.4194]
            },
            "employment": {
                "type": "Full-time",
                "level": "Senior",
                "department": "Engineering"
            },
            "benefits": [
                "Health, dental, and vision insurance",
                "401(k) with company match",
                "Unlimited PTO",
                "Remote work options",
                "Learning and development budget"
            ],
            "applicationDeadline": datetime.utcnow() + timedelta(days=30),
            "isActive": True
        },
        {
            "title": "Frontend Developer",
            "company": {
                "name": "StartupHub",
                "logo": None,
                "website": "https://startuphub.io",
                "size": "50-200",
                "industry": "Technology"
            },
            "description": "Join our exciting startup as a Frontend Developer! Build beautiful, responsive user interfaces that delight our customers.",
            "requirements": [
                "3+ years of frontend development experience",
                "Expert in React and TypeScript",
                "Strong CSS/SASS skills",
                "Experience with modern build tools",
                "Portfolio of previous work"
            ],
            "responsibilities": [
                "Build and maintain frontend applications",
                "Implement responsive designs",
                "Optimize application performance",
                "Work closely with designers and backend developers"
            ],
            "salary": {
                "min": 90000,
                "max": 130000,
                "currency": "USD",
                "type": "annual"
            },
            "location": {
                "city": "Austin",
                "state": "TX",
                "remote": True,
                "coordinates": [30.2672, -97.7431]
            },
            "employment": {
                "type": "Full-time",
                "level": "Mid-level",
                "department": "Engineering"
            },
            "benefits": [
                "Competitive salary",
                "Stock options",
                "Health insurance",
                "Flexible work hours",
                "Modern office space"
            ],
            "applicationDeadline": datetime.utcnow() + timedelta(days=45),
            "isActive": True
        },
        {
            "title": "Data Scientist",
            "company": {
                "name": "DataAnalytics Pro",
                "logo": None,
                "website": "https://dataanalytics.com",
                "size": "500-1000",
                "industry": "Technology"
            },
            "description": "We're seeking a talented Data Scientist to extract insights from complex datasets and drive data-driven decision making.",
            "requirements": [
                "Master's or PhD in Computer Science, Statistics, or related field",
                "4+ years of data science experience",
                "Strong Python skills (pandas, scikit-learn, TensorFlow)",
                "Experience with SQL and data visualization tools",
                "Strong statistical analysis background"
            ],
            "responsibilities": [
                "Develop predictive models and algorithms",
                "Analyze large datasets to identify trends",
                "Present findings to stakeholders",
                "Collaborate with engineering teams on ML implementations"
            ],
            "salary": {
                "min": 130000,
                "max": 170000,
                "currency": "USD",
                "type": "annual"
            },
            "location": {
                "city": "New York",
                "state": "NY",
                "remote": False,
                "coordinates": [40.7128, -74.0060]
            },
            "employment": {
                "type": "Full-time",
                "level": "Senior",
                "department": "Data Science"
            },
            "benefits": [
                "Comprehensive health coverage",
                "401(k) matching",
                "Professional development",
                "Commuter benefits",
                "Gym membership"
            ],
            "applicationDeadline": datetime.utcnow() + timedelta(days=60),
            "isActive": True
        },
        {
            "title": "DevOps Engineer",
            "company": {
                "name": "CloudScale Systems",
                "logo": None,
                "website": "https://cloudscale.io",
                "size": "200-500",
                "industry": "Technology"
            },
            "description": "Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines.",
            "requirements": [
                "3+ years of DevOps experience",
                "Strong knowledge of AWS or GCP",
                "Experience with Docker and Kubernetes",
                "Proficiency in scripting (Python, Bash)",
                "Understanding of CI/CD best practices"
            ],
            "responsibilities": [
                "Maintain and improve cloud infrastructure",
                "Implement and manage CI/CD pipelines",
                "Monitor system performance and reliability",
                "Automate deployment processes"
            ],
            "salary": {
                "min": 110000,
                "max": 150000,
                "currency": "USD",
                "type": "annual"
            },
            "location": {
                "city": "Seattle",
                "state": "WA",
                "remote": True,
                "coordinates": [47.6062, -122.3321]
            },
            "employment": {
                "type": "Full-time",
                "level": "Mid-level",
                "department": "Infrastructure"
            },
            "benefits": [
                "Health and dental insurance",
                "401(k) plan",
                "Remote work",
                "Education reimbursement",
                "Paid parental leave"
            ],
            "applicationDeadline": datetime.utcnow() + timedelta(days=40),
            "isActive": True
        },
        {
            "title": "Product Manager",
            "company": {
                "name": "InnovateTech",
                "logo": None,
                "website": "https://innovatetech.com",
                "size": "500-1000",
                "industry": "Technology"
            },
            "description": "We're hiring a Product Manager to lead the development of our flagship product.",
            "requirements": [
                "5+ years of product management experience",
                "Strong technical background",
                "Experience with agile methodologies",
                "Excellent communication skills",
                "Track record of successful product launches"
            ],
            "responsibilities": [
                "Define product vision and strategy",
                "Gather and prioritize requirements",
                "Work with engineering and design teams",
                "Analyze product metrics and user feedback"
            ],
            "salary": {
                "min": 140000,
                "max": 190000,
                "currency": "USD",
                "type": "annual"
            },
            "location": {
                "city": "Boston",
                "state": "MA",
                "remote": False,
                "coordinates": [42.3601, -71.0589]
            },
            "employment": {
                "type": "Full-time",
                "level": "Senior",
                "department": "Product"
            },
            "benefits": [
                "Competitive salary and bonus",
                "Comprehensive benefits package",
                "Stock options",
                "Flexible schedule",
                "Professional growth opportunities"
            ],
            "applicationDeadline": datetime.utcnow() + timedelta(days=50),
            "isActive": True
        },
        {
            "title": "UX/UI Designer",
            "company": {
                "name": "DesignForward",
                "logo": None,
                "website": "https://designforward.com",
                "size": "50-200",
                "industry": "Technology"
            },
            "description": "Creative UX/UI Designer needed to craft beautiful and intuitive user experiences.",
            "requirements": [
                "4+ years of UX/UI design experience",
                "Expert in Figma, Sketch, or Adobe XD",
                "Strong portfolio demonstrating design skills",
                "Understanding of user-centered design principles",
                "Experience with user research and testing"
            ],
            "responsibilities": [
                "Create wireframes, prototypes, and high-fidelity designs",
                "Conduct user research and usability testing",
                "Collaborate with product and engineering teams",
                "Maintain design systems and guidelines"
            ],
            "salary": {
                "min": 95000,
                "max": 135000,
                "currency": "USD",
                "type": "annual"
            },
            "location": {
                "city": "Portland",
                "state": "OR",
                "remote": True,
                "coordinates": [45.5152, -122.6784]
            },
            "employment": {
                "type": "Full-time",
                "level": "Mid-level",
                "department": "Design"
            },
            "benefits": [
                "Health insurance",
                "401(k) matching",
                "Remote work",
                "Design tools and resources",
                "Conference attendance"
            ],
            "applicationDeadline": datetime.utcnow() + timedelta(days=35),
            "isActive": True
        }
    ]

    print("🌱 Seeding jobs...")

    created_count = 0
    for job_data in sample_jobs:
        try:
            job_id = Job.create_job(job_data)
            created_count += 1
            print(f"✓ Created job: {job_data['title']} at {job_data['company']['name']}")
        except Exception as e:
            print(f"✗ Failed to create job {job_data['title']}: {e}")

    print(f"\n✅ Successfully created {created_count} sample jobs!")
    return created_count


if __name__ == "__main__":
    try:
        from config.database import get_database

        # Connect to database
        db = get_database()
        print(f"Connected to database: {db.name}")

        # Seed jobs
        create_sample_jobs()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
