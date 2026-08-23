#!/usr/bin/env bash
# Verify Banjir runs in 10 seconds.
set -e

API_BASE=${BANJIR_API_BASE:-http://127.0.0.1:8000}

# Kill any existing uvicorn on port 8000
for pid in $(lsof -ti :8000 2>/dev/null || true); do
    kill -9 "$pid" 2>/dev/null || true
done

# Start uvicorn
python -m uvicorn api.index:app --port 8000 &

echo "Waiting for server..."
for i in {1..30}; do
    if curl -s "$API_BASE/api/health" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

curl -s "$API_BASE/api/status?place=Gombak" | python -m json.tool
