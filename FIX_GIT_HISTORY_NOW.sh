#!/bin/bash
# Script to remove sensitive files from git history

echo "Starting git history cleanup..."

# Reset any previous filter-branch attempts
rm -rf .git/refs/original/

# Remove files one at a time (safer approach)
echo "Removing RAILWAY files..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch RAILWAY_DEPLOYMENT.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch RAILWAY_QUICK_START.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch RAILWAY_REDIS_CELERY_SETUP.md' \
  --prune-empty --tag-name-filter cat -- --all

echo "Removing OAuth files..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch GOOGLE_OAUTH_SETUP_GUIDE.md' \
  --prune-empty --tag-name-filter cat -- --all

echo "Removing other sensitive docs..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch UDEMY_AND_ADS_GUIDE.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch UDEMY_SETUP_INSTRUCTIONS.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch IMPORT_SUMMARY.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch SYSTEM_VERIFICATION.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch FINAL_TEST_REPORT.md' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch MONETIZATION_TEST_REPORT.md' \
  --prune-empty --tag-name-filter cat -- --all

echo "Removing test scripts..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch comprehensive_job_test.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_all_endpoints.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_complete_app.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_jobs_api.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_monetization.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_udemy_api.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_udemy_free_api.sh' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch find_udemy_endpoint.sh' \
  --prune-empty --tag-name-filter cat -- --all

echo "Removing log files..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch import_log.txt' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch udemy_test_results.txt' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch TEST_SUMMARY.txt' \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch SUMMARY_INSTRUCTIONS.txt' \
  --prune-empty --tag-name-filter cat -- --all

echo "Cleaning up..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "Done! Now you can force push with:"
echo "git push --force origin master"
