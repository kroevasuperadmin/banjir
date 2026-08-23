#!/usr/bin/env bash
# Verify Banjir runs in 10 seconds.
set -e

API_BASE=${BANJIR_API_BASE:-http://127.0.0.1:8000}

# Start uvicorn if not already listening
if ! curl -s "$API_BASE/api/health" > /dev/null 2>&1; then
    python -m uvicorn api.index:app --port 8000 &
    sleep 8
fi

curl -s "$API_BASE/api/status?place=Gombak" | python -m json.tool
