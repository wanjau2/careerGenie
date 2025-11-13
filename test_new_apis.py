#!/usr/bin/env python3
"""
Test script for all new API integrations
Tests: LinkedIn, Glassdoor, Internships, Udemy Free, Job Aggregator
"""
import sys
from services.linkedin_jobs_service import LinkedInJobsService
from services.glassdoor_service import GlassdoorService
from services.internships_service import InternshipsService
from services.udemy_free_service import UdemyFreeService
from services.job_aggregator import JobAggregator
from services.course_aggregation import CourseAggregationService

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_linkedin():
    """Test LinkedIn Jobs API"""
    print_header("TEST 1: LinkedIn Jobs API")
    try:
        linkedin = LinkedInJobsService()
        result = linkedin.search_jobs(
            query="Software Engineer",
            location="Nairobi, Kenya",
            limit=5
        )

        jobs = result.get('jobs', [])
        print(f"✅ LinkedIn API Working!")
        print(f"   Found: {len(jobs)} jobs")

        if jobs:
            print("\n   Sample Jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"      Location: {job.get('location', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ LinkedIn API Error: {str(e)}")
        return False

def test_glassdoor():
    """Test Glassdoor API"""
    print_header("TEST 2: Glassdoor Real-Time API")
    try:
        glassdoor = GlassdoorService()
        result = glassdoor.search_jobs(
            query="Data Scientist",
            location="New York, NY"
        )

        jobs = result.get('jobs', [])
        print(f"✅ Glassdoor API Working!")
        print(f"   Found: {len(jobs)} jobs")

        if jobs:
            print("\n   Sample Jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"      Location: {job.get('location', 'N/A')}")
                rating = job.get('company_rating', 0)
                if rating:
                    print(f"      Company Rating: {rating}/5.0")

        return True

    except Exception as e:
        print(f"❌ Glassdoor API Error: {str(e)}")
        return False

def test_internships():
    """Test Internships API"""
    print_header("TEST 3: Internships API")
    try:
        internships = InternshipsService()
        result = internships.get_active_internships(days=7)

        jobs = result.get('jobs', [])
        print(f"✅ Internships API Working!")
        print(f"   Found: {len(jobs)} active internships")

        if jobs:
            print("\n   Sample Internships:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"      Location: {job.get('location', 'N/A')}")
                duration = job.get('duration', '')
                if duration:
                    print(f"      Duration: {duration}")

        return True

    except Exception as e:
        print(f"❌ Internships API Error: {str(e)}")
        return False

def test_udemy_free():
    """Test Udemy Free Courses API"""
    print_header("TEST 4: Udemy Free Courses API (Alternative)")
    try:
        udemy_free = UdemyFreeService()
        result = udemy_free.get_free_courses(page=0, limit=5)

        courses = result.get('courses', [])
        print(f"✅ Udemy Free API Working!")
        print(f"   Found: {len(courses)} free courses")

        if courses:
            print("\n   Sample Courses:")
            for i, course in enumerate(courses[:3], 1):
                print(f"   {i}. {course.get('title', 'N/A')}")
                instructor = course.get('instructor', 'N/A')
                print(f"      Instructor: {instructor}")
                discount = course.get('discount', '0')
                print(f"      Discount: {discount}% OFF")

        return True

    except Exception as e:
        print(f"❌ Udemy Free API Error: {str(e)}")
        return False

def test_job_aggregator():
    """Test Job Aggregator (combines all job sources)"""
    print_header("TEST 5: Job Aggregator (All Sources)")
    try:
        aggregator = JobAggregator()
        result = aggregator.search_all_sources(
            query="Python Developer",
            location="London, UK",
            limit_per_source=3
        )

        jobs = result.get('jobs', [])
        source_stats = result.get('source_stats', {})

        print(f"✅ Job Aggregator Working!")
        print(f"   Total Unique Jobs: {len(jobs)}")
        print(f"\n   By Source:")
        for source, count in source_stats.items():
            print(f"      • {source}: {count} jobs")

        if jobs:
            print(f"\n   Sample Aggregated Jobs:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"      Source: {job.get('source', 'N/A')}")
                print(f"      Location: {job.get('location', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ Job Aggregator Error: {str(e)}")
        return False

def test_course_aggregator():
    """Test Course Aggregator with new Udemy Free API"""
    print_header("TEST 6: Course Aggregator (Including New Udemy API)")
    try:
        aggregator = CourseAggregationService()
        result = aggregator.search_courses(
            query="Python",
            sources=['udemy', 'udemy_free'],
            page_size=10
        )

        courses = result.get('courses', [])
        print(f"✅ Course Aggregator Working!")
        print(f"   Total Courses: {len(courses)}")

        # Count by source
        source_count = {}
        for course in courses:
            source = course.get('source', 'unknown')
            source_count[source] = source_count.get(source, 0) + 1

        print(f"\n   By Source:")
        for source, count in source_count.items():
            print(f"      • {source}: {count} courses")

        if courses:
            print(f"\n   Sample Courses:")
            for i, course in enumerate(courses[:3], 1):
                print(f"   {i}. {course.get('title', 'N/A')}")
                print(f"      Source: {course.get('source', 'N/A')}")
                rating = course.get('rating', 0)
                if rating:
                    print(f"      Rating: {rating}/5.0")

        return True

    except Exception as e:
        print(f"❌ Course Aggregator Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" TESTING ALL NEW API INTEGRATIONS")
    print("=" * 70)

    tests = [
        ("LinkedIn Jobs API", test_linkedin),
        ("Glassdoor API", test_glassdoor),
        ("Internships API", test_internships),
        ("Udemy Free API", test_udemy_free),
        ("Job Aggregator", test_job_aggregator),
        ("Course Aggregator", test_course_aggregator)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {str(e)}")
            results[test_name] = False

    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")

    if passed == total:
        print(f"\n🎉 All tests passed! All APIs are working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
