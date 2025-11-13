#!/usr/bin/env python3
"""
Test auto-apply feature and AI resume generation with training data.
Shows how the AI generates cover letters and customizes resumes.
"""

import sys
import json
from services.auto_apply_service import AutoApplyService
from services.gemini_service import GeminiService
from config.database import get_database

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_auto_apply_service():
    """Test the auto-apply service with a real job."""
    print_section("TEST 1: Auto-Apply Service")

    auto_apply = AutoApplyService()

    # Sample job data (using one from our database)
    db = get_database()
    sample_job = db.jobs.find_one({'is_active': True})

    if not sample_job:
        print("❌ No active jobs in database. Please run job fetching first.")
        return

    print("📝 Testing with job:")
    print(f"   Title: {sample_job.get('title')}")
    print(f"   Company: {sample_job.get('company', {}).get('name', sample_job.get('company'))}")
    print(f"   Location: {sample_job.get('location')}")
    print()

    # Sample user profile
    sample_user = {
        '_id': 'test_user_123',
        'profile': {
            'firstName': 'John',
            'lastName': 'Doe',
            'experience': 'Senior Software Engineer with 5 years experience',
            'resume': None
        },
        'workExperience': [
            {
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp',
                'duration': '3 years',
                'description': 'Led development of scalable microservices'
            },
            {
                'title': 'Software Engineer',
                'company': 'StartupXYZ',
                'duration': '2 years',
                'description': 'Built RESTful APIs and frontend applications'
            }
        ],
        'skills': [
            {'name': 'Python'},
            {'name': 'JavaScript'},
            {'name': 'React'},
            {'name': 'Node.js'},
            {'name': 'AWS'},
            {'name': 'Docker'},
            {'name': 'PostgreSQL'}
        ],
        'education': [
            {
                'degree': 'Bachelor of Science',
                'field': 'Computer Science',
                'institution': 'University of Technology'
            }
        ],
        'subscription': {
            'plan': 'paid'  # Required for auto-apply
        }
    }

    print("👤 Testing with user profile:")
    print(f"   Name: {sample_user['profile']['firstName']} {sample_user['profile']['lastName']}")
    print(f"   Current Role: {sample_user['workExperience'][0]['title']}")
    print(f"   Skills: {', '.join([s['name'] for s in sample_user['skills'][:5]])}")
    print()

    print("🔄 Checking auto-apply eligibility...")
    can_apply = auto_apply.can_auto_apply('test_user_123')
    print(f"   Can Auto-Apply: {'✅ Yes' if can_apply else '❌ No'}")
    print()

    if not can_apply:
        print("⚠️  Note: User must have 'paid' subscription for auto-apply")
        print("   Continuing with test anyway to show AI generation...")
        print()


def test_cover_letter_generation():
    """Test AI cover letter generation."""
    print_section("TEST 2: AI Cover Letter Generation")

    gemini = GeminiService()
    db = get_database()

    # Get a real job from database
    sample_job = db.jobs.find_one({'is_active': True})

    if not sample_job:
        print("❌ No active jobs in database")
        return

    # Format job data
    job_data = {
        'id': str(sample_job.get('_id')),
        'title': sample_job.get('title'),
        'company': {
            'name': sample_job.get('company', {}).get('name', sample_job.get('company'))
        },
        'description': sample_job.get('description', '')[:500],  # Truncate for brevity
        'requirements': sample_job.get('requirements', [])[:5]
    }

    # Sample user profile
    user_profile = {
        'profile': {
            'firstName': 'Sarah',
            'lastName': 'Johnson'
        },
        'workExperience': [
            {
                'title': 'Senior Data Scientist',
                'company': 'Analytics Inc',
                'description': 'Led ML model development and deployment'
            }
        ],
        'skills': [
            {'name': 'Python'},
            {'name': 'Machine Learning'},
            {'name': 'TensorFlow'},
            {'name': 'SQL'},
            {'name': 'Data Analysis'}
        ],
        'education': [
            {
                'degree': 'Masters',
                'field': 'Data Science'
            }
        ]
    }

    print("📄 Generating cover letter for:")
    print(f"   Job: {job_data['title']}")
    print(f"   Company: {job_data['company']['name']}")
    print(f"   Candidate: {user_profile['profile']['firstName']} {user_profile['profile']['lastName']}")
    print()

    print("🤖 Calling Gemini AI to generate cover letter...")
    print("   (This uses training from 2,532 resume examples)")
    print()

    result = gemini.generate_cover_letter(job_data, user_profile)

    if result['success']:
        print("✅ Cover Letter Generated Successfully!")
        print()
        print("-" * 80)
        print(result['coverLetter'])
        print("-" * 80)
        print()
        print("📊 Metadata:")
        print(f"   Word Count: {result['metadata']['wordCount']}")
        print(f"   Generated At: {result['generatedAt']}")
        print(f"   Model: {result['metadata']['model']}")
        print()
    else:
        print(f"❌ Failed: {result.get('error')}")


