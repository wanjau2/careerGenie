# CareerGenie - Railway Deployment Guide

## 🚂 Railway Deployment Configuration

### Current Server Information
- **Current Public IP**: 197.232.159.231
- **Platform**: Railway (Cloud PaaS)
- **Important**: Railway IPs can change on redeployment

---

## ⚠️ IMPORTANT: Railway IP Considerations

### Railway IP Behavior
Railway provides **dynamic outbound IPs** that can change when:
- You redeploy your application
- Railway scales your service
- Infrastructure maintenance occurs

### Impact on Careerjet API
Careerjet requires **IP whitelisting**, which can be problematic with Railway's dynamic IPs.

---

## 🔧 Solutions for Careerjet on Railway

### Option 1: Use Railway's Static Outbound IP (Recommended)
Railway offers static outbound IPs on **Pro plan** ($20/month):

1. **Upgrade to Railway Pro**:
   - Go to your Railway project settings
   - Upgrade to Pro plan
   - Enable "Static Outbound IP"

2. **Get Your Static IP**:
   ```bash
   # Railway will provide a static IP in your project settings
   # Look under: Settings > Networking > Static Outbound IP
   ```

3. **Whitelist in Careerjet**:
   - Use the static IP provided by Railway
   - Register at: https://www.careerjet.com/partners/api/
   - Whitelist the static IP in your dashboard

### Option 2: Use Proxy Service (Free Alternative)
If you want to stay on Railway's free tier, use a proxy:

1. **QuotaGuard Static** (Free tier available):
   - Sign up at: https://www.quotaguard.com/
   - Get your static IP
   - Add QuotaGuard to Railway as environment variable

2. **Configure Proxy in Careerjet Service**:
   ```python
   # In services/careerjet_rest_api.py
   proxies = {
       'http': os.getenv('QUOTAGUARD_URL'),
       'https': os.getenv('QUOTAGUARD_URL')
   }
   response = requests.get(self.base_url, params=params, proxies=proxies)
   ```

### Option 3: Skip Careerjet (Current Approach)
Your system is already working well without Careerjet:
- **SerpAPI**: 604 jobs fetched ✅
- **Greenhouse**: 237 jobs fetched ✅
- **Google Jobs Direct**: 165 jobs fetched ✅

You're getting **1,400+ jobs** without Careerjet, so this API is **optional**.

---

## 📋 Railway Environment Variables Setup

### Required Environment Variables for Railway

Go to your Railway project → Variables → Add these:

```bash
# MongoDB (Already configured)
MONGODB_URI=mongodb+srv://wanjau:YCcxYh2VtvkfHiZr@careergenie.w9saxx7.mongodb.net/CareerGenie?retryWrites=true&w=majority&appName=CareerGenie
DB_NAME=CareerGenie

# JWT Configuration
JWT_SECRET_KEY=WBEFlp7A5t3n8WlxjvJoAQD0kq0FfimodjXwQthmNak
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Flask Configuration
FLASK_ENV=production
PORT=8000
DEBUG=False

# SerpAPI (Working great!)
SERPAPI_KEY=1e7297556c2e6a28a2ab4f9efa55a73b3a65a8d0da71a501c63f644c86cf2bd5

# RapidAPI
RAPIDAPI_KEY=aa0310a77amsh86c1983fa2a943bp146108jsn1142ec5f3a54

# Google Services
GOOGLE_GEMINI_API_KEY=AIzaSyCpv1rs7UIV7O1Q25RrNBkRAz_dVDnA8xA

# Careerjet (Optional - only if you have static IP)
CAREERJET_AFFILIATE_ID=your_affiliate_id_here
SERVER_IP=your_railway_static_ip_here

# CORS - Add your production frontend URL
ALLOWED_ORIGINS=https://your-frontend-url.vercel.app,http://localhost:3000
```

---

## 🔄 Railway Deployment Workflow

