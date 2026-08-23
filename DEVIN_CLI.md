# Devin CLI — non-interactive cheatsheet (verified 23 Aug 2026, devin 3000.5.20, Windows/Git Bash)

Binary: `C:/Users/diony/AppData/Local/devin/cli/bin/devin.exe` (logged in as admin@kroeva.com, org kroevasuperadmin).
Run everything from the repo root: `cd /c/Users/diony/dev/hackathon-claw-2026`.

## 1. Run a task from a prompt file, no TUI (VERIFIED)

```bash
DEVIN=/c/Users/diony/AppData/Local/devin/cli/bin/devin.exe
cd /c/Users/diony/dev/hackathon-claw-2026
$DEVIN --model glm-5-2 --permission-mode dangerous --respect-workspace-trust false \
  --prompt-file DEVIN_PROMPT.md --export devin-session.json -p </dev/null 2>&1 | tee devin-run.log
```

- `-p` / `--print` = single-turn, prints the response to stdout, exits 0. No REPL.
- `--prompt-file FILE` = the prompt. `-p` with no inline prompt takes it from the file (verified).
- `--respect-workspace-trust false` = REQUIRED in print mode; otherwise it fails on an untrusted dir (can't show the trust prompt).
- `--permission-mode`:
  - `auto` (default) = read-only auto-approved, writes/shell PROMPT -> hangs in print mode. Do not use for a build.
  - `accept-edits` = file edits auto, shell still prompts.
  - `smart` = edits auto + a fast model judges shell commands (may not be enabled on the account).
  - `dangerous` (aliases `yolo`, `bypass`) = approves everything. Use this for the unattended build.
  - `autonomous` needs `--sandbox` = macOS/Linux only. Not on Windows.
- `--export [PATH]` = writes the whole conversation (ATIF JSON) after every turn. Commit it as proof Devin was used.
- `</dev/null` so it never waits on stdin.

Smoke test (free model, trivial prompt): exit 0, answer printed, took 88 s wall (GLM free tier is slow — budget for it).

## 2. Picking a model (`devin models list`)

`--model` takes a family slug, alias, or UID. Aliases: `opus`, `sonnet`/`claude`, `gpt`, `codex`, `gemini`, `swe`, `haiku`.
Cheap options (organiser asked for GLM / DeepSeek):

| UID | Price | Context |
|---|---|---|
| `glm-5-2` | FREE (GLM-5.2 High) | 200K |
| `swe-1-7`, `swe-1-7-medium` | FREE (Cognition SWE-1.7) | 262K |
| `deepseek-v4-flash-low/high/max` | $0.14 in / $0.28 out per 1M | 1M |
| `glm-5-2-max`, `glm-5-2-1m`, `glm-5-2-none` | $0.70 / $2.20 | 200K–1M |
| `deepseek-v4-pro-low/high/max` | $1.74 / $3.48 | 1M |
| `adaptive` | $0.50 / $2.00, auto-routes | — |

Everything else listed (40 families): Claude Opus 5 / Fable 5 / Sonnet 5 / Opus 4.8 / 4.7 / 4.6 / Sonnet 4.6 / 4.5 / Haiku 4.5, GPT-5.6 Sol/Luna/Terra, GPT-5.5 / 5.4 / 5.4-mini / 5.3-Codex / 5.2 / 5.1 / 4.1, Gemini 3.7/3.6/3.5/3.1-pro/3-flash, Grok 4.5/4.6, Kimi K3 / K2.7 / K2.6, Nemotron 3 Ultra, Inkling, SWE-1.7 Lightning, SWE-1.6. Full list: `devin models list` (or `--format json`).

Recommendation: `--model glm-5-2` (free) for the build; `--model deepseek-v4-flash-high` if GLM is too slow or flakes. Env alternative: `DEVIN_MODEL=glm-5-2`.

## 3. Continue / resume a session (VERIFIED)

```bash
$DEVIN list --format json                     # sessions in THIS directory: id, title, last_activity
$DEVIN -c -p "next: wire the Telegram bot" --respect-workspace-trust false </dev/null   # continue most recent in this dir
$DEVIN -r <session-id> -p "fix X" --respect-workspace-trust false </dev/null            # continue a specific one
```

- Session IDs are word pairs (e.g. `sneaky-friction`); `-r` accepts an unambiguous prefix.
- `--model` is IGNORED on resume (warning printed) — the session keeps its saved model.
- Resume of a trivial session took 27 s.
- `devin rm --force <id>` deletes a session non-interactively (without `--force` it errors in print mode).

## 4. Shareable session link

Local CLI sessions have NO web URL — they live on disk under `%APPDATA%\devin`. Ways to show judges Devin was used:

1. `--export devin-session.json` (above) → commit the file. Verified flag; file is the full transcript.
2. Interactive only: `/handoff` inside a REPL session packages context + branch into a cloud Devin session at app.devin.ai (that one has a shareable URL). Not testable non-interactively; untested here.
3. `devin cloud drs sandbox-create --repo <owner/repo> --prompt "..."` creates a cloud session for a GitHub repo (docs only, untested; needs the repo pushed to GitHub).
4. `/usage` and `/session-stats` in the REPL show credits/ACUs consumed — screenshot for the pitch.

## 5. Gotchas

- Always pass the prompt via `--prompt-file` or after `--`; a bare first word is parsed as a subcommand.
- `auth status` / `doctor` are safe checks: `$DEVIN auth status`, `$DEVIN doctor --json`.
- Config: `%APPDATA%\devin\config.json` (currently `{"version":1}`). Set a default model there with `{"agent":{"model":"glm-5-2"}}` if you want to drop `--model`.
- Docs: docs.devin.ai/cli/essential-commands, /cli/models, /cli/reference/commands (all reachable on venue wifi; `docs.devin.ai/cli/llms.txt` = 404, use `docs.devin.ai/llms.txt`).
