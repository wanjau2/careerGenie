#!/bin/bash
# Stop Celery Worker and Beat Scheduler

echo "Stopping Celery..."
echo ""

# Stop Celery worker
if pgrep -f "celery.*worker" > /dev/null; then
    echo "Stopping Celery worker..."
    pkill -f "celery.*worker"
    echo "✅ Celery worker stopped"
else
    echo "ℹ️  Celery worker is not running"
fi

echo ""

# Stop Celery beat
if pgrep -f "celery.*beat" > /dev/null; then
    echo "Stopping Celery beat..."
    pkill -f "celery.*beat"
    echo "✅ Celery beat stopped"
else
    echo "ℹ️  Celery beat is not running"
fi

echo ""
echo "All Celery processes stopped"
