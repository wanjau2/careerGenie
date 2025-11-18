# Job Fetching System

## Overview

Career Genie uses a **two-tier job fetching system**:

1. **Automated (Celery)**: Background tasks that run on schedule
2. **Manual (Fallback Script)**: On-demand script when Celery isn't available

## How It Works

### Database-First Approach ✅

**Jobs are fetched and stored in MongoDB ONCE, then served from the database.**

```
External APIs → Celery/Script → MongoDB → Users
     ↓              ↓              ↑
  (Daily)      (Stores jobs)   (Fast reads)
```

When users login and browse jobs:
- ❌ NOT calling external APIs every time
- ✅ Reading from pre-fetched MongoDB data
- ✅ Fast response times
- ✅ No rate limiting issues

---

## 1. Automated System (Celery)

### Celery Tasks

Located in: `tasks/job_fetching_tasks.py`

**Three main tasks:**

1. **`fetch_global_jobs`** - Daily at 2 AM
   - Fetches jobs for ALL regions (Kenya, USA, Europe, Asia)
   - 260+ job categories per location
   - Takes 6-8 hours with rate limiting
   - Rate limited: 15-25s delays between requests

2. **`fetch_kenya_jobs`** - Twice daily (2 AM, 2 PM)
   - Priority region for frequent updates
   - Faster updates for Kenyan jobs

3. **`cleanup_old_jobs`** - Weekly on Sundays at 3 AM
   - Marks jobs older than 30 days as inactive
   - Keeps database clean

### Running Celery

**Prerequisites:**
- Redis server running

**Start Celery worker:**
```bash
cd backend
source venv/bin/activate

# Start worker
celery -A tasks.job_fetching_tasks worker --loglevel=info

# Start beat scheduler (for periodic tasks)
celery -A tasks.job_fetching_tasks beat --loglevel=info
```

**Or run both together:**
```bash
celery -A tasks.job_fetching_tasks worker --beat --loglevel=info
```

---

## 2. Manual Fallback Script

Located in: `scripts/fetch_jobs_manual.py`

### Quick Start

**Show database stats:**
```bash
python scripts/fetch_jobs_manual.py --stats
```

**Fetch jobs for Kenya:**
```bash
python scripts/fetch_jobs_manual.py --region kenya
```

**Fetch jobs for USA:**
```bash
python scripts/fetch_jobs_manual.py --region usa
```

**Fetch jobs for ALL regions (WARNING: Takes 6-8 hours!):**
```bash
python scripts/fetch_jobs_manual.py --region all
```

### Advanced Usage

**Fetch specific job categories:**
```bash
python scripts/fetch_jobs_manual.py --region kenya \
  --categories "Data Engineer,Software Engineer,Data Scientist"
```

**Quick fetch with shorter delays (use carefully!):**
```bash
python scripts/fetch_jobs_manual.py --region kenya --quick
```
*Note: `--quick` uses 5-10s delays instead of 15-25s. May hit rate limits.*

**Cleanup old jobs:**
```bash
# Mark jobs older than 30 days as inactive
python scripts/fetch_jobs_manual.py --cleanup

# Custom days
python scripts/fetch_jobs_manual.py --cleanup --cleanup-days 60
```

**Custom limit per source:**
```bash
python scripts/fetch_jobs_manual.py --region kenya --limit 50
```

### Script Options

```
--region {kenya,usa,europe,asia,all}
    Region to fetch jobs for

--categories "Cat1,Cat2,Cat3"
    Comma-separated job categories (default: 40 popular categories)

--quick
    Use shorter delays (5-10s). Use carefully to avoid rate limits!

--cleanup
    Mark old jobs as inactive

--cleanup-days N
    Days threshold for cleanup (default: 30)

--stats
    Show database statistics

--limit N
    Max jobs per source API (default: 100)
```

---

## Job Sources

Jobs are fetched from 4 sources in parallel:

1. **JSearch API** (RapidAPI)
2. **LinkedIn Jobs API** (RapidAPI)
3. **Glassdoor API** (RapidAPI)
4. **Internships API** (RapidAPI)

Each source can return up to 100 jobs per request (configurable).

## Job Categories - Global Coverage

The system fetches jobs across **ALL industries** (180+ job titles):

### Industries Covered:
- **Tech & IT** (35 roles): Software Engineer, Data Scientist, DevOps, AI Engineer, etc.
- **Business & Finance** (28 roles): Accountant, Financial Analyst, CEO, HR Manager, etc.
- **Sales & Marketing** (18 roles): Sales Executive, Digital Marketer, SEO Specialist, etc.
- **Creative & Media** (17 roles): Graphic Designer, Video Editor, Content Creator, etc.
- **Engineering** (16 roles): Mechanical, Electrical, Civil, Petroleum Engineer, etc.
- **Healthcare** (15 roles): Doctor, Nurse, Pharmacist, Therapist, etc.
- **Education** (9 roles): Teacher, Professor, Tutor, Librarian, etc.
- **Law & Government** (13 roles): Lawyer, Paralegal, Policy Analyst, etc.
- **Hospitality & Travel** (11 roles): Chef, Hotel Manager, Tour Guide, etc.
- **Labour & Skilled Trades** (13 roles): Driver, Mechanic, Electrician, Plumber, etc.
- **Modern Gig Economy** (10 roles): Virtual Assistant, Freelancer, Online Tutor, etc.

