#!/usr/bin/env python3
"""
Test script for multi-field course recommendations
Tests: Healthcare, Business, Education, Trades, Creative, Tech
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.free_courses_aggregator import FreeCourseAggregator


def test_field(aggregator, field_name, query, category=None):
    """Test course search for a specific field"""
    print(f"\n{'='*60}")
    print(f"Testing: {field_name}")
    print(f"Query: '{query}' | Category: {category or 'None'}")
    print('='*60)

    try:
        courses = aggregator.search_courses(
            query=query,
            category=category,
            limit=5
        )

        print(f"\n✅ Found {len(courses)} courses:\n")

        for i, course in enumerate(courses, 1):
            print(f"{i}. {course['title']}")
            print(f"   Provider: {course['provider']}")
            print(f"   URL: {course['url']}")
            print(f"   Free: {course['isFree']}")
            if course.get('instructor'):
                print(f"   Instructor: {course['instructor']}")
            print()

        if not courses:
            print("⚠️  No courses found")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     Multi-Field Course Recommendation Test                  ║
║     Testing ALL fields: Healthcare, Business, Education,     ║
║     Trades, Creative, Tech                                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Initialize aggregator
    print("Initializing Free Course Aggregator...")
    aggregator = FreeCourseAggregator()
    print("✅ Aggregator initialized\n")

    # Test cases for different fields
    test_cases = [
        # Healthcare
        ("Healthcare - Nursing", "nursing", "healthcare"),
        ("Healthcare - First Aid", "first aid", "healthcare"),

        # Business
        ("Business - Accounting", "accounting", "business"),
        ("Business - Marketing", "marketing", "business"),

        # Education
        ("Education - Teaching", "teaching", "education"),
        ("Education - Classroom Management", "classroom management", "education"),

        # Trades
        ("Trades - Plumbing", "plumbing", "trades"),
        ("Trades - Electrical", "electrical wiring", "trades"),

        # Creative
        ("Creative - Photography", "photography", "design"),
        ("Creative - Graphic Design", "graphic design", "design"),

        # Tech (still supported)
        ("Tech - Python", "python programming", "tech"),
        ("Tech - Data Science", "data science", "tech"),
    ]

    results = []

    for field_name, query, category in test_cases:
        success = test_field(aggregator, field_name, query, category)
        results.append((field_name, success))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for field_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {field_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Multi-field course support is working.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
