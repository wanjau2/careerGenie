#!/bin/bash

echo "=========================================="
echo "🎯 CareerGenie Backend Monitor"
echo "=========================================="
echo ""
echo "✅ Backend running on: http://localhost:8000"
echo "📊 Database: 1,778 jobs available"
echo "👤 Test user: wanjaueugene@gmail.com"
echo ""
echo "📝 ENHANCED LOGGING ENABLED!"
echo "   - Preferences updates"
echo "   - History filters"
echo "   - Date parsing"
echo "   - Job fetching"
echo ""
echo "=========================================="
echo "🔍 MONITORING ALL REQUESTS..."
echo "=========================================="
echo ""
echo "Now run your Flutter app and watch the requests below:"
echo ""

# Monitor with colored output
tail -f /tmp/backend_debug.log | while read line; do
    # Color code different types of messages
    if [[ $line == *"🔧"* ]] || [[ $line == *"UPDATE"* ]] || [[ $line == *"PUT"* ]]; then
        echo -e "\033[1;34m$line\033[0m"  # Blue for updates
    elif [[ $line == *"❌"* ]] || [[ $line == *"ERROR"* ]] || [[ $line == *"EXCEPTION"* ]]; then
        echo -e "\033[1;31m$line\033[0m"  # Red for errors
    elif [[ $line == *"⚠️"* ]] || [[ $line == *"WARNING"* ]]; then
        echo -e "\033[1;33m$line\033[0m"  # Yellow for warnings
    elif [[ $line == *"✅"* ]] || [[ $line == *"SUCCESS"* ]]; then
        echo -e "\033[1;32m$line\033[0m"  # Green for success
    elif [[ $line == *"GET"* ]] || [[ $line == *"POST"* ]] || [[ $line == *"DELETE"* ]]; then
        echo -e "\033[1;36m$line\033[0m"  # Cyan for HTTP requests
    else
        echo "$line"
    fi
done
