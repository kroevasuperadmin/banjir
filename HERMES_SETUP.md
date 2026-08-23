# Hermes Agent — Windows setup for Banjir

Hermes Agent (Nous Research) = the agent runtime. One custom tool `flood_status(place)` → our API `GET /api/status?place=`. Telegram bot via Hermes gateway. Qwen via Alibaba Model Studio (intl) or OpenRouter.

Sources: https://github.com/NousResearch/hermes-agent · https://hermes-agent.nousresearch.com/docs (windows-native, configuring-models, integrations/providers, messaging/telegram, developer-guide/plugins, reference/cli-commands, reference/environment-variables). Tool-plugin contract verified against repo source (`hermes_cli/plugins.py` `register_tool`, `tools/registry.py` handler call). Items marked **UNVERIFIED** were not confirmed against docs/source.

## 0. Paths (Windows native)

| What | Path |
|---|---|
| Code (disposable) | `%LOCALAPPDATA%\hermes\hermes-agent\` |
| Config | `%LOCALAPPDATA%\hermes\config.yaml` |
| Secrets | `%LOCALAPPDATA%\hermes\.env` |
| Plugins (custom tools) | `%LOCALAPPDATA%\hermes\plugins\<name>\` |
| Skills | `%LOCALAPPDATA%\hermes\skills\` |
| Logs | `%LOCALAPPDATA%\hermes\logs\` |

Installer sets `HERMES_HOME=%LOCALAPPDATA%\hermes` and adds `%LOCALAPPDATA%\hermes\hermes-agent\bin` to user PATH. Docs that say `~/.hermes/...` = `%LOCALAPPDATA%\hermes\...` on Windows native (WSL2 uses `~/.hermes`).

## 1. Install (PowerShell, no admin)

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
# equivalent: iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```
- Installs Python 3.11 (via uv), Node, PortableGit if missing. Needs `git --version` to work or it provisions one.
- Skip the wizard: `& ([scriptblock]::Create((irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1))) -SkipSetup`
- **Open a NEW terminal** after install (PATH). Then `hermes doctor`.
- No pip/npm package route documented. Git-based install only. **UNVERIFIED:** `pip install hermes-agent` — not in docs, do not rely on it.
- Venue wifi: installer pulls from github.com + astral.sh (uv) + nodejs.org. If github.com/raw.githubusercontent.com is blocked, install is blocked — fall back to phone hotspot.

## 2. Model: Qwen (OpenAI-compatible)

### Option A — Alibaba Model Studio intl (native provider, preferred)
```powershell
hermes config set DASHSCOPE_API_KEY sk-xxxx          # goes to .env automatically
hermes config set DASHSCOPE_BASE_URL https://dashscope-intl.aliyuncs.com/compatible-mode/v1   # this IS the default; set anyway
hermes chat --provider alibaba --model qwen3.5-plus -q "hi"   # smoke test; swap model id to the one the workshop gave (e.g. qwen3.8-max)
```
Persist as default: `hermes model` → pick Alibaba/Qwen → model. Or in `config.yaml`:
```yaml
model:
  provider: alibaba
  default: qwen3.5-plus        # replace with workshop model id
```
**UNVERIFIED:** exact `model.provider` string for DashScope (`alibaba` is the documented `--provider` flag value; config key value assumed identical).

### Option B — any OpenAI-compatible URL (OpenRouter, DashScope, ModelScope)
`config.yaml`:
```yaml
model:
  default: qwen/qwen3.5-plus                    # model id as the endpoint expects it
  provider: custom
  base_url: https://openrouter.ai/api/v1        # or https://dashscope-intl.aliyuncs.com/compatible-mode/v1
  api_key: sk-or-xxxx                           # or leave out and set OPENAI_API_KEY in .env
  api_mode: chat_completions
```
`base_url` overrides `provider`. Custom endpoints use `model.api_key` → fallback `OPENAI_API_KEY`. They do NOT reuse `OPENROUTER_API_KEY`.

OpenRouter as first-class provider instead: `hermes config set OPENROUTER_API_KEY sk-or-xxxx` then `hermes chat --provider openrouter --model qwen/qwen3.5-plus`.

## 3. Custom tool: `flood_status(place)` (plugin)

Plugin = folder with `plugin.yaml` + `__init__.py` exposing `register(ctx)`. Handler gets `args: dict`, must return a JSON **string** (even on error), accept `**kwargs`. Plugins are opt-in: must be listed in `plugins.enabled`.

Files live in this repo at `hermes/plugins/banjir/`. Install = copy the folder:
```powershell
Copy-Item -Recurse -Force C:\Users\diony\dev\hackathon-claw-2026\hermes\plugins\banjir "$env:LOCALAPPDATA\hermes\plugins\banjir"
hermes plugins enable banjir        # writes plugins.enabled: [banjir] to config.yaml
hermes plugins list                 # banjir should show enabled, 1 tool
hermes plugins doctor banjir --ci   # manifest check
```

