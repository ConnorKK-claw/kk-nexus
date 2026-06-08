"""
build_index.py — 扫描 vault 知识文件，生成 knowledge/index.md

用法:
    python build_index.py <vault-path>
    python build_index.py <vault-path> --dry-run

扫描 vault/knowledge/ vault/cases/ vault/templates/ 下的 .md 文件，
提取 YAML frontmatter，生成按 domain → tag → status 分组的索引。
agent 检索时优先读 index.md（O(1)），未命中才降级文件搜索。
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def extract_frontmatter(filepath: Path) -> dict | None:
    """从 Markdown 文件提取 YAML frontmatter，返回 dict 或 None。
    只认开头 --- 闭合的 YAML 块，简单解析 key: value 和 key: [list]。
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [警告] 读取失败 {filepath}: {e}")
        return None

    # Strip BOM if present (PowerShell UTF8 adds ﻿)
    if content.startswith("﻿"):
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
    # 简单 YAML 解析：key: value 或 key: [item, item]
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
                fm[key] = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
                list_key = None
            else:
                if val == "":
                    fm[key] = []
                    list_key = key
                else:
                    fm[key] = val.strip('"').strip("'")
                    list_key = None
    return fm


def find_md_files(vault_dir: Path) -> dict[str, list[Path]]:
    """扫描 knowledge/ cases/ templates/ 三个目录，返回 {dir_name: [paths]}。"""
    result = {}
    for sub in ["knowledge", "cases", "templates"]:
        d = vault_dir / sub
        if d.is_dir():
            files = sorted(f for f in d.glob("*.md") if f.name != "index.md")
            if files:
                result[sub] = files
    return result


def find_issues(entries: list[dict]) -> list[str]:
    """检测潜在问题：同 tag 多节点、缺少字段、过期未标记。"""
    issues = []
    tag_groups = defaultdict(list)
    no_domain = []
    no_status = []

    for e in entries:
        if not e.get("domain"):
            no_domain.append(e["path"])
        if not e.get("status"):
            no_status.append(e["path"])
        if e.get("status") == "archived":
            continue
        for tag in e.get("tags", []):
            tag_groups[tag].append(e["path"])

    if no_domain:
        issues.append(f"⚠ 缺少 domain 字段: {len(no_domain)} 个文件")
        for p in no_domain[:5]:
            issues.append(f"    - {p}")

    if no_status:
        issues.append(f"⚠ 缺少 status 字段: {len(no_status)} 个文件")
        for p in no_status[:5]:
            issues.append(f"    - {p}")

    for tag, paths in tag_groups.items():
        if len(paths) > 1:
            issues.append(f"🔍 同标签 [{tag}] 下 {len(paths)} 个节点（可能重复/相关）")


    # === 交叉覆盖检测：gg0 ↔ bb0/aa0 ===
    # 硬编码映射表：同一主题有多个近似节点时提醒优先引用精化版本
    cross_map = [
        (["gg0-13-pricing", "bb0-1-定价"], "定价规则: gg0-13 为通用型，bb0-1 为精化实操版，建议优先引用 bb0"),
        (["gg0-1-performance", "gg0-23-soe-performance"], "业绩指标: gg0-1 通用 vs gg0-23 国资专项，按场景选择"),
        (["gg0-0-incentive-tool", "gg0-3-equity-incentive-design"], "工具选择与方案设计: gg0-0 详述工具，gg0-3 覆盖全流程设计"),
        (["gg0-4-approval", "gg0-17-soe-declaration"], "审批流程: gg0-4 通用 vs gg0-17 国资专项，按场景选择"),
        (["gg0-8-equity-incentive-tax", "gg0-33-tax-and-accounting"], "税务处理: gg0-8 聚焦个税，gg0-33 覆盖税会差异，建议综合引用"),
    ]
    for patterns, msg in cross_map:
        matched = [e["path"] for e in entries if any(p in e["path"] for p in patterns)]
        if len(matched) >= 2:
            issues.append(f"🔍 交叉覆盖: {msg}")
            for p in matched:
                issues.append(f"    - {p}")
    return issues


def build_index(vault_dir: Path, dry_run: bool = False) -> str:
    """构建 index.md 内容，返回字符串。"""
    vault_dir = vault_dir.resolve()
    if not vault_dir.is_dir():
        print(f"[错误] vault 目录不存在: {vault_dir}")
        sys.exit(1)

    file_map = find_md_files(vault_dir)
    all_entries = []

    # 收集所有条目
    for section, files in file_map.items():
        for f in files:
            fm = extract_frontmatter(f)
            rel_path = str(f.relative_to(vault_dir)).replace("\\", "/")
            entry = {
                "path": rel_path,
                "title": fm.get("title", f.stem) if fm else f.stem,
                "date": fm.get("date", "—") if fm else "—",
                "domain": fm.get("domain", "") if fm else "",
                "tags": fm.get("tags", []) if fm else [],
                "status": fm.get("status", "unknown") if fm else "unknown",
                "section": section,
            }
            all_entries.append(entry)

    # 按 domain → status → section 分组
    domain_groups = defaultdict(list)
    for e in all_entries:
        domain_groups[e["domain"] or "(未分类)"].append(e)

    # 构建 Markdown
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# Vault 知识索引")
    lines.append("")
    lines.append(f"> 自动生成于 {now}")
    lines.append(f"> 总条目: {len(all_entries)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for domain in sorted(domain_groups.keys()):
        entries = domain_groups[domain]
        lines.append(f"## {domain}（{len(entries)}）")
        lines.append("")

        # 按 status 分组
        status_groups = defaultdict(list)
        for e in entries:
            status_groups[e["status"]].append(e)

        for status in ["verified", "distilled", "raw", "expired", "archived", "unknown"]:
            if status not in status_groups:
                continue
            lines.append(f"### {status}")
            lines.append("")
            lines.append("| 文件 | 标题 | 日期 | 标签 |")
            lines.append("|------|------|------|------|")
            for e in sorted(status_groups[status], key=lambda x: x["date"], reverse=True):
                tags_str = ", ".join(e["tags"][:3])
                if len(e["tags"]) > 3:
                    tags_str += f" +{len(e['tags']) - 3}"
                lines.append(f"| [{e['path']}]({e['path']}) | {e['title']} | {e['date']} | {tags_str} |")
            lines.append("")

    # 添加问题报告
    issues = find_issues(all_entries)
    if issues:
        lines.append("---")
        lines.append("")
        lines.append("## 潜在问题")
        lines.append("")
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("")

    # 添加检索提示
    lines.append("---")
    lines.append("")
    lines.append("## 检索提示")
    lines.append("")
    lines.append("- 本索引覆盖 `knowledge/` `cases/` `templates/` 三个目录")
    lines.append("- 索引未命中时，使用 `Select-String -Path <vault> -Pattern \"关键词\" -Recurse` 全文搜索")
    lines.append("- 添加或修改知识节点后，运行 `python build_index.py <vault-path>` 重建本索引")
    lines.append("")

    content = "\n".join(lines)

    if dry_run:
        print(content)
        return content

    index_path = vault_dir / "knowledge" / "index.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(content, encoding="utf-8")
    print(f"[OK] 索引已生成: {index_path}")
    print(f"  总条目: {len(all_entries)}")
    if issues:
        print(f"  潜在问题: {len(issues)} 项（详见 index.md 底部）")
    return content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 vault 知识索引")
    parser.add_argument("vault_path", type=Path, help="Vault 目录路径")
    parser.add_argument("--dry-run", action="store_true", help="预览输出，不写入文件")
    args = parser.parse_args()
    build_index(args.vault_path, dry_run=args.dry_run)

