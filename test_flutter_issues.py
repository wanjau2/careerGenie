#!/usr/bin/env python3
"""
Test script to debug Flutter app issues:
1. Resume upload 404 error
2. No jobs returned for user
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login and get auth token"""
    print("=" * 60)
    print("TEST 1: Login")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "wanjaueugene@gmail.com",
            "password": "yourpassword"  # Replace with actual password
        }
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        token = response.json().get('accessToken')
        print(f"\n✅ Login successful!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"\n❌ Login failed!")
        return None


def test_jobs_endpoint(token):
    """Test jobs endpoint with authentication"""
    print("\n" + "=" * 60)
    print("TEST 2: Get Jobs")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/api/jobs?page=1&pageSize=5",
        headers=headers
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Jobs retrieved successfully!")
        print(f"Total jobs: {data.get('total', 0)}")
        print(f"Jobs returned: {len(data.get('jobs', []))}")
        print(f"\nFirst job:")
        if data.get('jobs'):
            job = data['jobs'][0]
            print(f"  Title: {job.get('title')}")
            print(f"  Company: {job.get('company', {}).get('name')}")
            print(f"  Location: {job.get('location', {}).get('formatted')}")
    else:
        print(f"❌ Jobs request failed!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_resume_endpoints(token):
    """Test resume-related endpoints"""
    print("\n" + "=" * 60)
    print("TEST 3: Resume Endpoints")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Test 1: Check if onboarding/parse-resume exists
    print("\n1. Testing /api/onboarding/parse-resume (correct endpoint)")
    response = requests.options(
        f"{BASE_URL}/api/onboarding/parse-resume",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    print(f"   Allowed methods: {response.headers.get('Allow', 'N/A')}")

    # Test 2: Check if profile/parse-resume exists (might be what Flutter is calling)
    print("\n2. Testing /api/profile/parse-resume (wrong endpoint?)")
    response = requests.options(
        f"{BASE_URL}/api/profile/parse-resume",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print(f"   ❌ This endpoint doesn't exist (404)")
        print(f"   This might be what Flutter is calling!")

    # Test 3: Check if resume/parse exists
    print("\n3. Testing /api/resume/parse")
    response = requests.options(
        f"{BASE_URL}/api/resume/parse",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print(f"   ❌ This endpoint doesn't exist (404)")


def test_available_routes():
    """List all available routes"""
    print("\n" + "=" * 60)
    print("TEST 4: Available Routes")
    print("=" * 60)

    # This won't work directly, but we can test common patterns
    common_endpoints = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/jobs",
        "/api/profile",
        "/api/onboarding/parse-resume",
        "/api/profile/parse-resume",
        "/api/resume/parse",
        "/api/resume/upload",
    ]

    print("\nTesting common endpoints:")
    for endpoint in common_endpoints:
        response = requests.options(f"{BASE_URL}{endpoint}")
        status = "✅" if response.status_code != 404 else "❌"
        print(f"{status} {endpoint} - {response.status_code}")


if __name__ == "__main__":
    print("\n🧪 Flutter App Debug Tests\n")

    # Test 1: Login
    token = test_login()

    if not token:
        print("\n⚠️ Cannot continue without valid token")
        print("Please update the password in this script and try again")
        exit(1)

    # Test 2: Jobs endpoint
    test_jobs_endpoint(token)

    # Test 3: Resume endpoints
    test_resume_endpoints(token)

    # Test 4: Available routes
    test_available_routes()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Likely issues:
1. Resume 404: Flutter app might be calling /api/profile/parse-resume
   Correct endpoint: /api/onboarding/parse-resume

2. No jobs: Check if:
   - User is authenticated (token valid)
   - Jobs endpoint requires pagination params
   - CORS headers are correct

Fix suggestions:
1. Update Flutter app to use /api/onboarding/parse-resume
2. Ensure proper Authorization header format
3. Check Flutter logs for actual URL being called
    """)
