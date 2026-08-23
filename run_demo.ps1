# Verify Banjir runs in 10 seconds.
$API_BASE = if ($env:BANJIR_API_BASE) { $env:BANJIR_API_BASE } else { "http://127.0.0.1:8000" }

try {
    Invoke-RestMethod -Uri "$API_BASE/api/health" -TimeoutSec 2 | Out-Null
} catch {
    Start-Process python -ArgumentList "-m uvicorn api.index:app --port 8000" -WindowStyle Hidden
    Start-Sleep -Seconds 8
}

Invoke-RestMethod -Uri "$API_BASE/api/status?place=Gombak" | ConvertTo-Json -Depth 5
