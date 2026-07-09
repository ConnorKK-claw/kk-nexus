#!/usr/bin/env python3
"""consolidate_learnings.py - Incrementally merge LEARNINGS.md into MEMORY.md"""
import re, sys
from pathlib import Path
from datetime import datetime

PROJ = Path(__file__).resolve().parent.parent
LEARN = PROJ / ".learnings" / "LEARNINGS.md"
MEM = PROJ / "MEMORY.md"
TRACK = PROJ / ".learnings" / ".consolidated_until"

# Employee vault paths (for --all-vaults)
VAULTS = [
    ("001", Path.home() / ".codex" / "skills" / "my-domain" / "vault"),
    ("002", Path.home() / ".codex" / "skills" / "another-domain" / "vault"),
    ("003", Path.home() / ".codex" / "skills" / "wr-domain" / "vault"),
    ("004", Path.home() / ".codex" / "skills" / "hk-domain" / "vault"),
    ("005", Path.home() / ".codex" / "skills" / "fa-domain" / "vault"),
    ("006", Path.home() / ".codex" / "skills" / "asr-domain" / "vault"),
    ("007", Path.home() / ".codex" / "skills" / "ta2-domain" / "vault"),
]

LEARN_FNAME = "LEARNINGS.md"
ERROR_FNAME = "ERRORS.md"
FEATURE_FNAME = "FEATURE_REQUESTS.md"
DATE_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\]")
SUB_RE = re.compile(r"^\*\*(Corrections|Insights|Best Practices):\*\*$")
ITEM_RE = re.compile(r"^\d+\.\s+(.+)")

def parse_learnings():
    if not LEARN.exists():
        print(f"[ERROR] {LEARN} not found"); sys.exit(1)
    c = LEARN.read_text(encoding="utf-8")
    if c.startswith("﻿"): c = c[1:]  # strip BOM
    sections, cur, cur_sub = [], None, None
    for line in c.splitlines():
        m = DATE_RE.match(line)
        if m:
            if cur: sections.append(cur)
            cur = {"date": m.group(1), "title": line[line.index("]")+2:].strip(),
                   "corrections": [], "insights": [], "best_practices": []}
            cur_sub = None; continue
        m = SUB_RE.match(line)
        if m:
            cur_sub = m.group(1).lower().replace(" ", "_"); continue
        m = ITEM_RE.match(line)
        if m and cur and cur_sub:
            cur[cur_sub].append(m.group(1).strip())
    if cur: sections.append(cur)
    return sections

def scan_vault_learnings(vaults):
    """Scan all employee vaults for .learnings/ files."""
    all_sections = []
    for num, vpath in vaults:
        lpath = vpath / ".learnings" / LEARN_FNAME
        if not lpath.exists():
            continue
        try:
            c = lpath.read_text(encoding="utf-8")
            if c.startswith("\ufeff"): c = c[1:]
            sections, cur, cur_sub = [], None, None
            for line in c.splitlines():
                m = DATE_RE.match(line)
                if m:
                    if cur: sections.append(cur)
                    cur = {"date": m.group(1), "title": f"[{num}] " + line[line.index("]")+2:].strip(),
                           "corrections": [], "insights": [], "best_practices": []}
                    cur_sub = None; continue
                m = SUB_RE.match(line)
                if m:
                    cur_sub = m.group(1).lower().replace(" ", "_"); continue
                m = ITEM_RE.match(line)
                if m and cur and cur_sub:
                    cur[cur_sub].append(m.group(1).strip())
            if cur: sections.append(cur)
            print(f"    [{num}] {len(sections)} sections from {lpath}")
            all_sections.extend(sections)
        except Exception as e:
            print(f"    [{num}] ERROR reading {lpath}: {e}")
    return all_sections

def get_track():
    return TRACK.read_text(encoding="utf-8").strip() if TRACK.exists() else None

def write_track(d):
    TRACK.parent.mkdir(parents=True, exist_ok=True)
    TRACK.write_text(d, encoding="utf-8")

