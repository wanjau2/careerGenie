#!/usr/bin/env python
"""Test course aggregation service."""
import sys
sys.path.insert(0, '/home/Root/Desktop/projects/CareerGenie/backend')

from services.course_aggregation import CourseAggregationService
import json

print("Testing Course Aggregation Service...")
print("=" * 60)

service = CourseAggregationService()

# Test 1: Search with query
print("\n1. Testing search with query 'python':")
result = service.search_courses(query='python', page=1, page_size=10)
print(f"Total courses: {result.get('total', 0)}")
print(f"Sources: {result.get('sources', [])}")
print(f"Errors: {result.get('errors', 'None')}")

udemy_courses = [c for c in result.get('courses', []) if 'udemy' in c.get('source', '')]
coursera_courses = [c for c in result.get('courses', []) if 'coursera' in c.get('source', '')]

print(f"\nUdemy courses: {len(udemy_courses)}")
print(f"Coursera courses: {len(coursera_courses)}")

if udemy_courses:
    print(f"\nFirst Udemy course: {udemy_courses[0].get('title', 'N/A')}")
else:
    print("\nNo Udemy courses found in aggregation")

# Test 2: Search with sources filter
print("\n\n2. Testing search with only 'udemy' source:")
result = service.search_courses(query='machine learning', sources=['udemy'], page_size=5)
print(f"Total courses: {result.get('total', 0)}")
print(f"Courses returned: {len(result.get('courses', []))}")
print(f"Errors: {result.get('errors', 'None')}")

if result.get('courses'):
    print("\nCourse titles:")
    for i, course in enumerate(result['courses'][:3], 1):
        print(f"  {i}. {course.get('title', 'N/A')} (source: {course.get('source', 'N/A')})")

print("\n\nTest complete!")
