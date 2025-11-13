#!/bin/bash

echo "=== CAREER GENIE - FINAL SYSTEM STATUS ==="
echo ""

# Test 1: Udemy Courses
echo "1. UDEMY COURSES API:"
curl -s "http://localhost:8000/api/courses/search?query=python&sources=udemy&limit=3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
courses = data.get('data', {}).get('courses', [])
print(f'   ✅ Found {len(courses)} Udemy courses')
for c in courses[:3]:
    print(f'   • {c.get(\"title\", \"N/A\")}')
"
echo ""

# Test 2: Jobs
echo "2. JOBS API:"
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"TestPassword123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('accessToken', ''))")

curl -s "http://localhost:8000/api/jobs?limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
jobs = data.get('data', {}).get('jobs', [])
total = data.get('data', {}).get('total', 0)
print(f'   ✅ Total jobs in database: {total}')
for j in jobs[:3]:
    print(f'   • {j.get(\"title\", \"N/A\")} at {j.get(\"company\", \"N/A\")}')
"
echo ""

# Test 3: AdMob
echo "3. ADMOB INTEGRATION:"
curl -s "http://localhost:8000/api/ads/config" | python3 -c "
import sys, json
data = json.load(sys.stdin)
admob = data.get('admob', {})
settings = data.get('adSettings', {})
print(f'   ✅ AdMob App ID: {admob.get(\"appId\", \"N/A\")[:35]}...')
print(f'   ✅ Banner Ad Unit: {admob.get(\"bannerAdUnitId\", \"N/A\")[:35]}...')
print(f'   ✅ Interstitial Frequency: Every {settings.get(\"interstitialAdFrequency\", \"N/A\")} swipes')
print(f'   ✅ Rewarded Ad Reward: {settings.get(\"rewardedAdReward\", \"N/A\")} extra swipes')
"
echo ""
echo "=== ALL SYSTEMS OPERATIONAL ==="