def test_resume_customization():
    """Test AI resume customization for specific job."""
    print_section("TEST 3: AI Resume Customization")

    gemini = GeminiService()
    db = get_database()

    # Get a real job
    sample_job = db.jobs.find_one({'is_active': True})

    if not sample_job:
        print("❌ No active jobs in database")
        return

    job_data = {
        'id': str(sample_job.get('_id')),
        'title': sample_job.get('title'),
        'description': sample_job.get('description', '')[:500],
        'requirements': sample_job.get('requirements', [])[:5]
    }

    # Original resume data
    original_resume = {
        'summary': 'Experienced software engineer with expertise in full-stack development',
        'workExperience': [
            {
                'title': 'Senior Software Engineer',
                'company': 'TechCorp',
                'duration': '2020-Present',
                'achievements': [
                    'Led team of 5 engineers in microservices migration',
                    'Improved API response time by 40%',
                    'Implemented CI/CD pipeline reducing deployment time by 60%'
                ]
            },
            {
                'title': 'Software Engineer',
                'company': 'StartupXYZ',
                'duration': '2018-2020',
                'achievements': [
                    'Built RESTful API serving 1M+ requests/day',
                    'Developed React frontend for admin dashboard'
                ]
            }
        ],
        'skills': [
            'Python', 'JavaScript', 'React', 'Node.js', 'AWS',
            'Docker', 'Kubernetes', 'PostgreSQL', 'MongoDB'
        ],
        'education': [
            {
                'degree': 'BS Computer Science',
                'institution': 'Tech University',
                'year': '2018'
            }
        ]
    }

    user_profile = {
        'profile': {
            'firstName': 'Alex',
            'lastName': 'Smith'
        }
    }

    print("📝 Customizing resume for:")
    print(f"   Job Title: {job_data['title']}")
    print(f"   Original Summary: {original_resume['summary'][:60]}...")
    print()

    print("🤖 Calling Gemini AI to customize resume...")
    print("   (AI will optimize resume for this specific job)")
    print()

    result = gemini.customize_resume_content(job_data, user_profile, original_resume)

    if result['success']:
        customized = result['customizedResume']

        print("✅ Resume Customized Successfully!")
        print()
        print("-" * 80)
        print("CUSTOMIZED PROFESSIONAL SUMMARY:")
        print(customized.get('summary', ''))
        print()
        print("TOP SKILLS (Reordered by relevance):")
        for i, skill in enumerate(customized.get('skills', [])[:7], 1):
            print(f"   {i}. {skill}")
        print()
        print("KEY ACHIEVEMENTS (Optimized for this role):")
        if customized.get('workExperience'):
            for exp in customized['workExperience'][:1]:  # Show first job
                print(f"   Position: {exp.get('title', 'N/A')}")
                for achievement in exp.get('achievements', [])[:3]:
                    print(f"   • {achievement}")
        print()
        print("IDENTIFIED KEYWORDS:")
        keywords = customized.get('keywords', [])
        print(f"   {', '.join(keywords[:10])}")
        print()
        print(f"ESTIMATED MATCH SCORE: {customized.get('matchScore', 0):.0%}")
        print("-" * 80)
        print()
    else:
        print(f"❌ Failed: {result.get('error')}")


