#!/usr/bin/env python3
"""auto_heartbeat.py - Full HEARTBEAT protocol for Super KAM.

Performs:
1. Run health_check.py --mode weekly (import as module or subprocess)
2. Check .learnings/ ERRORS.md for new entries (within 7 days)
3. Run consolidate_learnings.py to sync .learnings/ to vault journal
4. Check memory/maintenance: scan memory/ for files, report count
5. Check WAL: verify working-buffer.md and SESSION-STATE.md are recent
6. Output comprehensive report to logs/heartbeat_YYYY-MM-DD.md
7. Auto-distill raw vault files if pending
8. If any WARN/ERR found, also write a journal entry to vault/journal/YYYY-MM-DD.md
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS = PROJECT_ROOT / "logs"
LOGS.mkdir(exist_ok=True)
# VAULT_PATH: 请替换为你的 vault 路径，例如：# VAULT_PATH = Path.home() / ".codex" / "skills" / "my-skill" / "vault"

def run_health() -> str:
    """Run health_check.py --mode weekly and capture its output."""
    health_script = PROJECT_ROOT / "scripts" / "health_check.py"
    if not health_script.exists():
        return "[ERR] health_check.py not found"
    try:
        r = subprocess.run(
            [sys.executable, str(health_script), "--mode", "weekly"],
            capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace"
        )
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "[ERR] health_check.py timed out (>120s)"
    except Exception as e:
        return f"[ERR] health_check.py error: {e}"


def run_bridge_learnings() -> str:
    """Run consolidate_learnings.py to sync .learnings/ to MEMORY.md."""
    script = PROJECT_ROOT / "scripts" / "consolidate_learnings.py"
    if not script.exists():
        return "[ERR] consolidate_learnings.py not found"
    try:
        r = subprocess.run(
            [sys.executable, str(script), "--all-vaults"],
            capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace"
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"[ERR] consolidate_learnings error: {e}"


def check_errors_md() -> dict:
    """Check .learnings/ ERRORS.md for new entries within 7 days."""
    errors_path = PROJECT_ROOT / ".learnings" / "ERRORS.md"
    if not errors_path.exists():
        return {"status": "OK", "message": "No ERRORS.md"}
    content = errors_path.read_text(encoding="utf-8", errors="replace")
    now_ts = datetime.now().timestamp()
    recent = []
    for line in content.splitlines():
        line = line.strip()
        for word in line.split():
            word = word.strip("#-:()")
            try:
                dt = datetime.strptime(word, "%Y-%m-%d")
                age_days = (now_ts - dt.replace(tzinfo=None).timestamp()) / 86400
                if 0 <= age_days <= 7:
                    recent.append(line.strip())
                    break
            except ValueError:
                continue
    age_days = (now_ts - errors_path.stat().st_mtime) / 86400
    if age_days > 7 and not recent:
        return {"status": "OK", "message": "ERRORS.md has no new entries in last 7d"}
    if recent:
        return {"status": "INFO", "message": f"{len(recent)} recent entries in ERRORS.md", "detail": recent[:5]}
    return {"status": "OK", "message": "ERRORS.md modified recently but no dated entries found"}


def check_memory() -> dict:
    """Scan memory/ for files, report count."""
    memory_dir = PROJECT_ROOT / "memory"
    if not memory_dir.is_dir():
        return {"status": "OK", "message": "No memory/ directory", "count": 0}
    files = sorted(memory_dir.glob("*.md"))
    if not files:
        return {"status": "INFO", "message": "memory/ exists but empty", "count": 0}
    return {"status": "OK", "message": f"{len(files)} memory files", "count": len(files), "files": [f.name for f in files]}


def check_wal() -> dict:
    """Verify working-buffer.md and SESSION-STATE.md are recent."""
    now_ts = datetime.now().timestamp()
    targets = [
        ("SESSION-STATE.md", PROJECT_ROOT / "SESSION-STATE.md"),
        ("memory/working-buffer.md", PROJECT_ROOT / "memory" / "working-buffer.md"),
    ]
    entries = []
    all_ok = True
    for label, path in targets:
        if not path.exists():
            entries.append(f"[{label}] MISSING")
            all_ok = False
            continue
        age_days = (now_ts - path.stat().st_mtime) / 86400
        age_str = f"{age_days:.1f}d"
        if age_days > 7:
            entries.append(f"[{label}] STALE ({age_str})")
            all_ok = False
        else:
            entries.append(f"[{label}] OK ({age_str})")
    message = "; ".join(entries)
    return {"status": "OK" if all_ok else "WARN", "message": message}


def write_journal_entry(content_lines: list[str]):
    if not VAULT_PATH.exists():
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    journal_dir = VAULT_PATH / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)
    jp = journal_dir / f"{today}.md"
    ts = datetime.now().strftime("%H:%M:%S")
    text = ""
    for line in content_lines:
        text += f"- {ts} | auto_heartbeat | {line}" + chr(10)
    if jp.exists():
        jp.write_text(jp.read_text(encoding="utf-8") + text, encoding="utf-8")
    else:
        header = (
            f"---" + chr(10) +
            f"date: {today}" + chr(10) +
            f"source: agent" + chr(10) +
            f"domain: equity-incentive" + chr(10) +
            f"tags: [heartbeat]" + chr(10) +
            f"status: raw" + chr(10) +
            f"---" + chr(10) + chr(10) +
            f"# {today}" + chr(10) + chr(10) + text
        )
        jp.write_text(header, encoding="utf-8")
    return True


def main():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[auto_heartbeat] Starting HEARTBEAT protocol at {now_str}")
    report = [
        f"# Heartbeat Report - {today}",
        "",
        f"Generated: {now_str}",
        "",
    ]

    has_issues = False

    # Step 1: Run health check
    print("  [1/8] Running auto_health...")
    health_output = run_health()
    health_ok = "[ERR]" not in health_output[:20] if health_output else False
    report.append("## 1. Health Check")
    report.append("")
    report.append(f"- Status: {'OK' if health_ok else 'ERR'}")
    if len(health_output) > 1000:
        report.append(f"- Output:" + chr(10) + "`" + chr(10) + f"{health_output[:1000]}" + chr(10) + "`")
    else:
        report.append(f"- Output: {health_output}")
    report.append("")
    if not health_ok or "[WARN]" in health_output or "[ERR]" in health_output:
        has_issues = True

    # Step 2: Check learnings errors
    print("  [2/8] Checking .learnings/ERRORS.md...")
    err_check = check_errors_md()
    report.append("## 2. Learnings Errors")
    report.append("")
    report.append(f"- [{err_check['status']}] {err_check['message']}")
    if err_check.get("detail"):
        for d in err_check["detail"]:
            report.append(f"  - {d}")
    report.append("")
    if err_check["status"] in ("WARN", "ERR"):
        has_issues = True

    # Step 3: Run bridge_learnings
    print("  [3/8] Running bridge_learnings...")
    bridge_output = run_bridge_learnings()
    report.append("## 3. Bridge Learnings")
    report.append("")
    if "[ERR]" in bridge_output:
        report.append(f"- [WARN] {bridge_output}")
        has_issues = True
    else:
        report.append(f"- {bridge_output}")
    report.append("")

    # Step 4: Check memory
    print("  [4/8] Checking memory/...")
    mem_check = check_memory()
    report.append("## 4. Memory Status")
    report.append("")
    report.append(f"- [{mem_check['status']}] {mem_check['message']}")
    if mem_check.get("files"):
        for fn in mem_check["files"]:
            report.append(f"  - {fn}")
    report.append("")

        # Step 4.5: Check raw pending and trigger distill-vault
    print("  [4.5/8] Checking raw pending...")
    raw_dirs = [
        VAULT_PATH / "raw" / "user",
        VAULT_PATH / "raw" / "agent",
    ]
    raw_count = 0
    for rd in raw_dirs:
        if rd.is_dir():
            for f in rd.glob("*.md"):
                if f.name == ".gitkeep":
                    continue
                try:
                    c = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                if "status: raw" in c:
                    raw_count += 1
    report.append("## 4.5 Raw Pending")
    report.append("")
    if raw_count > 0:
        report.append(f"- [WARN] {raw_count} raw files pending distillation")
        print(f"    {raw_count} raw pending, triggering distill-vault...")
        import subprocess, sys
        script = PROJECT_ROOT / "scripts" / "auto_distill_vault.py"
        if script.exists():
            r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
            output = (r.stdout + r.stderr).strip()
            report.append(f"- Distill result: {output[:300]}")
            has_issues = True
        else:
            report.append("- [ERR] auto_distill_vault.py not found")
    else:
        report.append(f"- [OK] No raw files pending")
    report.append("")

# Step 4.75: Check working-buffer
    print("  [4.75/8] Checking working-buffer...")
    buf_file = PROJECT_ROOT / "memory" / "working-buffer.md"
    if buf_file.exists():
        buf_lines = buf_file.read_text(encoding="utf-8").split(chr(10))
        buf_total = len(buf_lines)
        report.append("## 4.75 Working Buffer")
        report.append("")
        if buf_total > 50:
            report.append(f"- [WARN] working-buffer: {buf_total} lines (>50 threshold)")
            import subprocess, sys
            script = PROJECT_ROOT / "scripts" / "compact_buffer.py"
            if script.exists():
                r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
                report.append(f"- Compaction: {(r.stdout + r.stderr)[:100]}")
                has_issues = True
        else:
            report.append(f"- [OK] working-buffer: {buf_total} lines")
    else:
        report.append("- [OK] No working-buffer")
    report.append("")

# Step 5: Check WAL
    print("  [5/8] Checking WAL...")
    wal_check = check_wal()
    report.append("## 6. WAL Integrity")
    report.append("")
    report.append(f"- [{wal_check['status']}] {wal_check['message']}")
    report.append("")
    if wal_check["status"] == "WARN":
        has_issues = True

    # Step 6: Summary
    print("  [6/8] Compiling summary...")
    report.append("## 7. Summary")
    report.append("")
    report.append(f"- Issues found: {'YES' if has_issues else 'NO'}")
    report.append("")

    # Step 7: Journal entry if issues found
    print("  [7/8] Writing journal entry (if issues)...")
    if has_issues:
        journal_entries = []
        for line in report:
            if line.startswith("-"):
                journal_entries.append(line.lstrip("- "))
        written = write_journal_entry([f"Heartbeat detected issues: {len(journal_entries)} items"])
        report.append("## 8. Journal")
        report.append("")
        if written:
            report.append(f"- Journal entry written to vault/journal/{today}.md")
        else:
            report.append("- WARN: Could not write journal (vault path not found)")
        report.append("")

    report.append("---")
    report.append("")
    report.append("_End of Heartbeat Report_")

    report_file = LOGS / f"heartbeat_{today}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(chr(10).join(report))
    print(f"  [LOG] {report_file}")
    print(f"[auto_heartbeat] Done (issues: {has_issues})")
    return 0 if not has_issues else 1


if __name__ == "__main__":
    sys.exit(main())

