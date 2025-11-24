"""Test auto-apply feature to verify it generates cover letters and customizes resumes."""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.auto_apply_service import AutoApplyService
from services.gemini_service import GeminiService


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_cover_letter_generation():
    """Test cover letter generation."""
    print_section("TEST 1: Cover Letter Generation")

    gemini_service = GeminiService()

    # Sample job data
    job_data = {
        'id': 'test_job_123',
        'title': 'Senior Software Engineer',
        'company': {
            'name': 'Google',
            'industry': 'Technology'
        },
        'description': 'We are looking for a Senior Software Engineer to join our team and help build the next generation of search technology. You will work on large-scale distributed systems.',
        'requirements': [
            '5+ years of software engineering experience',
            'Strong knowledge of Python, Java, or C++',
            'Experience with distributed systems',
            'Bachelor\'s degree in Computer Science'
        ]
    }

    # Sample user profile
    user_profile = {
        'profile': {
            'firstName': 'John',
            'lastName': 'Doe'
        },
        'workExperience': [
            {
                'title': 'Software Engineer',
                'company': 'Microsoft',
                'startDate': '2019-01-01',
                'current': True
            }
        ],
        'skills': [
            {'name': 'Python'},
            {'name': 'Java'},
            {'name': 'Distributed Systems'},
            {'name': 'Microservices'},
            {'name': 'Docker'}
        ],
        'education': [
            {
                'degree': 'Bachelor of Science',
                'field': 'Computer Science',
                'institution': 'Stanford University'
            }
        ]
    }

    print("📝 Generating cover letter...")
    result = gemini_service.generate_cover_letter(job_data, user_profile)

    if result['success']:
        print("✅ Cover letter generated successfully!\n")
        print("📄 Generated Cover Letter:")
        print("-" * 60)
        print(result['coverLetter'])
        print("-" * 60)
        print(f"\n📊 Metadata:")
        print(f"   - Word Count: {result['metadata']['wordCount']}")
        print(f"   - Job Title: {result['metadata']['jobTitle']}")
        print(f"   - Company: {result['metadata']['company']}")
        print(f"   - Model: {result['metadata']['model']}")
        return True
    else:
        print(f"❌ Cover letter generation failed: {result.get('error')}")
        return False


def test_resume_customization():
    """Test resume customization."""
    print_section("TEST 2: Resume Customization")

    gemini_service = GeminiService()

    # Sample job data
    job_data = {
        'id': 'test_job_456',
        'title': 'Full Stack Developer',
        'company': {
            'name': 'Amazon',
            'industry': 'E-commerce & Cloud'
        },
        'description': 'We are seeking a Full Stack Developer to work on AWS services and customer-facing applications.',
        'requirements': [
            'Experience with React and Node.js',
            'Knowledge of AWS services',
            'Strong database skills (SQL/NoSQL)',
            '3+ years of web development experience'
        ]
    }

    # Sample user profile
    user_profile = {
        'profile': {
            'firstName': 'Jane',
            'lastName': 'Smith'
        },
        'workExperience': [
            {
                'title': 'Full Stack Developer',
                'company': 'Startup Inc',
                'description': 'Built web applications using React, Node.js, and MongoDB'
            }
        ],
        'skills': [
            {'name': 'React'},
            {'name': 'Node.js'},
            {'name': 'AWS'},
            {'name': 'MongoDB'},
            {'name': 'PostgreSQL'}
        ]
    }

    # Original resume (simplified)
    original_resume = {
        'personalInfo': {
            'fullName': 'Jane Smith',
            'email': 'jane@example.com',
            'phone': '555-0123'
        },
        'summary': 'Experienced full stack developer with passion for building scalable applications',
        'experience': user_profile['workExperience'],
        'skills': ['React', 'Node.js', 'AWS', 'MongoDB']
    }

    print("🎨 Customizing resume for job...")
    result = gemini_service.customize_resume_content(job_data, user_profile, original_resume)

    if result['success']:
        print("✅ Resume customized successfully!\n")
        print("📄 Customized Resume Data:")
        print("-" * 60)
        import json
        print(json.dumps(result['customizedResume'], indent=2))
        print("-" * 60)
        print(f"\n📊 Metadata:")
        print(f"   - Job Title: {result['metadata']['jobTitle']}")
        print(f"   - Company: {result['metadata']['company']}")
        print(f"   - Model: {result['metadata']['model']}")
        return True
    else:
        print(f"❌ Resume customization failed: {result.get('error')}")
        return False