def format_entries(sections):
    kk, ll, seen = [], [], set()
    for s in sections:
        tag = "[from " + s["date"] + "]"
        if s["corrections"]:
            kk.append("### Corrections - " + s["title"] + " " + tag)
            for i, item in enumerate(s["corrections"], 1):
                kk.append("- **#" + str(i) + ":** " + item)
        if s["insights"]:
            kk.append("### Insights - " + s["title"] + " " + tag)
            for item in s["insights"]:
                kk.append("- " + item)
        if s["best_practices"]:
            for item in s["best_practices"]:
                key = item[:60]
                if key not in seen:
                    seen.add(key)
                    ll.append("- " + item + " " + tag)
    return kk, ll

def build_traps():
    return [
        "### Known Traps - High-Frequency Errors [consolidated 2026-05-23]",
        "",
        "#### 1. PowerShell-Python String Escaping",
        "- Symptom: python -c inline fails; long text truncated",
        "- Root: two shells with different quoting rules",
        "- Rule: always write multi-line Python to .py file first",
        "",
        "#### 2. Script Path Confusion",
        "- bootstrap_vault.py -> skill dir",
        "- enhance_skillmd.py -> skill dir",
        "- build_index.py -> vault dir",
        "- validate_vault.py -> skill dir",
        "- vault_ingest.py -> vault dir (--vault)",
        "",
        "#### 3. Silent Write Failure",
        "- Set-Content may fail without error",
        "- Rule: Test-Path after every write; prefer Python write_text()",
        "",
        "#### 4. SKILL.md Injection Integrity",
        "- Rule: verify marker exists and is not duplicated after injection",
    ]

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--all-vaults", action="store_true",
                   help="Scan all 7 employee vaults for .learnings/ and consolidate into MEMORY.md")
    args = p.parse_args()

    if args.all_vaults:
        print("[INFO] Scanning all employee vaults...")
        sections = scan_vault_learnings(VAULTS)
    else:
        sections = parse_learnings()
    print("[INFO] Parsed " + str(len(sections)) + " date sections")

    last = get_track()
    if last and not args.force:
        new = [s for s in sections if s["date"] > last]
        print("[INFO] Skipped " + str(len(sections)-len(new)) + " already processed (up to " + last + ")")
        sections = new
    else:
        print("[INFO] " + ("Force: processing all" if args.force else "First run: processing all"))

    if not sections:
        print("[OK] Nothing new"); return

    latest = max(s["date"] for s in sections)
    print("[INFO] Processing " + str(len(sections)) + " sections, latest=" + latest)
    kk, ll = format_entries(sections)
    first_run = last is None

    if args.dry_run:
        print("\n=== DRY RUN ===")
        print("Key Knowledge: " + str(len(kk)) + " lines")
        for line in kk[:8]: print("  " + line[:120])
        if first_run:
            traps = build_traps()
            print("Known Traps: " + str(len(traps)) + " lines")
        print("Lessons Learned: " + str(len(ll)) + " lines")
        for line in ll[:5]: print("  " + line[:120])
        print("Would write .consolidated_until = " + latest)
        return

    mem = MEM.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")
    mem = re.sub(r"> Last updated: \d{4}-\d{2}-\d{2}", "> Last updated: " + today, mem)

    kk_block = []
    if first_run:
        kk_block.append(""); kk_block.extend(build_traps()); kk_block.append("")
    if kk:
        kk_block.append("### Consolidated from session corrections")
        kk_block.extend(kk); kk_block.append("")

    ll_block = []
    if ll:
        ll_block.append(""); ll_block.extend(ll); ll_block.append("")

    if not kk_block and not ll_block:
        print("[OK] Nothing to append"); return

    if kk_block:
        pos = mem.find("\n---\n", mem.find("## Key Knowledge"))
        if pos != -1:
            mem = mem[:pos] + "\n" + "\n".join(kk_block) + "\n" + mem[pos:]
            print("[INFO] Inserted " + str(len(kk_block)) + " lines into ## Key Knowledge")

    if ll_block:
        pos = mem.find("\n---\n", mem.find("## Lessons Learned"))
        if pos != -1:
            mem = mem[:pos] + "\n" + "\n".join(ll_block) + "\n" + mem[pos:]
            print("[INFO] Inserted " + str(len(ll_block)) + " lines into ## Lessons Learned")

    MEM.write_text(mem, encoding="utf-8")
    print("[OK] MEMORY.md updated")
    write_track(latest)
    print("[OK] .consolidated_until = " + latest)

if __name__ == "__main__":
    main()
