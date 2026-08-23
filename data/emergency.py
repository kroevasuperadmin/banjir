# -*- coding: utf-8 -*-
"""Parse data/EMERGENCY.md into hotlines and checklists by risk level."""
import os
import re
from pathlib import Path

_MD = Path(__file__).with_name("EMERGENCY.md").read_text(encoding="utf-8")


def _clean(s):
    return re.sub(r"\s+", " ", s).strip()


def _national():
    out = []
    m = re.search(r"## Emergency numbers \(national\)(.*?)(?=\n## |\Z)", _MD, re.S)
    if not m:
        return out
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        text = line[1:].strip()
        # format: **number(s)** \u2014 title ...
        bm = re.match(r"\*\*([^*]+?)\*\*\s*(?:\u2014|-)\s*(.*?)(?:\.|\bVerified from|\b\()", text)
        if not bm:
            continue
        numbers_part = bm.group(1).strip()
        title = (bm.group(2).strip() or "National hotline").replace("\u2014", "-")
        title = re.split(r"\s*[,(]", title, 1)[0].strip()
        numbers = [n.strip() for n in re.split(r"/| dan | and ", numbers_part) if n.strip()]
        out.append({"title": title, "numbers": numbers})
    return out


def _state_hotlines():
    out = {}
    m = re.search(r"## State hotlines(.*?)## Where to get live info", _MD, re.S)
    if not m:
        return out
    section = m.group(1)
    category = "State hotline"
    for line in section.splitlines():
        h = re.match(r"^###\s+(.+)$", line)
        if h:
            category = h.group(1).strip().replace("\u2014", "-")
            continue
        line = line.strip()
        if not line.startswith("-"):
            continue
        text = line[1:].strip()
        # format: **State:** number(s)   OR   **State: number(s)**
        sm = re.match(r"\*\*([^*]+?):\s*\*\*\s*(.*)", text)
        if not sm:
            sm = re.match(r"\*\*([^*]+?)\*\*\s*:\s*(.*)", text)
        if not sm:
            continue
        state_raw = sm.group(1).strip()
        numbers_part = sm.group(2).strip()
        state = normalize_state(state_raw)
        numbers = [n.strip() for n in re.split(r"/| dan | and ", numbers_part) if n.strip()]
        out.setdefault(state, []).append({
            "category": category,
            "state_raw": state_raw,
            "numbers": numbers,
        })
    return out


def normalize_state(state):
    if not state:
        return ""
    s = state.lower()
    s = re.sub(r"\bwp\b", "", s)
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _checklist():
    out = {}
    for phase, bm in (("before", "Sebelum"), ("during", "Semasa"), ("after", "Selepas"), ("bag", "Beg Kecemasan")):
        pat = rf"\*\*([^*]*?{bm}[^*]*?):\*\*\s*(.*?)(?=\n\*\*[^*]+?:\*\*|\n## |\Z)"
        m = re.search(pat, _MD, re.S | re.I)
        if not m:
            continue
        items = []
        for line in m.group(2).splitlines():
            line = line.strip()
            if line.startswith("-"):
                item = re.sub(r"\*\*", "", line[1:].strip()).strip()
                if " \u00b7 " in item:
                    # one line may contain multiple BM (EN) chunks separated by ·
                    for chunk in [c.strip() for c in item.split(" \u00b7 ")]:
                        match = re.match(r"(.+?)\s*\(([^)]+)\)\s*$", chunk)
                        if match:
                            items.append({"bm": match.group(1).strip(), "en": match.group(2).strip()})
                        else:
                            items.append({"bm": chunk, "en": chunk})
                elif " \u2014 " in item or " - " in item:
                    sep = " \u2014 " if " \u2014 " in item else " - "
                    parts = [p.strip() for p in item.split(sep, 1)]
                    items.append({"bm": parts[0], "en": parts[1]})
                else:
                    items.append({"bm": item, "en": item})
        out[phase] = items
    return out


NATIONAL = _national()
STATE_HOTLINES = _state_hotlines()
CHECKLIST = _checklist()


def hotlines_for(state):
    state_norm = normalize_state(state)
    state_entries = STATE_HOTLINES.get(state_norm, [])
    return {"national": NATIONAL, "state_hotlines": state_entries, "state": state}


def checklist_for(risk_status):
    if risk_status in ("DANGER", "WARNING", "ALERT"):
        phases = ["during", "bag"]
    else:
        phases = ["before", "bag"]
    items = []
    for ph in phases:
        for it in CHECKLIST.get(ph, []):
            items.append(dict(it, phase=ph))
    return items


def source_note():
    return "Hotlines & checklist from data/EMERGENCY.md (verified 23 Aug 2026 from official .gov.my sources)."


if __name__ == "__main__":
    import json
    print(json.dumps(hotlines_for("Selangor"), ensure_ascii=False, indent=2))
    print("---")
    print(json.dumps(checklist_for("ALERT"), ensure_ascii=False, indent=2))
