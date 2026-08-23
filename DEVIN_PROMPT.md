# BANJIR — build spec for Devin

You are building **Banjir**, a Malaysian flood-awareness agent, at a one-day hackathon (#BuildForMsia). Submission is at 16:00 today. Optimise for: a WORKING LIVE URL, real data, graceful edge cases, and a demo that never stalls. Minimal code, minimal dependencies, commit after every working step.

## What it does (one happy path)
A person types or says where they are — "Gombak", "Kg. Baru Kuala Lumpur", "Kota Bharu" — and gets, in Bahasa Malaysia + English:
1. **Risk now**: the nearest JPS river stations, their current level vs the Alert/Warning/Danger thresholds, trend, and the timestamp (LIVE, scraped from JPS publicinfobanjir — see `data/jps.py`).
2. **Official warnings**: active MET Malaysia warnings that mention their state/area (LIVE — `data/met.py`).
3. **Next 24h**: MET forecast for the nearest location (LIVE — `data/met.py`).
4. **What to do**: a short checklist matched to the risk level + official hotlines (`data/EMERGENCY.md`; relief-centre data via `data/pps.py` if available, otherwise an honest "not available" line with the official link).
5. Every number carries its source + timestamp. Never invent. If a feed is down, say so in the UI.

## The judging rubric (50 pts) — build to this
1. Prototype completeness /10 — live URL on Vercel, end-to-end, handles 3 edge cases on stage: (a) unknown place → ask again + suggest nearby districts; (b) station offline / '-' values → shown as "no reading", not 0; (c) JPS site down → cached last-good data with a visible "last updated X min ago" badge.
2. Problem fit /10 — real public problem with evidence (`EVIDENCE.md` → put 3 stats in the README).
3. Solution quality & viability /10 — clear value + realistic next steps (see README skeleton).
4. Novelty & impact /10 — nobody else has live JPS thresholds per station in plain BM; the "Let Banjir explain" agent voice.
5. Pitch clarity /10 — smooth demo; +2 pts for an AGENT-LED presentation → a "Let Banjir pitch" button on the page where the agent narrates a 30-second pitch using today's real readings.

## Stack (eligibility gate — all must be present and documented)
- **Devin** (you) builds it. Commit messages prefixed `devin:`.
- **Hermes Agent** = the agent runtime. Telegram bot via Hermes; tools defined per `HERMES_SETUP.md`. The Hermes tool `flood_status(place)` calls our own HTTP API (`/api/status?place=`). Web page and Telegram share the same API.
- **Qwen** = the LLM that turns structured readings into the BM/EN explanation + the narrated pitch. OpenAI-compatible endpoint from env `QWEN_BASE_URL` / `QWEN_API_KEY` / `QWEN_MODEL` (e.g. `qwen3.8-max`). If the key is missing, fall back to a deterministic template so the demo never dies.

## Shape — keep it this small
```
data/jps.py        # live JPS scraper (exists) – do not rewrite, fix only if broken
data/met.py        # MET warnings + forecast (exists)
data/pps.py        # relief centres (exists; may return available:false)
data/EMERGENCY.md  # hotlines + checklist (exists)
api/               # Python (FastAPI or stdlib http.server) → GET /api/status?place=..., GET /api/pitch
web/               # ONE page (Next.js or plain HTML+JS) deployed on Vercel: input box → status cards → checklist → "Let Banjir pitch" button. Mobile-first; judges open it on phones.
hermes/            # tool definition + SKILL/instructions for the Telegram agent (see HERMES_SETUP.md)
samples/           # 3 canned places incl. the 3 edge cases
README.md          # fill the skeleton; keep the "Verify it runs (10 seconds)" block at the top
DEMO.md            # exact steps for the live demo + the 3 edge cases
```
Deployment: Vercel. If Python on Vercel is awkward, put the API in Next.js API routes and port the three data modules to TypeScript — but ONLY if the Python route fails; do not rewrite working code for style.

## Step 0 — smoke test first (30 min)
`GET /api/status?place=Gombak` returns real JPS stations with today's timestamp + MET data, and the web page renders it. Commit `devin: smoke test green`. Print the curl command + output — it goes at the top of README. Only then add Qwen explanation, the pitch button, Telegram, edge cases.

## Rules
- Windows + macOS both work. 10s timeouts on every external call. Cache JPS/MET for 5 min.
- Cite the publisher on every card: "Source: JPS Malaysia (publicinfobanjir) · updated 09:25".
- Do not ask questions; choose, and list assumptions at the end.
- When done print: Vercel URL, the curl smoke test, env vars needed, and the list of files.
