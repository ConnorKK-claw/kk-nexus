#!/usr/bin/env python3
"""log_skill_call.py - Append skill call log to engineering-practices vault journal."""
import argparse, sys
from pathlib import Path
from datetime import datetime

VAULT_JOURNAL = Path.home() / ".codex" / "skills" / "engineering-practices" / "vault" / "journal"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--skill", required=True)
    p.add_argument("--context", required=True)
    p.add_argument("--trigger", default="user_request", choices=["user_request","session_auto","scheduled_task"])
    p.add_argument("--outcome", default="success", choices=["success","partial","failure"])
    p.add_argument("--artifact", action="append", default=[])
    p.add_argument("--decision", action="append", default=[])
    p.add_argument("--lesson", action="append", default=[])
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lines = [f"- skill: {args.skill}", f"  trigger: {args.trigger}", f"  timestamp: {ts}", f"  context: {args.context}"]
    if args.decision:
        lines.append("  key_decisions:")
        lines += [f'    - "{d}"' for d in args.decision]
    lines.append(f"  outcome: {args.outcome}")
    if args.artifact:
        lines.append("  artifacts:")
        lines += [f'    - "{a}"' for a in args.artifact]
    if args.lesson:
        lines.append("  lessons:")
        lines += [f'    - "{l}"' for l in args.lesson]
    entry = "\n".join(lines)

    if args.dry_run:
        print("=== DRY RUN ===\n" + entry)
        return

    VAULT_JOURNAL.mkdir(parents=True, exist_ok=True)
    logfile = VAULT_JOURNAL / f"{today}.md"
    if not logfile.exists():
        logfile.write_text(f"---\ntitle: Skill Execution Log\ndate: {today}\nsource: agent\ndomain: engineering-practices\ntags: [log, journal]\nstatus: raw\nimported_by: log_skill_call.py\n---\n\n# Skill Execution Log - {today}\n\n", encoding="utf-8")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write("\n" + entry + "\n")
    print(f"[OK] Logged: {args.skill} ({args.outcome}) -> {logfile}")

if __name__ == "__main__":
    main()
