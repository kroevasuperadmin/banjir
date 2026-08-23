# Paste this into Devin (Web/CLI) at 9:30. Edit [BRACKETS] to match the morning brief first.

Build **Kira** in this repo: a Malaysian e-invoice helper for micro-traders AND the citizens who need valid receipts for tax relief. Keep it small: ONE happy path, no auth, no database.

## JUDGING RUBRIC (50 pts) — build to this, nothing else
1. Prototype completeness /10 — a WORKING LIVE URL (deploy to Vercel) with a reliable end-to-end flow that handles 3 basic edge cases on stage.
2. Problem fit /10 — real PUBLIC problem, defined target users, 2-3 sourced numbers in README.
3. Solution quality & viability /10 — clear value + realistic adoption next steps (named pilot users in README).
4. Novelty & impact /10 — wow factor vs existing options + practical way to reach users.
5. Pitch clarity /10 — smooth demo; up to 2 pts for an AGENT-LED presentation → build a "Let Kira pitch" button (Qwen narrates a 30-second pitch on the live page).
The three tools (Hermes, Qwen, Devin) are an ELIGIBILITY GATE, not points. Use them, document them, don't over-engineer them.

## SHAPE
- `web/` — one-page Next.js app on Vercel: textarea "paste your WhatsApp order / receipt" → button → shows (a) the e-invoice JSON, (b) a clean bilingual CUSTOMER RECEIPT card (the hero), (c) missing-fields checklist in BM/EN. Plus the "Let Kira pitch" button. Mobile-first, judges will open it on phones.
- `agent/` — the same logic exposed as Hermes tools so the Telegram bot does the identical flow for traders.
- 3 edge cases handled gracefully with a friendly BM/EN message: missing TIN → uses "General Public" fallback and says so; non-MYR currency → refuses with explanation; garbage input → asks for the order text again. Put these 3 in `samples/` and in DEMO.md so I can trigger them live.

## STEP 0 — SMOKE TEST FIRST (30 minutes, before anything else)
Before building any feature: get ONE canned input (`samples/01_warung.txt`) running end-to-end through Hermes with Qwen as the model (send it via Telegram, get the JSON back) and printing a JSON result. Commit it as `smoke: first end-to-end run`. Then STOP and print the exact command + its output — I paste that at the top of README. Only after that passes do you continue with the rest of this brief. A polished agent that doesn't run scores zero; a crude one that runs makes finalist.

## SCOPE LIMIT — e-invoice compliance is too big for one day
Do NOT attempt full LHDN MyInvois compliance. Validate a FIXED subset of required fields only: supplier TIN, buyer TIN (or "General Public" 000000000000000 fallback), MSIC code (5-digit, looked up via PasarAPI), classification code, invoice date/time, currency MYR, line items with unit price + qty + SST. Put that list in `README.md → Assumptions & limits` verbatim and in `validate.py` as a single `REQUIRED_FIELDS` constant. Ship `samples/schema_subset.json` as the schema. State clearly that it's a subset.

## What it does
[A Malaysian micro-SME owner pastes a WhatsApp order / receipt text (or a photo path). The agent extracts buyer, items, amounts, SST, and produces an LHDN MyInvois-compliant e-invoice JSON, validates required fields (TIN, MSIC code, classification codes, currency MYR), and prints a plain-English + Bahasa Malaysia list of anything missing.]

## Hard constraints — the hackathon judge checks ALL THREE are used meaningfully at RUNTIME
1. **Hermes Agent** (the OpenClaw-family runtime the organisers mandated in their setup workshop; treat 'OpenClaw' in the rules as satisfied by Hermes unless they say otherwise) is the agent runtime. The agent runs INSIDE Hermes: Qwen is its model (custom OpenAI-compatible endpoint), our Python tools are registered as Hermes tools/skills, Telegram is the channel (BotFather bot already paired). Do not reimplement an agent loop in Python — Hermes IS the loop. Keep `./openclaw.json` only as a fallback if the organisers insist on OpenClaw proper.
2. **Qwen 3.8** is the model, served from ModelScope (modelscope.ai) as an OpenAI-compatible endpoint. Model ID = the full `Qwen-Ambassador/Qwen3.8-Max`-style ID from the organisers; base URL + key from env `QWEN_BASE_URL` / `QWEN_API_KEY`. Hermes uses it as the brain; any direct Python LLM call uses the same endpoint. Nothing goes through OpenAI/Anthropic.
3. **Devin** builds this repo (you). Commit often with clear messages; I'll link the session in README. Do NOT build any runtime Devin integration — no points for it.
4. **Malaysian data** via PasarAPI remote MCP server `https://pasarapi.xyz/mcp` (no auth) — already in `openclaw.json`. Use it to look up [MSIC codes / company registry / relevant gov dataset]. Also expose `tools/pasar_lookup.py` as a fallback using `GET https://pasarapi.xyz/api/search?q=...`.

## Deliverables
- `openclaw.json` finalized (keep the structure already there)
- `skills/[kira]/SKILL.md` — the agent's instructions (system prompt, output JSON schema, BM/EN tone)
- `tools/` — `extract.py`, `validate.py`, `pasar_lookup.py`
- `samples/` — 3 realistic Malaysian inputs (warung order, clinic receipt, online-shop order) + expected outputs
- `run_demo.sh` / `run_demo.ps1` — one command that runs sample 1 end to end locally; PLUS the Vercel URL printed in README
- `README.md → Problem fit` — 2-3 numbers with source links (MyInvois phase dates + thresholds; number of Malaysian micro-SMEs; tax-relief categories that require receipts)
- `DEMO.md` — exact commands + expected output, step by step
- `README.md` — fill the existing skeleton. Headers must stay exactly: Problem Validity / Stack Integration / Functionality / Sustainability.
- Tests: `pytest` covering validate.py on the 3 samples

## Rules
- Windows + macOS must both work (the builder is on Windows). Use pathlib, no bash-only tricks in Python.
- Every external call has a 10s timeout and a clear error message.
- Commit after each working step with clear messages. Do not ask me questions — make reasonable choices and list assumptions at the end.
- When done, print: the exact commands to run the demo, and the list of env vars needed.
