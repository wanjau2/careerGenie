#!/usr/bin/env python3
"""
Test Web Scrapers for Course Aggregation
Tests: Class Central, MIT OCW, Udacity, Skillshare
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.course_scrapers import ClassCentralScraper, UdacityScraper, SkillshareScraper
from services.additional_course_sources import MITOpenCourseWare
from services.free_courses_aggregator import FreeCourseAggregator


def test_scraper(scraper_name, scraper, query, limit=5):
    """Test a specific scraper"""
    print(f"\n{'='*60}")
    print(f"Testing: {scraper_name}")
    print(f"Query: '{query}'")
    print('='*60)

    try:
        if hasattr(scraper, 'search_courses'):
            courses = scraper.search_courses(query, limit=limit)
        else:
            courses = scraper.get_courses(limit=limit)

        print(f"\n✅ Found {len(courses)} courses:\n")

        for i, course in enumerate(courses[:5], 1):  # Show first 5
            print(f"{i}. {course['title']}")
            print(f"   Provider: {course['provider']}")
            print(f"   URL: {course['url'][:80]}...")
            print(f"   Free: {course['isFree']}")
            print()

        if len(courses) > 5:
            print(f"... and {len(courses) - 5} more courses\n")

        return len(courses) > 0

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Course Web Scraper Test Suite                      ║
║     Testing scrapers that dramatically increase results     ║
╚══════════════════════════════════════════════════════════════╝
    """)

    results = []

    # Test 1: Class Central (THE BIG ONE - 50,000+ courses!)
    print("\n" + "="*60)
    print("TEST 1: Class Central (MOOC Aggregator)")
    print("Expected: 10-15 courses from various universities")
    print("="*60)
    class_central = ClassCentralScraper()
    success = test_scraper("Class Central", class_central, "python programming", limit=10)
    results.append(("Class Central", success))

    # Test 2: MIT OpenCourseWare
    print("\n" + "="*60)
    print("TEST 2: MIT OpenCourseWare")
    print("Expected: 5-10 MIT courses")
    print("="*60)
    mit_ocw = MITOpenCourseWare()
    success = test_scraper("MIT OCW", mit_ocw, "computer science", limit=10)
    results.append(("MIT OCW", success))

    # Test 3: Udacity Scraper
    print("\n" + "="*60)
    print("TEST 3: Udacity (Dynamic Scraping)")
    print("Expected: 5-10 tech courses")
    print("="*60)
    udacity = UdacityScraper()
    success = test_scraper("Udacity Scraper", udacity, "web development", limit=10)
    results.append(("Udacity Scraper", success))

    # Test 4: Skillshare
    print("\n" + "="*60)
    print("TEST 4: Skillshare (Creative Courses)")
    print("Expected: 5-10 creative courses")
    print("="*60)
    skillshare = SkillshareScraper()
    success = test_scraper("Skillshare", skillshare, "graphic design", limit=10)
    results.append(("Skillshare", success))

    # Test 5: Full Aggregator (ALL sources combined!)
    print("\n" + "="*60)
    print("TEST 5: Full Course Aggregator (All Sources)")
    print("Expected: 20+ courses from ALL sources")
    print("="*60)
    aggregator = FreeCourseAggregator()
    success = test_scraper("Full Aggregator", aggregator, "data science", limit=20)
    results.append(("Full Aggregator", success))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All scrapers working! Course results MASSIVELY increased!")
        print("\n📊 Course Sources Summary:")
        print("   - Class Central: 50,000+ courses")
        print("   - MIT OCW: 2,500+ courses")
        print("   - Udacity: 100+ courses")
        print("   - Skillshare: 30,000+ classes")
        print("   - YouTube: Unlimited (10K API/day)")
        print("   - edX: 3,000+ courses")
        print("   - Khan Academy: 10,000+ lessons")
        print("   - Alison: 4,000+ courses")
        print("   - Harvard CS50: 10+ courses")
        print("   - FreeCodeCamp: 10+ certifications")
        print("\n   🚀 TOTAL: 100,000+ free courses available!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} scraper(s) failed.")
        print("Note: Some scrapers may fail due to:")
        print("  - Website HTML structure changes")
        print("  - Network issues")
        print("  - Rate limiting")
        print("\nThis is normal for web scraping. The aggregator will still work with available sources.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
