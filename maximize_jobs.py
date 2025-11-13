#!/usr/bin/env python3
"""
Script to maximize job results by using multiple query variations
"""
import requests
import time
import json
from datetime import datetime

# Configuration
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MjQ1NjE5NywianRpIjoiYWU5NDE1MzEtMDNhZC00NzE4LWEzMTQtMzQ1MWZiNjczMTFlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY5MGNmMjg1OGM2MzVlOTU4Y2Q3M2VjZSIsIm5iZiI6MTc2MjQ1NjE5NywiY3NyZiI6IjE0OWRmMjU1LWMwY2UtNGY3ZS1hOWY3LTc5Nzk1N2JmOGVkMCIsImV4cCI6MTc2MjQ1OTc5N30.F-nf2M3P9oBmzui55k-oed_3IrPaJ09tP82mpRhxVCM"
BASE_URL = "http://localhost:8000"

# Define comprehensive job queries with variations
JOB_QUERIES = {
    'Data Engineering': [
        'Data Engineer',
        'Senior Data Engineer',
        'Junior Data Engineer',
        'Lead Data Engineer',
        'Data Engineering Manager',
        'ETL Developer',
        'ETL Engineer',
        'Data Pipeline Engineer',
        'Big Data Engineer',
        'Data Architect',
        'Data Warehouse Engineer',
        'Analytics Engineer'
    ],
    'Software Engineering': [
        'Software Engineer',
        'Senior Software Engineer',
        'Software Developer',
        'Backend Developer',
        'Backend Engineer',
        'Frontend Developer',
        'Frontend Engineer',
        'Full Stack Developer',
        'Full Stack Engineer',
        'Web Developer'
    ],
    'DevOps & Cloud': [
        'DevOps Engineer',
        'Cloud Engineer',
        'Site Reliability Engineer',
        'SRE',
        'Platform Engineer',
        'Infrastructure Engineer',
        'AWS Engineer',
        'Azure Engineer',
        'Kubernetes Engineer'
    ],
    'Data Science & AI': [
        'Data Scientist',
        'Senior Data Scientist',
        'Machine Learning Engineer',
        'ML Engineer',
        'AI Engineer',
        'Deep Learning Engineer',
        'Computer Vision Engineer',
        'NLP Engineer',
        'MLOps Engineer'
    ],
    'Business & Analytics': [
        'Data Analyst',
        'Business Analyst',
        'Business Intelligence Analyst',
        'BI Developer',
        'Analytics Manager',
        'Product Analyst',
        'Operations Analyst'
    ]
}

# Locations - focus on major tech hubs
LOCATIONS = [
    'Nairobi, Kenya',
    'New York, USA',
    'San Francisco, USA',
    'London, UK',
    'Berlin, Germany',
    'Singapore',
    'Dubai, UAE'
]

def fetch_jobs(query, location, limit=50):
    """Fetch jobs for a specific query and location"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/fetch",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "location": location,
                "limit": limit,
                "saveToDb": True
            },
            timeout=30
        )

        if response.ok:
            data = response.json()
            return {
                'success': True,
                'fetched': data['meta']['count'],
                'saved': data['meta']['savedCount']
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}"
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("MAXIMIZING JOB RESULTS - BATCH FETCH")
    print("=" * 80)
    print(f"Start time: {datetime.now()}")
    print()

    total_fetched = 0
    total_saved = 0
    total_requests = 0
    failed_requests = 0

    # Strategy: Fetch jobs for each category, query, and location combination
    for category, queries in JOB_QUERIES.items():
        print(f"\n{'='*80}")
        print(f"CATEGORY: {category}")
        print(f"{'='*80}")

        # For efficiency, test first 3 queries per category in multiple locations
        for query in queries[:3]:  # Limit to 3 queries per category
            print(f"\n  Query: {query}")

            # Test 2 locations per query
            for location in LOCATIONS[:2]:
                total_requests += 1
                print(f"    → {location}...", end=" ")

                result = fetch_jobs(query, location)

                if result['success']:
                    fetched = result['fetched']
                    saved = result['saved']
                    total_fetched += fetched
                    total_saved += saved

                    if saved > 0:
                        print(f"✓ {fetched} fetched, {saved} new")
                    else:
                        print(f"○ {fetched} fetched, 0 new (all duplicates)")
                else:
                    failed_requests += 1
                    print(f"✗ Failed: {result.get('error', 'Unknown error')}")

                # Rate limiting - be nice to the API
                time.sleep(1.5)

    # Summary
    print("\n" + "=" * 80)
    print("BATCH FETCH SUMMARY")
    print("=" * 80)
    print(f"Total requests:        {total_requests}")
    print(f"Successful:            {total_requests - failed_requests}")
    print(f"Failed:                {failed_requests}")
    print(f"Jobs fetched:          {total_fetched}")
    print(f"New jobs saved:        {total_saved}")
    print(f"Duplicates filtered:   {total_fetched - total_saved}")
    print(f"Success rate:          {((total_requests - failed_requests) / total_requests * 100):.1f}%")
    print(f"\nEnd time: {datetime.now()}")
    print("=" * 80)

if __name__ == '__main__':
    main()
