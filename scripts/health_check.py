"""
health_check.py — vault 知识健康检查

用法:
    python health_check.py <vault-path>
    python health_check.py <vault-path> --raw-days 14 --knowledge-months 6
    python health_check.py <vault-path> --auto-expire

检查项:
  - raw/ 下超过 N 天未蒸馏的文件（提示蒸馏）
  - knowledge/ 下超过 M 个月未更新的节点（提示可能过期）
  - knowledge/ 下同 tag 多节点（潜在重复）
  - 可选 --auto-expire: 自动标记过期节点 status: expired
"""

import argparse
import sys
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


# Fragment keyword constants (kept in sync with auto_distill_vault.py)
FRAGMENT_KEYWORDS = [
    "法律意见书", "律师意见",
    "自查报告",
    "通知债权人", "催告",
    "回购注销实施公告",
    "核查意见",
    "公示情况说明", "公示情况",
]

STOCK_CODE_RE = re.compile(r"(\d{6})")


def extract_frontmatter(filepath: Path) -> dict | None:
    """提取 YAML frontmatter。"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    if content.startswith("\ufeff"):
        content = content[1:]
    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    fm_text = content[3:end].strip()
    if not fm_text:
        return None

    fm = {}
    list_key = None
    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if list_key:
                fm.setdefault(list_key, []).append(stripped[2:].strip())
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                fm[key] = [v.strip().strip('\"').strip("'") for v in inner.split(",") if v.strip()]
                list_key = None
            else:
                cleaned = val.strip('\"').strip("'")
                if cleaned == "":
                    # 空值可能是后续列表项的容器，初始化为列表
                    fm[key] = []
                    list_key = key
                else:
                    fm[key] = cleaned
                    list_key = None
    return fm


def check_fragment_announcements(vault_dir: Path) -> list[str]:
    d = vault_dir / "knowledge"
    if not d.is_dir(): return []
    issues = []
    for f in sorted(d.glob("*.md")):
        if f.name in (".gitkeep", "index.md"): continue
        fm = extract_frontmatter(f)
        if not fm: continue
        if fm.get("status") == "archived": continue
        search_text = f.name + " " + fm.get("title", "")
        has_code = STOCK_CODE_RE.search(f.name)
        if not has_code: continue
        is_frag = any(kw in search_text for kw in FRAGMENT_KEYWORDS)
        if not is_frag: continue
        cases_dir = vault_dir / "cases"
        if not cases_dir.is_dir(): continue
        code = has_code.group(1)
        m = re.search(rf"{code}-[a-z]{{2}}-(.+?)-", f.name)
        co_name = m.group(1) if m else None
        has_case = any(code in cf.stem or (co_name and co_name in cf.stem) for cf in sorted(cases_dir.glob("*.md")))
        if has_case:
            rel = str(f.relative_to(vault_dir)).replace(chr(92), chr(47))
            issues.append(f"{rel} -> 已有案例覆盖，建议运行 archive_redundant.py 归档")
    return issues


def check_raw_stale(vault_dir: Path, days: int) -> list[str]:
    """检查 raw/ 下超期未蒸馏文件。"""
    issues = []
    cutoff = datetime.now() - timedelta(days=days)

    for src_dir in ["raw/user", "raw/agent"]:
        d = vault_dir / src_dir
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.md")):
            if f.name == ".gitkeep":
                continue
            fm = extract_frontmatter(f)
            if not fm:
                continue
            if fm.get("status") != "raw":
                continue
            try:
                file_date = datetime.strptime(fm.get("date", "2000-01-01"), "%Y-%m-%d")
            except ValueError:
                continue
            if file_date < cutoff:
                age = (datetime.now() - file_date).days
                rel = str(f.relative_to(vault_dir)).replace(chr(92), chr(47))
                issues.append(f"{rel} — {age} 天未蒸馏")

    return issues


def check_knowledge_stale(vault_dir: Path, months: int) -> list[str]:
    """检查 knowledge/ 下长期未更新节点。"""
    issues = []
    cutoff = datetime.now() - timedelta(days=months * 30)
    d = vault_dir / "knowledge"
    if not d.is_dir():
        return issues

    for f in sorted(d.glob("*.md")):
        if f.name in (".gitkeep", "index.md"):
            continue
        fm = extract_frontmatter(f)
        if not fm:
            continue
        if fm.get("status") in ("expired", "verified"):
            continue
        # 显式标记 expirable: false 的节点跳过过期检测（如法规原文等静态参考）
        expirable = fm.get("expirable", True)
        if isinstance(expirable, str):
            expirable = expirable.lower() not in ("false", "no", "0")
        if not expirable:
            continue
        try:
            file_date = datetime.strptime(fm.get("date", "2000-01-01"), "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            age_months = (datetime.now() - file_date).days // 30
            rel = str(f.relative_to(vault_dir)).replace(chr(92), chr(47))
            issues.append(f"{rel} — {age_months} 个月未更新（状态: {fm.get('status', '?')}）")

    return issues


def check_duplicate_tags(vault_dir: Path) -> list[str]:
    """检测 knowledge/ 下同 tag 多节点（潜在重复）。"""
    d = vault_dir / "knowledge"
    if not d.is_dir():
        return []

    tag_groups = defaultdict(list)
    for f in sorted(d.glob("*.md")):
        if f.name in (".gitkeep", "index.md"):
            continue
        fm = extract_frontmatter(f)
        if not fm:
            continue
        rel = str(f.relative_to(vault_dir)).replace(chr(92), chr(47))
        for tag in fm.get("tags", []):
            tag_groups[tag].append(rel)

    issues = []
    for tag, paths in sorted(tag_groups.items()):
        if len(paths) > 1:
            issues.append(f"标签 [{tag}] 下 {len(paths)} 个节点: {', '.join(paths)}")
    return issues


def auto_expire(vault_dir: Path, months: int) -> int:
    """自动标记过期节点。"""
    cutoff = datetime.now() - timedelta(days=months * 30)
    d = vault_dir / "knowledge"
    if not d.is_dir():
        return 0

    count = 0
    for f in sorted(d.glob("*.md")):
        if f.name in (".gitkeep", "index.md"):
            continue
        fm = extract_frontmatter(f)
        if not fm:
            continue
        if fm.get("status") == "expired":
            continue
        try:
            file_date = datetime.strptime(fm.get("date", "2000-01-01"), "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            content = f.read_text(encoding="utf-8")
            content = content.replace("status: distilled", "status: expired")
            content = content.replace("status: verified", "status: expired")
            content = content.replace("status: raw", "status: expired")
            f.write_text(content, encoding="utf-8")
            rel = str(f.relative_to(vault_dir)).replace(chr(92), chr(47))
            print(f"  [EXPIRED] {rel}")
            count += 1

    return count


def _run_weekly_mode():
    """Run weekly deep health checks: BOM, duplicate URLs, encoding, coverage."""
    import os
    from pathlib import Path
    from collections import defaultdict

    codex_skills = Path.home() / ".codex" / "skills"
    vaults_to_check = []
    if codex_skills.exists():
        for skill_dir in sorted(codex_skills.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            vault_raw = skill_dir / "vault" / "raw" / "user"
            if vault_raw.exists():
                vaults_to_check.append((skill_dir.name, vault_raw))

    if not vaults_to_check:
        print("[weekly] No vault raw/user/ directories found.")
        return 0

    total_issues = 0
    for vault_name, vault_path in vaults_to_check:
        print(f"\n=== {vault_name} ===")
        files = sorted([f for f in vault_path.iterdir() if f.suffix == ".md"])
        if not files:
            print("  (no .md files)")
            continue

        # Double BOM
        bom_bad = []
        for f in files:
            raw = f.read_bytes()[:6]
            if raw[:6] == b"\xef\xbb\xbf\xef\xbb\xbf":
                bom_bad.append(f.name)
        if bom_bad:
            total_issues += 1
            print(f"  ISSUE: {len(bom_bad)} double-BOM files")
        else:
            print("  OK: No double BOM")

        # Duplicate URLs
        url_map = defaultdict(list)
        for f in files:
            content_md = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^url[\uff1a:]\s*(https?://\S+)", content_md, re.MULTILINE)
            if m:
                url_map[m.group(1)].append(f.name)
        dupes = {u: fs for u, fs in url_map.items() if len(fs) > 1}
        if dupes:
            total_issues += 1
            print(f"  ISSUE: {len(dupes)} duplicate URL(s)")
        else:
            print("  OK: No duplicate URLs")

        # Encoding
        enc_bad = []
        for f in files:
            raw = f.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                enc_bad.append(f.name)
        if enc_bad:
            total_issues += 1
            print(f"  ISSUE: {len(enc_bad)} encoding errors")
        else:
            print("  OK: Encoding clean")

        print(f"  Files: {len(files)}")

    print(f"\n[weekly] Total issues across {len(vaults_to_check)} vaults: {total_issues}")
    return total_issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="vault 健康检查")
    parser.add_argument("vault_path", type=Path, nargs="?", default=None, help="Vault 目录路径 (optional for --mode weekly)")
    parser.add_argument("--raw-days", type=int, default=14, help="raw 未蒸馏告警阈值（天）")
    parser.add_argument("--knowledge-months", type=int, default=6, help="knowledge 过期阈值（月）")
    parser.add_argument("--mode", choices=["quick","weekly"], default="quick",
                        help="quick: standard vault health; weekly: deep cross-vault scan")
    parser.add_argument("--auto-expire", action="store_true", help="自动标记过期节点")
    args = parser.parse_args()

    if args.mode == 'weekly':
        issues = _run_weekly_mode()
        sys.exit(0 if issues == 0 else 1)


    vault_dir = args.vault_path.resolve()
    if not vault_dir.is_dir():
        print(f"[错误] vault 目录不存在: {vault_dir}")
        sys.exit(1)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"健康检查: {vault_dir.name}")
    print(f"时间: {now}")
    print(f"参数: raw 未蒸馏 > {args.raw_days} 天, knowledge 过期 > {args.knowledge_months} 个月")
    print()

    # 1. Raw 未蒸馏
    stale_raw = check_raw_stale(vault_dir, args.raw_days)
    if stale_raw:
        print(f"[WARN] {len(stale_raw)} 个 raw 文件超期未蒸馏:")
        for s in stale_raw:
            print(f"  - {s}")
        print()
    else:
        print("[OK] raw 文件均在蒸馏窗口内")
        print()

    # 2. Knowledge 过期
    stale_knowledge = check_knowledge_stale(vault_dir, args.knowledge_months)
    if stale_knowledge:
        print(f"[WARN] {len(stale_knowledge)} 个 knowledge 节点长期未更新:")
        for s in stale_knowledge:
            print(f"  - {s}")
        print()
    else:
        print("[OK] knowledge 节点均在有效期内")
        print()

    # 3. 公告碎片检测
    ad = check_fragment_announcements(vault_dir)
    if ad:
        print(f"[INFO] {len(ad)} 个公告碎片建议归档")
        for s in ad:
            print(f"  - {s}")
        print()
    else:
        print("[OK] 无公告碎片节点")
        print()

    # 4. 重复标签
    dup_tags = check_duplicate_tags(vault_dir)
    if dup_tags:
        print(f"[INFO] {len(dup_tags)} 个标签下有多个节点:")
        for s in dup_tags:
            print(f"  - {s}")
        print()
    else:
        print("[OK] 无标签重复")
        print()

    # 4. Auto-expire
    if args.auto_expire:
        print("自动标记过期...")
        n = auto_expire(vault_dir, args.knowledge_months)
        print(f"已标记 {n} 个过期节点")
        if n > 0:
            print("建议运行 build_index.py 重建索引")

    total = len(stale_raw) + len(stale_knowledge) + len(ad) + len(dup_tags)
    print(f"\n总提醒: {total} 项")
    if total > 0:
        sys.exit(1)

# === --mode weekly (merged from weekly_vault_health.py) ===