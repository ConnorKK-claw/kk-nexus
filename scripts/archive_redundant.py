#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive_redundant.py - Archive auto-distilled knowledge nodes that have case coverage.

Scans knowledge/ for non-X0 auto-distilled nodes with stock codes,
checks if cases/ has a corresponding company case file, and if so,
marks the node as status: archived with a reason and timestamp.
"""

import argparse, re, sys
from datetime import datetime
from pathlib import Path

STOCK_CODE_RE = re.compile(r"(\d{6})")

FRAGMENT_KEYWORDS = [
    "法律意见书", "律师意见",
    "自查报告",
    "通知债权人", "催告",
    "回购注销实施公告",
    "核查意见",
    "公示情况说明", "公示情况",
]


def resolve_vault(vault_arg):
    if vault_arg:
        return Path(vault_arg).resolve()
    hv = Path.home() / ".codex" / "skills" / "equity-incentive" / "vault"
    if hv.is_dir():
        return hv
    return hv


def extract_frontmatter(filepath: Path):
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in content[3:end].strip().splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [x.strip().strip(chr(34)).strip(chr(39)) for x in v[1:-1].split(",") if x.strip()]
        else:
            fm[k] = v.strip(chr(34)).strip(chr(39))
    return fm


def has_case_coverage(vault, filename: str):
    cases_dir = vault / "cases"
    if not cases_dir.is_dir():
        return None
    code_match = STOCK_CODE_RE.search(filename)
    stock_code = code_match.group(1) if code_match else None
    company_name = None
    if stock_code:
        m = re.search(rf"{stock_code}-[a-z]{{2}}-(.+?)-", filename)
        if m:
            company_name = m.group(1)
    if not stock_code and not company_name:
        return None
    for case_file in sorted(cases_dir.glob("*.md")):
        cn = case_file.stem
        if stock_code and stock_code in cn:
            return case_file.name
        if company_name and company_name in cn:
            return case_file.name
    return None


def is_non_x0(filename: str) -> bool:
    return bool(re.match(r"^zk-[a-z]+-[a-z]+\d\d+-\d+-", filename))


def main():
    parser = argparse.ArgumentParser(description="Archive redundant knowledge nodes")
    parser.add_argument("vault", nargs="?", help="Vault path (default: auto-detect)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview only")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    knowledge_dir = vault / "knowledge"
    if not knowledge_dir.is_dir():
        print(f"[ERR] knowledge/ not found in {vault}")
        sys.exit(1)

    candidates = []
    for f in sorted(knowledge_dir.glob("*.md")):
        if f.name == "index.md":
            continue
        fm = extract_frontmatter(f)
        if not fm:
            continue
        if fm.get("status") == "archived":
            continue
        if not is_non_x0(f.name):
            continue  # Skip curated X0 nodes
        code_match = STOCK_CODE_RE.search(f.name)
        if not code_match:
            continue
        search_text = f.name + " " + fm.get("title", "")
        if not any(kw in search_text for kw in FRAGMENT_KEYWORDS):
            continue
        case_file = has_case_coverage(vault, f.name)
        if case_file:
            candidates.append((f, case_file))

    if not candidates:
        print(f"[archive] No redundant nodes found in {knowledge_dir}")
        return

    print(f"[archive] {len(candidates)} candidate(s) for archival:")
    for f, cf in candidates:
        print(f"  {f.name[:60]} -> cases/{cf}")

    if args.dry_run:
        print("\n[DRY-RUN] No files modified")
        return

    now_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    archived = 0
    for f, case_file in candidates:
        try:
            content = f.read_text(encoding="utf-8")
            if re.search(r"^status:", content, re.M):
                content = re.sub(r"^status:.*$", "status: archived", content, flags=re.M)
            end = content.find("---", 3)
            if end != -1:
                note = f"\narchived_reason: 已整合到 cases/{case_file}" + f"\narchived_at: {now_ts}"
                content = content[:end] + note + content[end:]
            f.write_text(content, encoding="utf-8")
            print(f"  [ARCHIVED] {f.name}")
            archived += 1
        except Exception as e:
            print(f"  [ERR] {f.name}: {e}")

    idx_script = Path(__file__).parent / "build_index.py"
    if idx_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(idx_script), str(vault)])

    print(f"\n[archive] Done: {archived} archived")


if __name__ == "__main__":
    sys.exit(main())
