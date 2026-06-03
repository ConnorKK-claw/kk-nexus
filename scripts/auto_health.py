"""auto_health.py - automated vault health check."""
import subprocess, sys, os, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"

# All vaults discovered dynamically from UNIFIED_INDEX.md
VAULTS = {}
import re as _re
_idx = PROJECT_ROOT / "UNIFIED_INDEX.md"
if _idx.exists():
    _txt = _idx.read_text("utf-8")
    for _m in _re.finditer(r"(?m)^\r?- \*\*Path\*\*: `(.+?)`", _txt):
        _p = Path(_m.group(1))
        _name = _p.parent.name
        if _name == "vault":
            _name = _p.parent.parent.name
        if _p.exists():
            VAULTS[_name] = _p

def run_health(name, vpath):
    script = SCRIPTS / "health_check.py"
    cmd = [sys.executable, str(script), str(vpath), "--knowledge-months", "12", "--raw-days", "14"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        out = r.stdout + r.stderr
    except Exception as e:
        out = str(e)
    warnings = 0
    for line in out.split("\n"):
        if "[WARN]" in line or "[ERR]" in line:
            warnings += 1
    return {"status": "OK", "warnings": warnings} if warnings == 0 else {"status": "WARN", "warnings": warnings}

def count_raw_files(vault_path):
    count = 0
    for subdir in ["raw/user", "raw/agent"]:
        dp = vault_path / subdir
        if dp.exists():
            for f in dp.glob("*.md"):
                try:
                    txt = f.read_text("utf-8", errors="replace")
                    if "status: raw" in txt:
                        count += 1
                except:
                    pass
    return count

def check_raw_pending(vault_path, name):
    count = count_raw_files(vault_path)
    if count == 0:
        return {"status": "OK", "message": f"{name}: 0 raw files pending"}
    elif count <= 20:
        return {"status": "OK", "message": f"{name}: {count} raw files pending"}
    else:
        return {"status": "WARN", "message": f"{name}: {count} raw files pending (>20)"}

def check_tag_consistency(vault_path):
    return {"status": "SKIP", "message": "Skipped"}

def check_index_freshness():
    path = PROJECT_ROOT / "UNIFIED_INDEX.md"
    if not path.exists():
        return {"status": "ERR", "message": "UNIFIED_INDEX.md does not exist"}
    age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(path.stat().st_mtime)).total_seconds()
    hours = age / 3600
    if hours > 24:
        return {"status": "WARN", "message": f"UNIFIED_INDEX.md is {hours:.1f}h old (>24h)"}
    return {"status": "OK", "message": f"UNIFIED_INDEX.md is {hours:.1f}h old (<24h)"}


def check_txtai_health():
    """Check txtai index health via txtai_health.py"""
    script = SCRIPTS / "txtai_health.py"
    if not script.exists():
        return {"status": "SKIP", "message": "txtai_health.py not found"}
    try:
        r = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        out = r.stdout + r.stderr
        if "[ERROR]" in out or "[ERR]" in out:
            return {"status": "ERR", "message": "txtai index error"}
        elif "[WARN]" in out:
            return {"status": "WARN", "message": "txtai index warnings"}
        return {"status": "OK", "message": "txtai index healthy"}
    except subprocess.TimeoutExpired:
        return {"status": "WARN", "message": "txtai health check timeout"}
    except Exception as e:
        return {"status": "WARN", "message": f"txtai check error: {e}"}
def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report = []
    report.append(f"# Auto Health Check - {now.split()[0]}")
    report.append(f"Time: {now}")
    report.append("")
    report.append("## Vault Health")
    for name, vpath in sorted(VAULTS.items()):
        result = run_health(name, vpath)
        report.append(f"- [{result['status']}] {name}: {result['warnings']} warnings")
    report.append("")
    report.append("## Index Freshness")
    idx_result = check_index_freshness()
    report.append(f"- [{idx_result['status']}] {idx_result['message']}")
    report.append("")
    report.append("## txtai Health
    txtai_result = check_txtai_health()
    report.append(f"- [{txtai_result['status']}] {txtai_result['message']}")
    report.append("")
## Raw Pending Count")
    for name, vpath in sorted(VAULTS.items()):
        result = check_raw_pending(vpath, name)
        report.append(f"- [{result['status']}] {result['message']}")
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"health_{now.split()[0]}.md"
    log_file.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"[auto_health] {now}")
    for line in report:
        if line.startswith("- ["):
            print(f"  {line}")
    print(f"  [LOG] {log_file}")
    print("[auto_health] Done")

if __name__ == "__main__":
    main()
