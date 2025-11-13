#!/usr/bin/env python
"""Direct test of Udemy service."""
import sys
sys.path.insert(0, '/home/Root/Desktop/projects/CareerGenie/backend')

from services.udemy_service import UdemyService
import json

print("Testing Udemy Service Directly...")
print("=" * 50)

udemy = UdemyService()

# Test search
print("\n1. Testing search for 'python' courses:")
result = udemy.search_courses(query='python', page=1, page_size=5)
print(f"Total courses: {result.get('total', 0)}")
print(f"Error: {result.get('error', 'None')}")
if result.get('courses'):
    print(f"First course: {result['courses'][0].get('title', 'N/A')}")
    print(f"Source: {result['courses'][0].get('source', 'N/A')}")
else:
    print("No courses returned")

print("\n2. Testing search for 'web development' courses:")
result = udemy.search_courses(query='web development', page=1, page_size=3)
print(f"Total courses: {result.get('total', 0)}")
print(f"Error: {result.get('error', 'None')}")

print("\n3. Testing get_featured_courses:")
result = udemy.get_featured_courses(limit=3)
print(f"Total courses: {result.get('total', 0)}")
print(f"Error: {result.get('error', 'None')}")

print("\nTest complete!")
