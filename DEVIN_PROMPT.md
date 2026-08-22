# Paste this into Devin (Web/CLI) at 9:30. Edit [BRACKETS] to match the morning brief first.

Build a working CLI agent project called **[Kira]** in this repo. Python 3.11. Keep it small: ONE happy path, no auth, no database, no web UI.

## What it does
[A Malaysian micro-SME owner pastes a WhatsApp order / receipt text (or a photo path). The agent extracts buyer, items, amounts, SST, and produces an LHDN MyInvois-compliant e-invoice JSON, validates required fields (TIN, MSIC code, classification codes, currency MYR), and prints a plain-English + Bahasa Malaysia list of anything missing.]

## Hard constraints — the hackathon judge checks ALL THREE are used meaningfully at RUNTIME
1. **OpenClaw** is the agent runtime. The agent must run via OpenClaw (config at `./openclaw.json`, copy to `~/.openclaw/openclaw.json`). Tools are registered as OpenClaw tools/skills. Do not reimplement an agent loop in Python — OpenClaw IS the loop.
2. **Qwen** is the model. OpenClaw `agents.defaults.model.primary` = `qwen/[qwen3.7-plus → replace with the Qwen 3.8 ID given at the workshop]`. API key from env `QWEN_API_KEY`. Every LLM call goes through Qwen, none through OpenAI/Anthropic.
3. **Devin** is used at runtime: implement `tools/devin_builder.py` — an OpenClaw tool that calls the Devin API (`POST https://api.devin.ai/v1/sessions`, bearer `DEVIN_API_KEY`) with a prompt to generate a new data connector when the agent hits an input format it can't parse. Return the session URL. If the key is missing, log clearly and continue.
4. **Malaysian data** via PasarAPI remote MCP server `https://pasarapi.xyz/mcp` (no auth) — already in `openclaw.json`. Use it to look up [MSIC codes / company registry / relevant gov dataset]. Also expose `tools/pasar_lookup.py` as a fallback using `GET https://pasarapi.xyz/api/search?q=...`.

## Deliverables
- `openclaw.json` finalized (keep the structure already there)
- `skills/[kira]/SKILL.md` — the agent's instructions (system prompt, output JSON schema, BM/EN tone)
- `tools/` — `extract.py`, `validate.py`, `pasar_lookup.py`, `devin_builder.py`
- `samples/` — 3 realistic Malaysian inputs (warung order, clinic receipt, online-shop order) + expected outputs
- `run_demo.sh` / `run_demo.ps1` — one command that runs sample 1 end to end
- `DEMO.md` — exact commands + expected output, step by step
- `README.md` — fill the existing skeleton. Headers must stay exactly: Problem Validity / Stack Integration / Functionality / Sustainability.
- Tests: `pytest` covering validate.py on the 3 samples

## Rules
- Windows + macOS must both work (the builder is on Windows). Use pathlib, no bash-only tricks in Python.
- Every external call has a 10s timeout and a clear error message.
- Commit after each working step with clear messages. Do not ask me questions — make reasonable choices and list assumptions at the end.
- When done, print: the exact commands to run the demo, and the list of env vars needed.
