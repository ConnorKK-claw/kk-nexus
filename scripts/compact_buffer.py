#!/usr/bin/env python3
"""compact_buffer.py - Compress working-buffer to memory/."""
import argparse, re, sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUFFER = PROJECT_ROOT / "memory" / "working-buffer.md"
SESSION_STATE = PROJECT_ROOT / "SESSION-STATE.md"
MEMORY_DIR = PROJECT_ROOT / "memory"
THRESHOLD = 50
KEEP = 25
NL = chr(10)

def parse_session_state(text: str):
    meta = {"last_session": "", "session_count": 0, "compact_count": 0, "last_compact": "", "vaults_active": []}
    for line in text.split(NL):
        line = line.strip()
        m = re.match(r"^- (\w[\w_]+):\s*(.+)", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if key == "compact_count":
                try: meta["compact_count"] = int(val.split()[0])
                except ValueError: pass
            elif key == "vaults_active":
                meta["vaults_active"] = [i.strip().strip("'").strip('"') for i in val.strip("[]").split(",") if i.strip()]
            else:
                meta[key] = val
    return meta

def update_compact_count(text: str, new_count: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    old = "- compact_count:"
    if old in text:
        idx = text.index(old)
        end = text.find(NL, idx)
        text = text[:idx] + f"- compact_count: {new_count}" + text[end:]
    else:
        marker = "## Context Notes"
        if marker in text:
            text = text.replace(marker, marker + NL + f"- compact_count: {new_count}")
        else:
            text += NL + "## Context Notes" + NL + f"- compact_count: {new_count}" + NL
    old2 = "- last_compact:"
    if old2 in text:
        idx = text.index(old2)
        end = text.find(NL, idx)
        text = text[:idx] + f"- last_compact: {today}" + text[end:]
    else:
        text += f"- last_compact: {today}" + NL
    return text

def count_pending(text: str) -> int:
    count = 0
    in_p = False
    for line in text.split(NL):
        if "### Pending" in line: in_p = True
        elif "### Completed" in line or line.startswith("## "): in_p = False
        elif in_p and line.strip().startswith("- ["): count += 1
    return count

def main():
    p = argparse.ArgumentParser(description="Compress working-buffer")
    p.add_argument("--dry-run", "-n", action="store_true")
    args = p.parse_args()
    if not BUFFER.exists():
        print(f"[compact] No working-buffer")
        return 0
    lines = BUFFER.read_text(encoding="utf-8").split(NL)
    total = len(lines)
    print(f"[compact] working-buffer: {total} lines (threshold: {THRESHOLD})")
    if total <= THRESHOLD:
        print(f"[compact] Skipped (under threshold)")
        return 0
    move_count = total - KEEP
    print(f"[compact] Moving {move_count} lines, keeping {KEEP}")
    if args.dry_run:
        print(f"[dry-run] Would archive {move_count} lines")
        return 0
    move_lines = lines[:move_count]
    keep_lines = lines[move_count:]
    today = datetime.now().strftime("%Y-%m-%d")
    mem_file = MEMORY_DIR / f"{today}.md"
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H:%M:%S")
    archive = NL + f"### [compact] working-buffer - {ts}" + NL + NL + NL.join(move_lines) + NL
    if mem_file.exists():
        existing = mem_file.read_text(encoding="utf-8")
        mem_file.write_text(existing + archive, encoding="utf-8")
    else:
        mem_file.write_text(f"# {today}" + NL + archive, encoding="utf-8")
    BUFFER.write_text(NL.join(keep_lines), encoding="utf-8")
    if SESSION_STATE.exists():
        ss_text = SESSION_STATE.read_text(encoding="utf-8")
        meta = parse_session_state(ss_text)
        new_count = meta.get("compact_count", 0) + 1
        ss_text = update_compact_count(ss_text, new_count)
        SESSION_STATE.write_text(ss_text, encoding="utf-8")
        print(f"[compact] compact_count -> {new_count}")
    print(f"[compact] Done: {move_count} lines archived")
    return 0

if __name__ == "__main__":
    sys.exit(main())
