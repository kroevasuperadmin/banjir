# Verify Banjir runs in 10 seconds.
$API_BASE = if ($env:BANJIR_API_BASE) { $env:BANJIR_API_BASE } else { "http://127.0.0.1:8000" }

# Kill any existing listener on port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

# Start uvicorn
Start-Process python -ArgumentList "-m uvicorn api.index:app --port 8000" -WindowStyle Hidden

Write-Host "Waiting for server..."
for ($i = 0; $i -lt 30; $i++) {
    try {
        $null = Invoke-RestMethod -Uri "$API_BASE/api/health" -TimeoutSec 1
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

Invoke-RestMethod -Uri "$API_BASE/api/status?place=Gombak" | ConvertTo-Json -Depth 5
