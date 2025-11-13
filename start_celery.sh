#!/bin/bash
# Start Celery Worker and Beat Scheduler
# This script starts both the worker and scheduler for automated job fetching

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

echo "=========================================="
echo "Starting Celery for Career Genie"
echo "=========================================="
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "   Starting Redis..."
    sudo systemctl start redis-server || sudo service redis-server start
    sleep 2
fi

echo "✅ Redis is running"
echo ""

# Create logs directory
mkdir -p logs

# Check if Celery is already running
if pgrep -f "celery.*worker" > /dev/null; then
    echo "⚠️  Celery worker is already running"
    echo "   Stop it first with: ./stop_celery.sh"
    echo ""
else
    echo "Starting Celery Worker..."
    ./venv/bin/celery -A tasks.job_fetching_tasks worker \
        --loglevel=info \
        --logfile=logs/celery_worker.log \
        --detach

    echo "✅ Celery worker started"
    echo "   Logs: logs/celery_worker.log"
fi

echo ""

if pgrep -f "celery.*beat" > /dev/null; then
    echo "⚠️  Celery beat is already running"
    echo "   Stop it first with: ./stop_celery.sh"
else
    echo "Starting Celery Beat (Scheduler)..."
    ./venv/bin/celery -A tasks.job_fetching_tasks beat \
        --loglevel=info \
        --logfile=logs/celery_beat.log \
        --detach

    echo "✅ Celery beat started"
    echo "   Logs: logs/celery_beat.log"
fi

echo ""
echo "=========================================="
echo "Celery Status"
echo "=========================================="
echo ""
echo "Scheduled Tasks:"
echo "  • fetch-global-jobs-daily: Runs daily at 2 AM"
echo "  • fetch-kenya-jobs-twice-daily: Runs at 2 AM and 2 PM"
echo "  • cleanup-old-jobs-weekly: Runs every Sunday at 3 AM"
echo ""
echo "Each task fetches 100 jobs per source per query!"
echo ""
echo "View logs:"
echo "  tail -f logs/celery_worker.log"
echo "  tail -f logs/celery_beat.log"
echo ""
echo "Stop Celery:"
echo "  ./stop_celery.sh"
echo ""
