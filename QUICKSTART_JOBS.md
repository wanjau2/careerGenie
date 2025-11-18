# Quick Start: Job Fetching System

## TL;DR

✅ **Jobs are stored in MongoDB and served from there**
✅ **External APIs only called during scheduled fetches**
✅ **You have 2 options: Celery (auto) OR Manual script**
✅ **196 job categories across ALL industries** (not just tech!)
✅ **Global platform serving everyone** - from Software Engineers to Chefs to Nurses

---

## Option 1: Automated (Celery) - RECOMMENDED

**Start the automated system:**

```bash
cd backend
source venv/bin/activate

# Make sure Redis is running first
redis-server &

# Start Celery worker + scheduler
celery -A tasks.job_fetching_tasks worker --beat --loglevel=info
```

**What happens:**
- ⏰ Daily at 2 AM: Fetches global jobs
- ⏰ 2 AM & 2 PM: Fetches Kenya jobs
- ⏰ Sundays 3 AM: Cleans up old jobs
- 🔄 Runs forever in background

**To stop:** `Ctrl+C`

---

## Option 2: Manual Script - FALLBACK

**When to use:** Celery isn't running OR you need jobs RIGHT NOW

### Quick Commands

```bash
cd backend
source venv/bin/activate

# 1. Check what's in database
python scripts/fetch_jobs_manual.py --stats

# 2. Fetch Kenya jobs NOW (takes ~1-2 hours)
python scripts/fetch_jobs_manual.py --region kenya

# 3. Fetch specific jobs quickly
python scripts/fetch_jobs_manual.py --region kenya \
  --categories "Data Engineer,Data Scientist,Python Developer"

# 4. Clean up old jobs
python scripts/fetch_jobs_manual.py --cleanup
```

---

## Current Status

Run this to see what's in your database:

```bash
python scripts/fetch_jobs_manual.py --stats
```

**Current output:**
```
Total jobs: 399
Active jobs: 399

Top cities:
  • New York: 104
  • Nairobi: 93
  • London: 86

Jobs by category:
  • Software Engineer: 115
  • Data Engineer: 11
  • Machine Learning: 11
```

---

## For Developers

### How it works:

1. **External APIs** (JSearch, LinkedIn, Glassdoor, Internships)
   ↓
2. **Job Aggregator** (fetches from all sources)
   ↓
3. **MongoDB** (stores jobs, prevents duplicates)
   ↓
4. **Flask API** (reads from MongoDB, NO external calls)
   ↓
5. **Flutter App** (displays jobs)

### When are external APIs called?

**ONLY during:**
- ✅ Celery scheduled tasks (daily)
- ✅ Manual script execution

**NEVER during:**
- ❌ User browsing jobs
- ❌ User login
- ❌ GET /api/jobs requests

---

## Files

| File | Purpose |
|------|---------|
| `tasks/job_fetching_tasks.py` | Celery automated tasks |
| `scripts/fetch_jobs_manual.py` | Manual fallback script |
| `scripts/README_JOB_FETCHING.md` | Full documentation |
| `routes/jobs.py` | API endpoint (reads from DB) |
| `services/job_aggregator.py` | Multi-source fetching |
| `models/job.py` | Job database model |

---

## FAQ

**Q: Do I need to run both Celery AND the manual script?**
A: No. Pick one:
- **Production:** Use Celery (automated)
- **Development/Testing:** Use manual script as needed

**Q: How long does it take to fetch jobs?**
A:
- Kenya only: ~1-2 hours
- All regions: ~6-8 hours (don't do this often!)

**Q: What if I get rate limit errors?**
A: The script auto-backs off 60s on 429 errors. If persistent, increase delays.

**Q: How do I know if jobs are being fetched?**
A: Run `python scripts/fetch_jobs_manual.py --stats` to see count increasing.

**Q: Can users browse jobs now?**
A: YES! You have 399 jobs in the database ready to serve.

---

## One-Liner for Production

```bash
# Start everything needed for job system
redis-server &
celery -A tasks.job_fetching_tasks worker --beat --loglevel=info &
python app.py
```

---

## Need Help?

1. Check `scripts/README_JOB_FETCHING.md` for full documentation
2. Check `JOBS_SYSTEM_SUMMARY.md` for architecture overview
3. Run `python scripts/fetch_jobs_manual.py --help` for all options
