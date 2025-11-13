#!/usr/bin/env python3
"""Check jobs in database"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('DB_NAME', 'career_genie')]

# Count total jobs
total_jobs = db.jobs.count_documents({})
print(f'Total jobs in database: {total_jobs}')

# Count jobs in Nairobi
nairobi_jobs = db.jobs.count_documents({'location.city': 'Nairobi'})
print(f'Jobs in Nairobi: {nairobi_jobs}')

# Get breakdown by job title
print(f'\nTop 20 job titles in Nairobi:')
pipeline = [
    {'$match': {'location.city': 'Nairobi'}},
    {'$group': {'_id': '$title', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 20}
]
results = list(db.jobs.aggregate(pipeline))
for i, r in enumerate(results, 1):
    print(f'{i:2d}. {r["_id"]}: {r["count"]}')

# Get companies hiring
print(f'\nTop companies hiring in Nairobi:')
pipeline = [
    {'$match': {'location.city': 'Nairobi'}},
    {'$group': {'_id': '$company.name', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 15}
]
results = list(db.jobs.aggregate(pipeline))
for i, r in enumerate(results, 1):
    print(f'{i:2d}. {r["_id"]}: {r["count"]} positions')

# Check data engineering related jobs
print(f'\nData Engineering related jobs breakdown:')
de_keywords = ['Data Engineer', 'Data Analyst', 'Machine Learning', 'Big Data', 'Business Intelligence', 'Data Scientist', 'ETL']
for keyword in de_keywords:
    count = db.jobs.count_documents({
        'location.city': 'Nairobi',
        'title': {'$regex': keyword, '$options': 'i'}
    })
    if count > 0:
        print(f'  {keyword}: {count} jobs')
