#!/usr/bin/env python3
"""Check jobs in database"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('DB_NAME')]

# Count total jobs
total = db.jobs.count_documents({'isActive': True})
print(f'📊 Total active jobs in database: {total}')

# Count by category
print(f'\n📋 Jobs by category:')
pipeline = [
    {'$match': {'isActive': True}},
    {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
for doc in db.jobs.aggregate(pipeline):
    print(f'   {doc["_id"]}: {doc["count"]} jobs')

# Count by source
print(f'\n🔍 Jobs by source:')
pipeline = [
    {'$match': {'isActive': True}},
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
for doc in db.jobs.aggregate(pipeline):
    print(f'   {doc["_id"]}: {doc["count"]} jobs')

# Show sample jobs
print(f'\n✅ Sample jobs (first 5):')
for i, job in enumerate(db.jobs.find({'isActive': True}).limit(5), 1):
    print(f'\n   {i}. {job.get("title", "N/A")}')
    print(f'      Company: {job.get("company", "N/A")}')
    print(f'      Location: {job.get("location", "N/A")}')
    print(f'      Category: {job.get("category", "N/A")}')
    print(f'      Source: {job.get("source", "N/A")}')
