#!/usr/bin/env python3
"""Comprehensive database check after testing"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('DB_NAME', 'career_genie')]

print('='*80)
print('COMPREHENSIVE DATABASE REPORT')
print('='*80)
print()

# Total statistics
total_jobs = db.jobs.count_documents({})
print(f'📊 Total jobs in database: {total_jobs}')
print()

# Jobs by country
print('🌍 Jobs by Country:')
print('-' * 80)
pipeline = [
    {'$group': {'_id': '$location.country', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 20}
]
results = list(db.jobs.aggregate(pipeline))
for i, r in enumerate(results, 1):
    country = r['_id'] or 'Unknown'
    print(f'{i:2d}. {country:30s} {r["count"]:4d} jobs')
print()

# Jobs by city
print('🏙️  Top 20 Cities:')
print('-' * 80)
pipeline = [
    {'$group': {'_id': '$location.city', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 20}
]
results = list(db.jobs.aggregate(pipeline))
for i, r in enumerate(results, 1):
    city = r['_id'] or 'Unknown'
    print(f'{i:2d}. {city:30s} {r["count"]:4d} jobs')
print()

# Jobs by employment type
print('💼 Jobs by Employment Type:')
print('-' * 80)
pipeline = [
    {'$group': {'_id': '$employment.type', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
results = list(db.jobs.aggregate(pipeline))
for r in results:
    emp_type = r['_id'] or 'Not Specified'
    print(f'   {emp_type:30s} {r["count"]:4d} jobs')
print()

# Top companies hiring globally
print('🏢 Top 30 Companies Hiring Globally:')
print('-' * 80)
pipeline = [
    {'$group': {'_id': '$company.name', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 30}
]
results = list(db.jobs.aggregate(pipeline))
for i, r in enumerate(results, 1):
    company = r['_id'] or 'Unknown'
    print(f'{i:2d}. {company:40s} {r["count"]:3d} positions')
print()

# Job categories breakdown
print('📋 Job Category Analysis:')
print('-' * 80)

categories = {
    'Technology': ['Software', 'Developer', 'Engineer', 'DevOps', 'Cloud', 'Full Stack', 'Backend', 'Frontend'],
    'Data Science': ['Data Scientist', 'Data Analyst', 'Machine Learning', 'Data Engineer', 'Analytics', 'Big Data'],
    'Business': ['Business Analyst', 'Project Manager', 'Product Manager', 'Consultant'],
    'Marketing': ['Marketing', 'Content', 'Social Media', 'SEO', 'Digital Marketing'],
    'Design': ['Designer', 'UI/UX', 'Graphic', 'Creative'],
    'Finance': ['Financial', 'Accountant', 'Finance', 'Investment'],
    'Healthcare': ['Nurse', 'Doctor', 'Medical', 'Healthcare', 'Clinical'],
    'Sales': ['Sales', 'Account Manager', 'Business Development'],
    'HR': ['HR', 'Human Resources', 'Recruiter', 'Talent'],
    'Engineering': ['Mechanical', 'Civil', 'Electrical', 'Manufacturing']
}

for category, keywords in categories.items():
    regex_pattern = '|'.join(keywords)
    count = db.jobs.count_documents({
        'title': {'$regex': regex_pattern, '$options': 'i'}
    })
    if count > 0:
        print(f'   {category:30s} {count:4d} jobs')
print()

# Remote vs On-site
print('🏠 Remote vs On-site:')
print('-' * 80)
remote_count = db.jobs.count_documents({'location.remote': True})
onsite_count = db.jobs.count_documents({'location.remote': False})
print(f'   Remote jobs:                  {remote_count:4d}')
print(f'   On-site jobs:                 {onsite_count:4d}')
print()

# Jobs with salary information
print('💰 Salary Information:')
print('-' * 80)
with_salary = db.jobs.count_documents({
    '$or': [
        {'salary.min': {'$ne': None, '$gt': 0}},
        {'salary.max': {'$ne': None, '$gt': 0}}
    ]
})
without_salary = total_jobs - with_salary
print(f'   Jobs with salary info:        {with_salary:4d} ({with_salary*100//total_jobs if total_jobs > 0 else 0}%)')
print(f'   Jobs without salary info:     {without_salary:4d} ({without_salary*100//total_jobs if total_jobs > 0 else 0}%)')
print()

# Jobs by source
print('🔍 Jobs by Source:')
print('-' * 80)
pipeline = [
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
results = list(db.jobs.aggregate(pipeline))
for r in results:
    source = r['_id'] or 'Unknown'
    print(f'   {source:30s} {r["count"]:4d} jobs')
print()

print('='*80)
print('END OF REPORT')
print('='*80)
