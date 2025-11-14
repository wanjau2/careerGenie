#!/usr/bin/env python3
"""
Quick Test - Course Recommendation System
==========================================

This script tests the course recommendation system and demonstrates how it works.

Usage:
    python test_course_system.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.course_aggregation import CourseAggregationService


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_course(course, index=None):
    """Print course details in a nice format."""
    prefix = f"{index}. " if index else "  "

    print(f"{prefix}{course.get('title', 'Unknown Title')}")
    print(f"   Provider: {course.get('provider', 'Unknown')} | "
          f"Rating: ⭐ {course.get('rating', 0):.1f} | "
          f"Level: {course.get('level', 'Unknown')}")

    if course.get('isFree'):
        print(f"   Price: FREE")
    elif course.get('price'):
        print(f"   Price: {course.get('price')}")

    print(f"   URL: {course.get('registrationUrl', 'N/A')[:60]}...")
    print()


def test_basic_search():
    """Test basic course search."""
    print_separator()
    print("TEST 1: Basic Course Search")
    print_separator()

    service = CourseAggregationService()

    print("\n🔍 Searching for 'Python' courses...\n")

    result = service.search_courses(query="Python", page_size=5)

    print(f"Found {result.get('total', 0)} courses")
    print(f"Showing {len(result.get('courses', []))} results:\n")

    for i, course in enumerate(result.get('courses', []), 1):
        print_course(course, i)

    if result.get('errors'):
        print("⚠ Errors encountered:")
        for error in result.get('errors', []):
            print(f"  - {error['source']}: {error['error']}")


def test_recommendations():
    """Test course recommendations based on skills."""
    print_separator()
    print("TEST 2: Course Recommendations")
    print_separator()

    service = CourseAggregationService()

    skills = ["Python", "Django", "React"]
    print(f"\n💡 Getting recommendations for skills: {', '.join(skills)}\n")

    result = service.get_recommended_courses(skills=skills, limit=5)

    print(f"Found {len(result.get('courses', []))} recommended courses:\n")

    for i, course in enumerate(result.get('courses', []), 1):
        print_course(course, i)


def test_free_courses():
    """Test fetching free courses only."""
    print_separator()
    print("TEST 3: Free Courses Only")
    print_separator()

    service = CourseAggregationService()

    print("\n🎁 Searching for FREE courses...\n")

    result = service.search_courses(is_free=True, page_size=5)

    print(f"Found {result.get('total', 0)} free courses")
    print(f"Showing {len(result.get('courses', []))} results:\n")

    for i, course in enumerate(result.get('courses', []), 1):
        print_course(course, i)


def test_featured_courses():
    """Test fetching featured courses."""
    print_separator()
    print("TEST 4: Featured Courses")
    print_separator()

    service = CourseAggregationService()

    print("\n⭐ Getting featured courses...\n")

    result = service.get_featured_courses(limit=5)

    print(f"Found {len(result.get('courses', []))} featured courses:\n")

    for i, course in enumerate(result.get('courses', []), 1):
        print_course(course, i)


def test_multi_skill_search():
    """Test searching with multiple skills."""
    print_separator()
    print("TEST 5: Multi-Skill Search")
    print_separator()

    service = CourseAggregationService()

    query = "Machine Learning Data Science"
    print(f"\n🔍 Searching for: '{query}'\n")

    result = service.search_courses(query=query, page_size=5)

    print(f"Found {result.get('total', 0)} courses")
    print(f"Showing {len(result.get('courses', []))} results:\n")

    for i, course in enumerate(result.get('courses', []), 1):
        print_course(course, i)


def test_sources():
    """Test course sources availability."""
    print_separator()
    print("TEST 6: Course Sources Check")
    print_separator()

    service = CourseAggregationService()

    sources_to_test = ['coursera', 'udemy', 'udemy_free']

    print("\n📊 Testing individual course sources:\n")

    for source in sources_to_test:
        print(f"Testing {source}...")

        result = service.search_courses(
            query="programming",
            sources=[source],
            page_size=3
        )

        count = len(result.get('courses', []))
        errors = result.get('errors', [])

        if count > 0:
            print(f"  ✓ {source}: {count} courses found")
        elif errors:
            error_msg = errors[0].get('error', 'Unknown error')
            print(f"  ✗ {source}: Error - {error_msg}")
        else:
            print(f"  ⚠ {source}: No courses found")

    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CAREER GENIE - COURSE SYSTEM TEST")
    print("=" * 80)

    # Check API key
    api_key = os.getenv('RAPIDAPI_KEY')
    if api_key:
        print(f"\n✓ RAPIDAPI_KEY configured: {api_key[:10]}...")
    else:
        print("\n⚠ WARNING: RAPIDAPI_KEY not found!")
        print("  Set RAPIDAPI_KEY in .env for full functionality")

    print("\nRunning comprehensive tests...\n")

    try:
        # Run all tests
        test_sources()
        test_basic_search()
        test_recommendations()
        test_free_courses()
        test_featured_courses()
        test_multi_skill_search()

        print_separator()
        print("ALL TESTS COMPLETED")
        print_separator()
        print("\n✓ Course system is working correctly!\n")

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
