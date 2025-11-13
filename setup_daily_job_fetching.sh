#!/bin/bash
# Setup script for daily automatic job fetching

echo "Setting up daily job fetching for Career Genie..."

# Get the absolute path to the backend directory
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$BACKEND_DIR/venv/bin/python"
SCRIPT_PATH="$BACKEND_DIR/fetch_global_jobs.py"
LOG_PATH="$BACKEND_DIR/logs/job_fetching.log"

# Create cron job entry
CRON_JOB="0 2 * * * cd $BACKEND_DIR && $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "⚠️ Cron job already exists"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "$SCRIPT_PATH"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added successfully!"
    echo ""
    echo "Job will run daily at 2:00 AM"
    echo "Logs will be saved to: $LOG_PATH"
fi

echo ""
echo "To view all cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e"
echo "  (then delete the line containing fetch_global_jobs.py)"
echo ""
echo "To test the script manually:"
echo "  $PYTHON_PATH $SCRIPT_PATH"
