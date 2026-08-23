#!/usr/bin/env python
"""
THE WATCHER — a real, always-on background process.
Polls the live prod API for registered places on a fixed interval, compares
each station's status against the last poll, and proactively pushes a
Telegram alert the moment a station's status escalates (e.g. NORMAL -> ALERT,
ALERT -> WARNING). This is not a demo trick: it is an actual running process
that watches Malaysia's rivers whether or not anyone is looking at the app.

Run: python watcher.py            (foreground, logs to stdout)
     nohup python watcher.py &    (background)
State: watcher_state.json (last-seen status per station)
Log:   watcher.log (every poll, every alert, with real timestamps)
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

PROD = "https://banjirai.vercel.app"
BOT_TOKEN = "8786119365:AAFFuuArbsaza52vMq20MbU5wmAzBsCbMmw"
CHAT_ID = "5116627802"
PLACES = ["Gombak", "Shah Alam", "Kota Bharu", "Kuching", "Klang"]
INTERVAL_SECONDS = int(os.environ.get("WATCHER_INTERVAL", "300"))  # 5 min default

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "watcher_state.json")
LOG_FILE = os.path.join(HERE, "watcher.log")

MYT = timezone(timedelta(hours=8))

ESCALATION_ORDER = {"NORMAL": 0, "ALERT": 1, "WARNING": 2, "DANGER": 3, "OFFLINE": -1, "UNKNOWN": -1}


def log(msg):
    line = f"{datetime.now(MYT).isoformat()} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state):
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"))


def fetch_status(place):
    url = f"{PROD}/api/status?place={urllib.parse.quote(place)}"
    with urllib.request.urlopen(url, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def check_once(state):
    for place in PLACES:
        try:
            d = fetch_status(place)
        except Exception as e:
            log(f"POLL FAIL place={place} err={e}")
            continue
        jps = d.get("jps", {})
        stations = jps.get("nearest") or jps.get("stations") or []
        for s in stations[:5]:
            sid = s.get("station_id") or s.get("id") or s.get("name")
            if not sid:
                continue
            status = s.get("status", "UNKNOWN")
            prev = state.get(sid, {}).get("status")
            state[sid] = {"status": status, "name": s.get("name"), "place": place, "checked": datetime.now(MYT).isoformat()}
            if prev is None:
                continue  # first sighting, establish baseline, no alert
            if prev != status and ESCALATION_ORDER.get(status, -1) > ESCALATION_ORDER.get(prev, -1):
                msg = (
                    f"⚠️ BANJIR WATCHER\n\n{s.get('name')} ({s.get('district', place)})\n"
                    f"Status changed: {prev} -> {status}\n"
                    f"Level: {s.get('level')} m (alert {s.get('alert')} / warning {s.get('warning')} / danger {s.get('danger')})\n"
                    f"Source: JPS Malaysia, checked {datetime.now(MYT).strftime('%H:%M')}"
                )
                try:
                    send_telegram(msg)
                    log(f"ALERT SENT station={sid} {prev}->{status}")
                except Exception as e:
                    log(f"ALERT SEND FAIL station={sid} err={e}")
        log(f"poll ok place={place} stations={len(stations)}")
    save_state(state)


def main():
    log(f"WATCHER STARTED interval={INTERVAL_SECONDS}s places={PLACES}")
    state = load_state()
    while True:
        check_once(state)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