`plugin.yaml`:
```yaml
name: banjir
version: 0.1.0
description: "Banjir flood-status tool — calls the Banjir API (/api/status?place=)."
provides_tools:
  - flood_status
```

`__init__.py` (stdlib only):
```python
import json, os, urllib.parse, urllib.request

API_BASE = os.environ.get("BANJIR_API_BASE", "http://localhost:8000")

FLOOD_STATUS = {
    "name": "flood_status",
    "description": "Live Malaysian flood status for a place: nearest JPS river stations vs Alert/Warning/Danger thresholds, MET warnings, 24h forecast, checklist, hotlines, source+timestamp. Call for ANY 'banjir / is my area flooding' question. Never guess.",
    "parameters": {
        "type": "object",
        "properties": {"place": {"type": "string", "description": "Place as the user said it, e.g. 'Gombak', 'Kg Baru KL'"}},
        "required": ["place"],
    },
}

def flood_status(args: dict, **kwargs) -> str:
    place = (args.get("place") or "").strip()
    if not place:
        return json.dumps({"error": "place is required"})
    url = f"{API_BASE}/api/status?place={urllib.parse.quote(place)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        return json.dumps({"error": f"Banjir API unreachable: {e}", "url": url})

def register(ctx):
    ctx.register_tool(name="flood_status", toolset="banjir", schema=FLOOD_STATUS, handler=flood_status, emoji="🌊")
```

Point it at the deployed API instead of localhost: `setx BANJIR_API_BASE https://<vercel-url>` (new terminal after). **UNVERIFIED:** whether Hermes loads `.env` vars into `os.environ` before plugin import — use `setx`/system env to be safe.

Test: `hermes chat -q "Gombak banjir ke sekarang?"` → should call `flood_status`. In interactive `hermes chat`, `/plugins` shows status. Plugin tool-calls go through the normal tool loop; `--yolo` skips approval prompts if any appear.

Tool error → agent text. Handler never raises; the "API unreachable" JSON lets the model say "live feed is down" instead of hallucinating (data rule).

## 4. Telegram

1. Telegram → @BotFather → `/newbot` → name → username ending `bot` → copy token `123456789:ABC...`.
2. Your numeric user id: message @userinfobot.
3. Configure:
```powershell
hermes gateway setup          # interactive: pick Telegram, paste token, allowed users
# or non-interactive:
hermes config set TELEGRAM_BOT_TOKEN 123456789:ABCdefGHI...
hermes config set TELEGRAM_ALLOWED_USERS 123456789        # comma-separated ids; judges' ids can be added here
```
4. Run:
```powershell
hermes gateway run            # foreground — use this on stage, logs visible
hermes gateway start          # background (Windows: scheduled task via hermes gateway install)
hermes gateway status / stop / restart
```
5. Pairing (for users NOT in `TELEGRAM_ALLOWED_USERS`, e.g. a judge DMs the bot): bot replies `Pairing code: XKGH5N7P` → on the laptop:
```powershell
hermes pairing approve telegram XKGH5N7P
hermes pairing list
```
Codes expire in 1 h. Default policy denies everyone not allowlisted or paired.
6. Groups: BotFather → `/mybots` → Bot Settings → Group Privacy → Turn off, then remove + re-add bot to the group. Optional `config.yaml`:
```yaml
telegram:
  require_mention: false
```
7. Telegram API hosts (`api.telegram.org`) — test from venue wifi first: `curl https://api.telegram.org/bot<TOKEN>/getMe`. If blocked: `TELEGRAM_PROXY=socks5://...` or hotspot.

## 5. Headless / demo run order

```powershell
# terminal 1 — Banjir API
cd C:\Users\diony\dev\hackathon-claw-2026; python -m api            # whatever the api/ entrypoint is
# terminal 2 — agent via Telegram
hermes gateway run
# one-shot, no UI (scripts / pitch narration):
hermes -z "Give a 30-second Banjir pitch using flood_status('Gombak')"
hermes chat --quiet -q "Return only JSON: flood_status for Kota Bharu"
```
`hermes -z` = prompt in, final text out, nothing else on stdout. `-m`/`--provider` override per call without touching config.

Persona/instructions for the bot (BM+EN, cite publisher, never invent): put in `%LOCALAPPDATA%\hermes\SOUL.md` (agent identity file, documented). Copy from `hermes/SOUL.md` in this repo if present.

## 6. Unreachable / not done

- Nothing installed on this machine (per task). `hermes` not on PATH; `%LOCALAPPDATA%\hermes` does not exist.
- Plugin self-check ran: `python hermes\plugins\banjir\__init__.py` → correct error JSON (API not up yet). Re-run after API starts.
- `openclaw.json` in repo root is the OpenClaw-format config. Hermes does not read it. Same pasarapi MCP in Hermes `config.yaml` (verified key):
```yaml
mcp_servers:
  pasarapi:
    url: "https://pasarapi.xyz/mcp"
    timeout: 20
```
