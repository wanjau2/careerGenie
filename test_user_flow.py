#!/usr/bin/env python3
"""Test script to verify user registration, login, and profile flow."""

import requests
import json

BASE_URL = "http://192.168.8.101:8000"

# Test user credentials
TEST_USER = {
    "email": "test@careergenie.com",
    "password": "TestPassword123!",
    "firstName": "Test",
    "lastName": "User"
}

def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_health():
    """Test backend health."""
    print_section("1. Testing Backend Health")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Backend Status: {response.json()['status']}")
        print(f"   Database: {response.json()['database']}")
        return True
    except Exception as e:
        print(f"❌ Backend Error: {e}")
        return False

def test_register():
    """Test user registration."""
    print_section("2. Testing User Registration")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Registration Successful!")
            print(f"   User ID: {data.get('user', {}).get('id', 'N/A')}")
            print(f"   Email: {data.get('user', {}).get('email', 'N/A')}")
            print(f"   Token: {data.get('accessToken', 'N/A')[:30]}...")
            return data.get('accessToken')
        elif response.status_code == 409:
            print(f"⚠️  User already exists, will try login...")
            return None
        else:
            print(f"❌ Registration Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return None

def test_login():
    """Test user login."""
    print_section("3. Testing User Login")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login Successful!")
            print(f"   Email: {data.get('user', {}).get('email', 'N/A')}")
            print(f"   Token: {data.get('accessToken', 'N/A')[:30]}...")
            return data.get('accessToken')
        else:
            print(f"❌ Login Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return None

def test_get_profile(token):
    """Test getting user profile."""
    print_section("4. Testing Get Profile")
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/profile",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            print(f"✅ Profile Retrieved!")
            print(f"   First Name: {user.get('firstName', 'N/A')}")
            print(f"   Last Name: {user.get('lastName', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Job Title: {user.get('jobTitle', 'Not set')}")
            print(f"   Skills: {user.get('skills', [])}")
            print(f"   Profile Complete: {user.get('isProfileComplete', False)}")
            return user
        else:
            print(f"❌ Get Profile Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Get Profile Error: {e}")
        return None

def test_update_profile(token):
    """Test updating user profile."""
    print_section("5. Testing Update Profile")
    try:
        profile_data = {
            "jobTitle": "Software Engineer",
            "skills": ["Python", "Flutter", "React"],
            "experience": "2-5 years",
            "bio": "Passionate developer building amazing apps"
        }

        response = requests.put(
            f"{BASE_URL}/api/user/profile",
            json=profile_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            print(f"✅ Profile Updated!")
            print(f"   Job Title: {user.get('jobTitle', 'N/A')}")
            print(f"   Skills: {user.get('skills', [])}")
            print(f"   Experience: {user.get('experience', 'N/A')}")
            print(f"   Bio: {user.get('bio', 'N/A')}")
            return user
        else:
            print(f"❌ Update Profile Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Update Profile Error: {e}")
        return None

def main():
    """Run all tests."""
    print("\n" + "🚀 Career Genie Backend Test Suite".center(60))
    print("Testing user registration, login, and profile flow\n")

    # Test 1: Health check
    if not test_health():
        print("\n❌ Backend is not healthy. Please start the backend first.")
        return

    # Test 2: Register or Login
    token = test_register()
    if not token:
        token = test_login()

    if not token:
        print("\n❌ Could not get access token. Tests aborted.")
        return

    # Test 3: Get Profile
    profile = test_get_profile(token)

    # Test 4: Update Profile
    if profile:
        test_update_profile(token)
        # Get profile again to see updates
        test_get_profile(token)

    print_section("✅ All Tests Completed!")
    print(f"\n💡 Use these credentials in Flutter app:")
    print(f"   Email: {TEST_USER['email']}")
    print(f"   Password: {TEST_USER['password']}")
    print(f"\n   Access Token (for manual testing):")
    print(f"   {token[:50]}...\n")

if __name__ == "__main__":
    main()
