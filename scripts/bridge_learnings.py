"""DEPRECATED — 请使用 consolidate_learnings.py 替代。
保留仅用于参考，不再维护。
"""

#!/usr/bin/env python3
"""bridge_learnings.py - Bridge .learnings/ entries into KAM vault journals."""
import argparse, hashlib, json, re, sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = PROJECT_ROOT / ".bridged_cache.json"
VAULTS = [
    # Path.home() / ".codex" / "skills" / "my-skill" / "vault",
    Path.home() / ".codex" / "skills" / "another-domain" / "vault",
]

def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"bridged": {}, "skipped": {}}

def save_cache(cache: dict):
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

def entry_id(title: str, date_str: str) -> str:
    return hashlib.md5(f"{date_str}-{title}".encode("utf-8")).hexdigest()[:12]

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        return path.read_text(encoding="utf-8")

def parse_learnings(path: Path) -> list:
    if not path.exists(): return []
    text = read_file(path)
    entries = []
    for block in re.split(r"(?=^## \[\d{4}-\d{2}-\d{2}\])", text, flags=re.M):
        block = block.strip()
        if not block or "## [" not in block: continue
        m = re.match(r"^## \[(\d{4}-\d{2}-\d{2})\]\s+(.+)", block, re.M)
        if not m: continue
        date_str, title = m.group(1), m.group(2).strip()
        types = []
        if "**Corrections:**" in block: types.append("correction")
        if "**Insights:**" in block: types.append("insight")
        if "**Best Practices:**" in block: types.append("best_practice")
        entries.append({"source": "LEARNINGS.md", "date": date_str, "title": title, "types": types, "body": block, "eid": entry_id(title, date_str)})
    return entries

def parse_errors(path: Path) -> list:
    if not path.exists(): return []
    text = read_file(path)
    entries = []
    for block in re.split(r"(?=^## \[)", text, flags=re.M):
        block = block.strip()
        if not block or "## [" not in block: continue
        m = re.match(r"^## \[(.+?)\]\s+(.+)", block, re.M)
        if not m: continue
        topic, title = m.group(1).strip(), m.group(2).strip()
        entries.append({"source": "ERRORS.md", "date": datetime.now().strftime("%Y-%m-%d"), "title": f"{topic}: {title}", "types": ["error"], "body": block, "eid": entry_id(f"ERR-{topic}", datetime.now().strftime("%Y-%m-%d"))})
    return entries

def write_journal(vault: Path, entry: dict, dry_run: bool) -> bool:
    date_str, jfile = entry["date"], vault / "journal" / f"{entry['date']}.md"
    header = chr(10).join(["---", f"date: {date_str}", "source: agent", "domain: equity-incentive", "tags: [learning-bridge]", "status: raw", "---", "", f"# {date_str}", ""])
    body = f"- [learning] [{chr(47).join(entry['types'])}] {entry['title']}"
    for line in entry["body"].split(chr(10)):
        s = line.strip()
        if s.startswith("- **"):
            body += chr(10) + f"  {s}"
    body += chr(10) + f"  source: .learnings/{entry['source']}"
    body += chr(10) + f"  eid: {entry['eid']}"
    body += chr(10)
    if dry_run: return True
    (vault / "journal").mkdir(parents=True, exist_ok=True)
    if jfile.exists():
        if entry["eid"] in jfile.read_text(encoding="utf-8"): return False
        jfile.write_text(jfile.read_text(encoding="utf-8") + body, encoding="utf-8")
        return True
    jfile.write_text(header + chr(10) + body, encoding="utf-8")
    return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", "-n", action="store_true")
    p.add_argument("--suggest", action="store_true")
    args = p.parse_args()
    ae = parse_learnings(PROJECT_ROOT / ".learnings" / "LEARNINGS.md")
    ae += parse_errors(PROJECT_ROOT / ".learnings" / "ERRORS.md")
    if not ae: print("[bridge] No entries"); return 0
    cache = load_cache()
    new = [e for e in ae if e["eid"] not in cache.get("bridged", {})]
    if not new: print(f"[bridge] All {len(ae)} already bridged"); return 0
    print(f"[bridge] {len(new)} new:")
    for e in new:
        print(f"  [{chr(47).join(e['types'])}] {e['title']} ({e['date']})")
    if args.suggest:
        print()
        for e in new:
            if "correction" in e["types"]: print(f"  \u25b6 Consider knowledge: {e['title']}")
            if "error" in e["types"]: print(f"  \u25b6 For TOOLS.md: {e['title']}")
    if args.dry_run: print("[dry-run]"); return 0
    for e in new:
        w = any(write_journal(v, e, False) for v in VAULTS if v.exists())
        if w:
            cache.setdefault("bridged", {})[e["eid"]] = {"title": e["title"], "date": e["date"], "bridged_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
    save_cache(cache)
    print(f"[bridge] Done")
    return 0

if __name__ == "__main__":
    sys.exit(main())