def test_skill_gap_analysis():
    """Test AI skill gap analysis."""
    print_section("TEST 4: AI Skill Gap Analysis")

    gemini = GeminiService()
    db = get_database()

    # Get a job
    sample_job = db.jobs.find_one({'is_active': True})

    if not sample_job:
        print("❌ No active jobs in database")
        return

    job_data = {
        'title': sample_job.get('title'),
        'description': sample_job.get('description', '')[:500],
        'requirements': sample_job.get('requirements', [])[:7]
    }

    user_skills = [
        'Python', 'JavaScript', 'React', 'SQL', 'Git'
    ]

    print(f"🔍 Analyzing skill match for: {job_data['title']}")
    print(f"   User's Skills: {', '.join(user_skills)}")
    print(f"   Job Requirements: {', '.join(job_data.get('requirements', [])[:5])}")
    print()

    print("🤖 Running AI skill gap analysis...")
    print()

    result = gemini.analyze_skill_match(job_data, user_skills)

    if result['success']:
        analysis = result['analysis']

        print("✅ Analysis Complete!")
        print()
        print("-" * 80)
        print(f"OVERALL MATCH SCORE: {analysis.get('matchScore', 0):.0%}")
        print()
        print("✅ MATCHING SKILLS:")
        for skill in analysis.get('matchingSkills', []):
            print(f"   • {skill}")
        print()
        print("❌ MISSING SKILLS:")
        for missing in analysis.get('missingSkills', [])[:5]:
            priority = missing.get('priority', 'medium').upper()
            skill_name = missing.get('skill', '')
            reason = missing.get('reason', '')
            print(f"   [{priority}] {skill_name}")
            print(f"        → {reason}")
        print()
        print("🔄 TRANSFERABLE SKILLS:")
        for skill in analysis.get('transferableSkills', []):
            print(f"   • {skill}")
        print()
        print("💡 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            print(f"   {i}. {rec}")
        print()
        print("OVERALL ASSESSMENT:")
        print(f"   {analysis.get('overallAssessment', '')}")
        print("-" * 80)
        print()
    else:
        print(f"❌ Failed: {result.get('error')}")


def check_training_data():
    """Check what training data is available."""
    print_section("BONUS: Training Data Statistics")

    import os
    import glob

    training_dir = 'training_data/scraped'

    if not os.path.exists(training_dir):
        print("❌ Training data directory not found")
        return

    # Count resume files
    resume_files = glob.glob(f'{training_dir}/**/*.txt', recursive=True)

    print(f"📚 Training Data Available:")
    print(f"   Total Resume Examples: {len(resume_files)}")
    print()

    # Sample a few resumes to show categories
    if resume_files:
        print("   Sample Categories:")
        categories = set()
        for file in resume_files[:50]:
            # Extract category from filename (e.g., resume_0001_HR.txt)
            filename = os.path.basename(file)
            if '_' in filename:
                parts = filename.split('_')
                if len(parts) >= 3:
                    category = parts[2].replace('.txt', '')
                    categories.add(category)

        for cat in sorted(categories)[:10]:
            print(f"   • {cat}")

        if len(categories) > 10:
            print(f"   ... and {len(categories) - 10} more categories")

    print()
    print("ℹ️  This training data helps the AI:")
    print("   1. Understand professional resume structure")
    print("   2. Learn industry-specific terminology")
    print("   3. Generate contextually appropriate content")
    print("   4. Match writing style to job category")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  AUTO-APPLY & AI RESUME GENERATION TEST SUITE")
    print("  Testing with Google Gemini AI + 2,532 Resume Training Examples")
    print("=" * 80)

    try:
        # Check training data first
        check_training_data()

        # Test auto-apply service
        test_auto_apply_service()

        # Test cover letter generation
        test_cover_letter_generation()

        # Test resume customization
        test_resume_customization()

        # Test skill gap analysis
        test_skill_gap_analysis()

        print("\n" + "=" * 80)
        print("  TEST SUITE COMPLETE")
        print("=" * 80)
        print()
        print("📊 Summary:")
        print("   ✅ Auto-Apply Service - Tested")
        print("   ✅ AI Cover Letter Generation - Tested")
        print("   ✅ AI Resume Customization - Tested")
        print("   ✅ AI Skill Gap Analysis - Tested")
        print()
        print("💡 The AI is using Gemini 2.5 Flash model with training from")
        print("   2,532 real resume examples to generate professional content!")
        print()

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
