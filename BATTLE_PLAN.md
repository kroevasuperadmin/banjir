# Devin x Claw Collective x Qwen Hackathon — 23 Aug 2026 — BATTLE PLAN

Check-in 8:45 · Workshops 9:00 · Sprint 9:30–4:00 (HARD) · AI prelim judging 5:00 → 6 finalists · Live demos → 3 winners 6:00
Criteria (no weights): Problem validity · Stack integration (ALL THREE) · Functionality (runs live) · Sustainability (would users adopt)

## THE ONE INSIGHT
Preliminary judging is done BY AN AI AGENT. ~50 teams → 6 finalists, decided by a machine reading repos.
Everyone else builds for humans. You build for the judge that actually cuts 90% of the field:
- README headers = the 4 criteria, verbatim. The judge pattern-matches.
- "Stack Integration" section = table: tool → exact file path → what it does at runtime. Zero ambiguity.
- Devin session links + Qwen model ID + OpenClaw config path all in README. Proof, not claims.
- A 45-sec demo.gif/mp4 IN the repo. An AI judge can't watch you demo; it can read a transcript + see a GIF exists.
- `DEMO.md` = exact commands + expected output. Reproducible = "functionality: runs".

## ROLES OF THE 3 TOOLS (natural, not forced — judge checks "meaningful")
- Qwen 3.8  = THE BRAIN. OpenClaw primary model. `agents.defaults.model.primary: "qwen/qwen3.7-plus"` (swap to 3.8 ID given at workshop).
- OpenClaw  = THE BODY. Agent runtime. Tools = PasarAPI remote MCP (Malaysian gov data, zero auth) + your custom tools.
- Devin     = THE HANDS, TWICE. (1) Builds the code (paste DEVIN_PROMPT.md at 9:30). (2) RUNTIME: an OpenClaw tool that calls Devin API to write new connectors on demand. Runtime use beats "we used it to build" — most teams only do #1.

## DEFAULT IDEA (flex to the brief when revealed at 9:00)
**"Kira" — e-Invoice agent for micro-SMEs.** LHDN MyInvois is mandatory and the smallest businesses hit the wall in 2026. A warung/clinic owner forwards a WhatsApp order / photo receipt → agent extracts → validates against LHDN fields (TIN, MSIC, classification codes) → produces compliant e-invoice JSON → flags what's missing in BM/English.
Why it wins the criteria:
- Problem validity: legally mandated, every Malaysian business, 2026 timing. Judge recognises it instantly.
- Sustainability: YOU HAVE REAL USERS. Say it: "PulseLink (Malaysian SMEs) and Helm AI's 20 clinics/schools — we pilot Monday." Nobody else in the room has a customer.
- Malaysian data: PasarAPI MCP → MSIC codes / company registry / gov datasets. Real data, not mock.
Fallbacks if brief forces a lane:
- Education → "Cikgu" agent: teacher admin automation (Helm's schools = real users).
- Fintech/SME → "Tender" agent: scans gov tenders/grants (ePerolehan, Cradle, MDEC via PasarAPI) and drafts the application.
- Social impact → flood/disaster info agent over data.gov.my feeds.
Rule: whatever the brief, keep (a) Malaysian gov data via PasarAPI, (b) a named real pilot user, (c) one happy-path demo.

## SCOPE LAW (you are a vibe-coder with 6.5 hours)
ONE happy path. Input → agent → output. No auth, no DB, no UI beyond a terminal/Telegram/WhatsApp chat.
Stop building at 2:30 PM. 2:30–3:30 = README + GIF + DEMO.md + rehearse. 3:30–4:00 = submit with buffer.
Record the demo video at 2:45 when it works. Live demos die; the GIF in the repo is your insurance.

## TIMELINE
09:00 Workshops — get the 3 API keys + the official Qwen 3.8 model ID + how they want submissions. Ask: "what does the judging agent read — repo URL? form?"
09:30 `git clone` this scaffold → Devin: paste DEVIN_PROMPT.md (edited to the brief). **Devin's FIRST job is a 30-min scaffold + SMOKE TEST**: one canned order (`samples/01_warung.txt`) runs end-to-end through OpenClaw+Qwen and prints JSON. Nothing else until that passes.
10:00 SMOKE TEST GREEN = the real start. Paste its command + output at the TOP of README (the judge verifies "it runs" in 10 seconds). Only now let Devin add validation, PasarAPI, Devin-tool, BM output.
11:00 Second end-to-end run with the full path. Fix with Devin (paste errors), Claude Code for config.
13:00 Lunch — talk to organisers (Hoh Jia Da, shuenrui, Xavier Loo). Be memorable before judging.
14:30 FREEZE. Polish README to the 4 criteria. Record GIF. DEMO.md.
15:30 Submit. Then rehearse the 2-min pitch 5x.
17:00 If finalist: Problem (20s) → live demo (60s) → "real users Monday" (20s) → stack slide (20s).

## TEAM
Solo is fine (allowed) but a 2nd pair of hands who can read a stack trace doubles your odds. Ask at check-in: "anyone solo who can code? I have the idea, the scaffold, and real customers." Pitch the customers — that's your leverage.

## WHAT'S IN THIS FOLDER
- BATTLE_PLAN.md  — this
- DEVIN_PROMPT.md — paste into Devin at 9:30 after editing [BRACKETS]
- openclaw.json   — config template: Qwen primary + PasarAPI MCP + Devin tool
- README.md       — judge-optimised README skeleton, fill the blanks
- DEMO.md         — reproducible run script skeleton
- PITCH.md        — 2-min finalist pitch skeleton
