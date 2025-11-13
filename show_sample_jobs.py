#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('DB_NAME', 'career_genie')]

# Get sample data engineering jobs
print('='*80)
print('SAMPLE DATA ENGINEERING JOBS IN NAIROBI')
print('='*80)

jobs = list(db.jobs.find(
    {'location.city': 'Nairobi', 'title': {'$regex': 'Data Engineer', '$options': 'i'}},
    {'title': 1, 'company.name': 1, 'location': 1, 'employment.type': 1, 'applyLink': 1, '_id': 0}
).limit(15))

for i, job in enumerate(jobs, 1):
    print(f'\n{i}. {job.get("title")}')
    print(f'   Company: {job.get("company", {}).get("name")}')
    print(f'   Location: {job.get("location", {}).get("city")}, {job.get("location", {}).get("country")}')
    print(f'   Type: {job.get("employment", {}).get("type")}')
    link = job.get('applyLink', '')
    print(f'   Apply: {link[:70]}...' if len(link) > 70 else f'   Apply: {link}')

print(f'\n' + '='*80)
print(f'Total Data Engineering jobs stored: {len(jobs)}')
print('='*80)
