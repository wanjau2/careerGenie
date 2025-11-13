#!/usr/bin/env python3
"""Check database status and source field distribution."""

from config.database import get_database

db = get_database()

print('=' * 60)
print('DATABASE STATUS')
print('=' * 60)
print()
print('Total Statistics:')
print(f'  Total jobs: {db.jobs.count_documents({})}')
print(f'  Active jobs: {db.jobs.count_documents({"is_active": True})}')
print(f'  Inactive jobs: {db.jobs.count_documents({"is_active": False})}')
print()
print('Jobs by Source:')
for source in ['jobs_search', 'linkedin', 'glassdoor', 'internships_api']:
    total = db.jobs.count_documents({'source': source})
    active = db.jobs.count_documents({'source': source, 'is_active': True})
    print(f'  {source}:')
    print(f'    Total: {total}')
    print(f'    Active: {active}')
print()
print('Jobs with Source Field:')
with_source = db.jobs.count_documents({'source': {'$exists': True}})
without_source = db.jobs.count_documents({'source': {'$exists': False}})
print(f'  With source: {with_source}')
print(f'  Without source: {without_source}')
print()

# Sample one job from each source
print('Sample Jobs (one per source):')
for source in ['jobs_search', 'linkedin', 'glassdoor', 'internships_api']:
    sample = db.jobs.find_one({'source': source})
    if sample:
        company = sample.get('company', {})
        if isinstance(company, dict):
            company_name = company.get('name', 'N/A')
        else:
            company_name = company
        print(f'  {source}: {sample.get("title", "N/A")} at {company_name}')
    else:
        print(f'  {source}: No jobs found')

print()
print('=' * 60)