### Initial Deployment
```bash
# Railway CLI (if not installed)
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

### Environment-Specific Considerations

#### Local Development (.env file)
- Use local `.env` file
- Redis on localhost
- Local file uploads

#### Railway Production (Environment Variables)
- **No Redis needed** for basic operation (job fetching uses direct MongoDB)
- **No local file storage** - use Railway Volumes or S3
- **Environment variables** instead of `.env` file

---

## 📊 Railway-Optimized Job Fetching

### Current Setup Analysis
Your job fetching is running **locally** (not on Railway). Here's what you need to know:

#### Where Job Fetching Happens:
1. **Local Machine** (Current):
   - Running: `python scripts/fetch_jobs_manual.py`
   - PID: 193139
   - Log: `/tmp/job_fetch_kenya_with_serpapi.log`
   - ✅ **This is fine!** Jobs are stored in MongoDB (cloud)

2. **Railway Server** (Future - Optional):
   - Would use Railway Cron Jobs
   - Or external cron service (e.g., cron-job.org)

#### Recommended Approach:
**Keep job fetching on your local machine or a separate VPS** because:
- Railway charges for compute time
- Job fetching takes 3-4 hours (expensive on Railway)
- Railway is best for serving API requests (instant, low compute)

---

## 🎯 Optimal Architecture for Railway

```
┌─────────────────────────────────────────────────────────┐
│ LOCAL MACHINE / VPS (Job Fetching)                     │
├─────────────────────────────────────────────────────────┤
│ - Run scripts/fetch_jobs_manual.py                     │
│ - Connects to MongoDB (cloud)                          │
│ - Fetches jobs from APIs                               │
│ - Stores in MongoDB                                     │
│ - Schedule: Daily via cron                             │
└─────────────────────────────────────────────────────────┘
                        ↓
                  (Stores in)
                        ↓
┌─────────────────────────────────────────────────────────┐
│ MONGODB ATLAS (Cloud Database)                         │
├─────────────────────────────────────────────────────────┤
│ - 1,400+ jobs stored                                    │
│ - All 196 categories                                    │
│ - Accessible from anywhere                             │
└─────────────────────────────────────────────────────────┘
                        ↓
                  (Queries from)
                        ↓
┌─────────────────────────────────────────────────────────┐
│ RAILWAY (Flask API Server)                             │
├─────────────────────────────────────────────────────────┤
│ - GET /api/jobs → Query MongoDB                        │
│ - GET /api/jobs?category=Nurse → Query MongoDB         │
│ - Fast, instant responses                              │
│ - Low compute usage = Low cost                         │
└─────────────────────────────────────────────────────────┘
                        ↓
                  (Serves to)
                        ↓
┌─────────────────────────────────────────────────────────┐
│ USERS (Flutter App / Web)                              │
│ - Instant job results from database                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Railway Deployment Checklist

### Pre-Deployment
- [ ] Set all environment variables in Railway dashboard
- [ ] Change `FLASK_ENV=production` and `DEBUG=False`
- [ ] Update `ALLOWED_ORIGINS` with your production frontend URL
- [ ] Remove Redis dependencies if not using Celery on Railway

### Post-Deployment
- [ ] Test API endpoints: `https://your-app.railway.app/health`
- [ ] Verify MongoDB connection works from Railway
- [ ] Check CORS allows your frontend
- [ ] Test job fetching from local machine → MongoDB → Railway API

### Ongoing
- [ ] Run job fetching locally or on a cheap VPS (not Railway)
- [ ] Schedule daily job fetches via cron
- [ ] Monitor Railway compute usage
- [ ] Monitor MongoDB storage (free tier: 512MB)

---

## 💡 Cost Optimization Tips

### Railway Costs
1. **API Serving**: ~$1-5/month (very light compute)
2. **Job Fetching on Railway**: ~$20-50/month (heavy compute) ❌ **Avoid this!**

### Recommended Setup (Low Cost)
1. **Railway**: Only for Flask API ($1-5/month)
2. **Local Machine**: Run job fetching script daily (FREE)
3. **MongoDB Atlas**: Free tier 512MB (should be enough for 30K jobs)

### Alternative (If local machine not always on)
1. **DigitalOcean Droplet**: $4/month
2. **Hetzner Cloud**: €4/month (~$4.50)
3. **Run cron job**: Fetch jobs daily

---

## 🔍 Current Status

### ✅ What's Working
- 27 categories fetched (13.8% complete)
- 1,405 jobs in database
- SerpAPI returning 604 jobs
- Greenhouse returning 237 jobs
- Job fetching running locally (FREE)

### ⚠️ What Needs Attention
1. **Careerjet**: Requires static IP (Railway Pro) or skip it
2. **Railway Environment Variables**: Need to be set for production deployment
3. **CORS**: Need to add production frontend URL

### 📝 Next Steps
1. **Option A**: Upgrade Railway to Pro for static IP + enable Careerjet
2. **Option B**: Skip Careerjet (you have 3 other working sources)
3. **Set Railway environment variables** for production
4. **Keep job fetching local** (or use cheap VPS)
5. **Deploy to Railway** (API serving only)

---

## 🎉 Summary

Your current setup is **already optimized** for Railway:
- ✅ Job fetching runs locally (no Railway compute costs)
- ✅ Jobs stored in MongoDB cloud (accessible from anywhere)
- ✅ Railway will serve API requests (instant, low cost)
- ✅ 3 job sources working without IP whitelisting

**Careerjet is optional.** You're getting great results without it!