This ensures Career Genie serves **everyone**, not just tech professionals!

---

## Rate Limiting

### Why Delays?

External APIs have rate limits (typically 100-500 requests/hour). To avoid `429 Too Many Requests` errors:

- **Default delays**: 15-25 seconds between requests
- **Quick mode**: 5-10 seconds (use sparingly)
- **On 429 error**: Automatic 60-second backoff

### Estimated Times

**Kenya only** (6 locations × 40 categories):
- 240 requests × 20s average = ~1.3 hours

**All regions** (38 locations × 260 categories):
- 9,880 requests × 20s average = ~55 hours
- Actual: 6-8 hours (due to parallelization and failures)

---

## Database Schema

**Jobs Collection:**
```javascript
{
  _id: ObjectId,
  title: String,
  company: {
    name: String,
    logo: String
  },
  location: {
    city: String,
    state: String,
    country: String,
    formatted: String
  },
  type: String,  // Full-time, Part-time, etc.
  salary: {
    min: Number,
    max: Number,
    currency: String
  },
  description: String,
  requirements: {
    skills: [String],
    experience: String,
    education: String
  },
  isActive: Boolean,
  scrapedAt: Date,
  deactivatedAt: Date,
  job_hash: String,  // Unique identifier to prevent duplicates
  source: Object     // Source statistics
}
```

**Duplicate Prevention:**
```javascript
job_hash = "title::company::location"
// Example: "data engineer::google::nairobi"
```

---

## Monitoring

### Check Job Count

```bash
python scripts/fetch_jobs_manual.py --stats
```

Output example:
```
======================================================================
📊 DATABASE STATISTICS
======================================================================
Total jobs: 399
Active jobs: 385
Inactive jobs: 14

Active jobs by region:
  • Kenya: 213
  • USA: 98
  • India: 45
  • UK: 29
======================================================================
```

### Via MongoDB

```bash
mongo
use CareerGenie

# Total jobs
db.jobs.count()

# Active jobs
db.jobs.count({isActive: true})

# Jobs by location
db.jobs.aggregate([
  {$match: {isActive: true}},
  {$group: {_id: "$location.country", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

---

## Troubleshooting

### No jobs being fetched

**Check RapidAPI key:**
```bash
echo $RAPIDAPI_KEY
```

**Check Redis connection (for Celery):**
```bash
redis-cli ping
# Should return: PONG
```

### Rate limit errors (429)

**Solution 1:** Increase delays
```bash
# Default is 15-25s, script will auto-backoff on 429
```

**Solution 2:** Reduce jobs per source
```bash
python scripts/fetch_jobs_manual.py --region kenya --limit 20
```

### Duplicate jobs

The system prevents duplicates using `job_hash`. If you see duplicates:

```bash
# Rebuild job hashes
mongo CareerGenie --eval '
  db.jobs.find({}).forEach(function(job) {
    var hash = (job.title + "::" + job.company.name + "::" + job.location.formatted).toLowerCase();
    db.jobs.updateOne({_id: job._id}, {$set: {job_hash: hash}});
  });
'
```

---

## Production Recommendations

1. **Use Celery for automation** - Set it and forget it
2. **Run manual script for immediate needs** - Quick top-ups
3. **Monitor job count weekly** - Ensure Celery is working
4. **Cleanup monthly** - Keep database fresh

### Ideal Setup

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Flask API
python app.py

# Terminal 3: Celery
celery -A tasks.job_fetching_tasks worker --beat --loglevel=info
```

---

## Quick Reference

```bash
# Most common commands

# 1. Check what's in database
python scripts/fetch_jobs_manual.py --stats

# 2. Fetch Kenya jobs NOW
python scripts/fetch_jobs_manual.py --region kenya

# 3. Clean up old jobs
python scripts/fetch_jobs_manual.py --cleanup

# 4. Start automated system
celery -A tasks.job_fetching_tasks worker --beat --loglevel=info
```

---

## Questions?

- **When do jobs get fetched?** Daily via Celery, or on-demand via script
- **Where are jobs stored?** MongoDB `jobs` collection
- **Are external APIs called on every user request?** NO! Only during fetch operations
- **How often should I run manual script?** Only when Celery isn't running
- **What if I want more jobs?** Run the script with `--region all` or add more categories