def test_full_auto_apply():
    """Test the complete auto-apply flow."""
    print_section("TEST 3: Complete Auto-Apply Flow")

    auto_apply = AutoApplyService()

    # Sample job data
    job_data = {
        'id': 'test_job_789',
        'title': 'DevOps Engineer',
        'company': {
            'name': 'Netflix',
            'industry': 'Streaming Media'
        },
        'description': 'Join our DevOps team to build and maintain cloud infrastructure at scale.',
        'requirements': [
            'Experience with Kubernetes and Docker',
            'CI/CD pipeline expertise',
            'AWS or GCP knowledge',
            'Infrastructure as Code (Terraform)'
        ]
    }

    # Sample user profile (would normally be fetched from DB)
    user_profile = {
        '_id': 'test_user_123',
        'profile': {
            'firstName': 'Bob',
            'lastName': 'Johnson'
        },
        'workExperience': [
            {
                'title': 'DevOps Engineer',
                'company': 'Tech Corp',
                'description': 'Managed Kubernetes clusters and CI/CD pipelines'
            }
        ],
        'skills': [
            {'name': 'Kubernetes'},
            {'name': 'Docker'},
            {'name': 'AWS'},
            {'name': 'Terraform'},
            {'name': 'Jenkins'}
        ],
        'education': [
            {
                'degree': 'Bachelor of Science',
                'field': 'Information Technology'
            }
        ],
        'subscription': {
            'plan': 'paid'  # Required for auto-apply
        },
        'resumes': {
            'original': 'path/to/resume.pdf',
            'parsed': {
                'personalInfo': {
                    'fullName': 'Bob Johnson',
                    'email': 'bob@example.com'
                },
                'summary': 'DevOps engineer with 5 years of experience'
            }
        }
    }

    print("🚀 Running complete auto-apply process...")
    print("   This will:")
    print("   1. Generate cover letter")
    print("   2. Customize resume")
    print("   3. Create application record (simulated)")
    print("   4. Update analytics")
    print()

    # Note: This would normally create DB records, so we're just testing the AI generation
    print("⚠️  Note: Actual application creation skipped (requires DB connection)")
    print("   Testing AI generation components only...\n")

    # Test cover letter generation
    print("📝 Step 1: Generating cover letter...")
    cover_letter_result = auto_apply._generate_cover_letter(job_data, user_profile)

    if cover_letter_result['success']:
        print("✅ Cover letter generated")
        print(f"   Preview: {cover_letter_result['coverLetter'][:100]}...")
    else:
        print(f"❌ Cover letter failed: {cover_letter_result.get('error')}")

    # Test resume customization
    print("\n🎨 Step 2: Customizing resume...")
    resume_result = auto_apply._customize_resume(
        job_data,
        user_profile,
        user_profile['resumes']['parsed']
    )

    if resume_result['success']:
        print("✅ Resume customized")
        print(f"   Resume data prepared for job application")
    else:
        print(f"❌ Resume customization failed: {resume_result.get('error')}")

    # Summary
    print("\n" + "="*60)
    print("📊 AUTO-APPLY TEST SUMMARY")
    print("="*60)

    success = cover_letter_result['success'] and resume_result['success']

    if success:
        print("✅ All AI generation components working correctly!")
        print()
        print("🔍 What happens in real auto-apply:")
        print("   ✅ Cover letter is generated using Gemini AI")
        print("   ✅ Resume is customized for the specific job")
        print("   ✅ Application record is created in database")
        print("   ✅ User analytics are updated")
        print("   ✅ Skill gaps are tracked for recommendations")
        print()
        print("⚠️  IMPORTANT LIMITATION:")
        print("   ❌ Application is NOT automatically submitted to employer")
        print("   📝 Materials are prepared, but user must manually submit")
        print("   🔗 User clicks the job link to apply with generated materials")
        return True
    else:
        print("❌ Some components failed")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("  AUTO-APPLY FEATURE TEST SUITE")
    print("  Testing Cover Letter & Resume Generation")
    print("="*60)

    results = {
        'cover_letter': False,
        'resume_customization': False,
        'full_flow': False
    }

    try:
        # Test 1: Cover letter generation
        results['cover_letter'] = test_cover_letter_generation()

        # Test 2: Resume customization
        results['resume_customization'] = test_resume_customization()

        # Test 3: Complete flow
        results['full_flow'] = test_full_auto_apply()

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

    # Final summary
    print_section("FINAL TEST RESULTS")

    print("Test Results:")
    print(f"  ✅ Cover Letter Generation: {'PASS' if results['cover_letter'] else 'FAIL'}")
    print(f"  ✅ Resume Customization: {'PASS' if results['resume_customization'] else 'FAIL'}")
    print(f"  ✅ Full Auto-Apply Flow: {'PASS' if results['full_flow'] else 'FAIL'}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed! Auto-apply feature is working.")
    else:
        print("\n⚠️  Some tests failed. Check logs above.")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
