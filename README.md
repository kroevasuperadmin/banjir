# [Kira] — [one-line: what it does for whom in Malaysia]

> Built at Devin × Claw Collective × Qwen AI Agents Hackathon 2026, Kuala Lumpur, 23 Aug 2026. Theme: AI for a Better Malaysia.

**Demo:** `demo/demo.gif` (45 sec)  ·  **Run it:** see [DEMO.md](DEMO.md)  ·  **Team:** Faris Irfan [+ names]

## Problem Validity
[2–4 sentences. Who in Malaysia, what breaks today, why now. One real number with a source link.]
- Who: [micro-SMEs / clinics / schools — be specific]
- Today: [the manual pain, in one line]
- Why now: [the 2026 trigger — regulation / policy / event]

## Stack Integration
All three partner technologies run at runtime, not just at build time.

| Partner | Role | Where in repo | What happens at runtime |
|---|---|---|---|
| **Qwen 3.8** (Alibaba Cloud) | Model layer — all reasoning & extraction | `openclaw.json` → `agents.defaults.model.primary: "qwen/[id]"` | Every LLM call (extraction, validation explanations, BM/EN output) |
| **OpenClaw** | Agent runtime — orchestration, tools, MCP | `openclaw.json`, `skills/[kira]/SKILL.md`, `tools/*.py` | Runs the agent loop, routes tool calls, connects PasarAPI MCP server (`https://pasarapi.xyz/mcp`) |
| **Devin** (Cognition) | (1) Built this repo — session: [link]. (2) Runtime tool `tools/devin_builder.py` | `tools/devin_builder.py` | When input format is unknown, the agent spawns a Devin session to generate a new connector |

Malaysian data source: PasarAPI (Malaysian/SEA open-data catalogue) via MCP — real government datasets, not mock data.

## Functionality
- One command: `./run_demo.sh` (or `run_demo.ps1`) → runs sample 1 end to end. Expected output in [DEMO.md](DEMO.md).
- Tested: `pytest` — [N] tests on 3 realistic Malaysian samples (`samples/`).
- Live demo recorded: `demo/demo.gif`.

## Sustainability
- **Real pilot users, not hypothetical:** [PulseLink (Malaysian SME network) / Helm AI's ~20 B2B clients — clinics, schools]. Pilot starts [date].
- Path to adoption: [how it reaches users — WhatsApp / existing platform / Helm module]
- Cost to run: Qwen per call ≈ [x]; zero-auth public data. Works for a 1-person warung.
- What's next (1 week): [3 bullets]

## Assumptions & limits
[Honest list. Judges (human and AI) trust repos that state limits.]
