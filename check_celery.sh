#!/bin/bash
# Check Celery status and view recent logs

echo "=========================================="
echo "Celery Status Check"
echo "=========================================="
echo ""

# Check Redis
echo "Redis Status:"
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis is running"
else
    echo "  ❌ Redis is not running"
fi

echo ""

# Check Celery Worker
echo "Celery Worker:"
if pgrep -f "celery.*worker" > /dev/null; then
    PID=$(pgrep -f "celery.*worker")
    echo "  ✅ Running (PID: $PID)"
else
    echo "  ❌ Not running"
fi

echo ""

# Check Celery Beat
echo "Celery Beat:"
if pgrep -f "celery.*beat" > /dev/null; then
    PID=$(pgrep -f "celery.*beat")
    echo "  ✅ Running (PID: $PID)"
else
    echo "  ❌ Not running"
fi

echo ""
echo "=========================================="
echo "Recent Worker Logs (last 20 lines)"
echo "=========================================="
if [ -f logs/celery_worker.log ]; then
    tail -20 logs/celery_worker.log
else
    echo "No worker logs found"
fi

echo ""
echo "=========================================="
echo "Recent Beat Logs (last 10 lines)"
echo "=========================================="
if [ -f logs/celery_beat.log ]; then
    tail -10 logs/celery_beat.log
else
    echo "No beat logs found"
fi

echo ""
echo "To view live logs:"
echo "  tail -f logs/celery_worker.log"
echo "  tail -f logs/celery_beat.log"
