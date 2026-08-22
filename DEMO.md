# DEMO — reproducible in 3 commands

## Prereqs
- Node 20+, Python 3.11+
- `npm i -g openclaw`
- Env: `QWEN_API_KEY=...`  `DEVIN_API_KEY=...` (optional — tool degrades gracefully)

## Run
```bash
cp openclaw.json ~/.openclaw/openclaw.json      # Windows: copy openclaw.json %USERPROFILE%\.openclaw\openclaw.json
openclaw config validate
./run_demo.sh                                    # Windows: .\run_demo.ps1
```

## Expected output (sample 1 — [warung order])
```
[paste the real output here at 2:30 PM]
```

## What the judge should notice
1. Model used: `qwen/[id]` (see first log line)
2. Tool calls: `pasarapi.*` MCP tool → real Malaysian data returned
3. `devin_builder` invoked on sample 3 (unknown format) → Devin session URL printed
