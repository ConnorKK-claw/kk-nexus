"""Generate author and institution index for financial-analysis vault."""

import argparse
import re
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def extract_frontmatter(filepath: Path) -> dict | None:
    """Extract YAML frontmatter from Markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None
    fm = m.group(1)
    meta = {}
    
    title_m = re.search(chr(39) + r"^title:\s*" + chr(34) + r"([^" + chr(34) + r"]*)" + chr(34), fm, re.MULTILINE)
    if title_m:
        meta["title"] = title_m.group(1)
    elif re.search(r"^title:\s*(.+)", fm, re.MULTILINE):
        meta["title"] = re.search(r"^title:\s*(.+)", fm, re.MULTILINE).group(1).strip()
    
    author_m = re.search(chr(39) + r"^author:\s*" + chr(34) + r"([^" + chr(34) + r"]*)" + chr(34), fm, re.MULTILINE)
    if author_m:
        raw = author_m.group(1)
        meta["authors"] = [a.strip() for a in re.split(r"[、,]", raw) if a.strip()]
    elif re.search(r"^author:\s*(.+)", fm, re.MULTILINE):
        raw = re.search(r"^author:\s*(.+)", fm, re.MULTILINE).group(1).strip()
        meta["authors"] = [a.strip() for a in re.split(r"[、,]", raw) if a.strip()]
    
    inst_m = re.search(r"^institution:\s*(.+)", fm, re.MULTILINE)
    if inst_m:
        meta["institution"] = inst_m.group(1).strip().strip(chr(34)).strip(chr(39))
    
    date_m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", fm, re.MULTILINE)
    if date_m:
        meta["date"] = date_m.group(1)
    
    tags_m = re.search(r"^tags:\s*\[([^\]]*)\]", fm, re.MULTILINE)
    if tags_m:
        meta["tags"] = tags_m.group(1)
    
    source_m = re.search(r"^source:\s*(.+)", fm, re.MULTILINE)
    if source_m:
        meta["source"] = source_m.group(1).strip()
    return meta


def build_authors_index(vault_path: Path, dry_run: bool = False):
    """Scan vault, generate author and institution index."""
    raw_dir = vault_path / "raw" / "user"
    knowledge_dir = vault_path / "knowledge"
    
    author_articles = defaultdict(list)
    author_knowledge = defaultdict(list)
    inst_articles = defaultdict(list)
    
    total_raw = 0
    total_knowledge = 0
    
    if raw_dir.exists():
        for f in sorted(raw_dir.glob("*.md")):
            if f.name == ".gitkeep":
                continue
            meta = extract_frontmatter(f)
            if not meta:
                continue
            total_raw += 1
            rel_path = f"raw/user/{f.name}"
            title = meta.get("title", f.stem)
            date = meta.get("date", "")
            tags = meta.get("tags", "")
            source = meta.get("source", "")
            if meta.get("authors"):
                for author in meta["authors"]:
                    author_articles[author].append((rel_path, title, date, tags, source))
            if meta.get("institution"):
                inst_articles[meta["institution"]].append((rel_path, title, date, meta.get("authors", [""])[0]))
    
    if knowledge_dir.exists():
        for f in sorted(knowledge_dir.glob("zk-*.md")):
            meta = extract_frontmatter(f)
            if not meta:
                continue
            total_knowledge += 1
            rel_path = f"knowledge/{f.name}"
            title = meta.get("title", f.stem)
            date = meta.get("date", "")
            tags = meta.get("tags", "")
            if meta.get("institution"):
                inst_articles[meta["institution"]].append((rel_path, title, date, meta.get("authors", [""])[0]))
            if meta.get("authors"):
                for author in meta["authors"]:
                    author_knowledge[author].append((rel_path, title, date, tags))
    
    # Build output
    output_parts = []
    output_parts.append("# 005 financial-analysis 作者索引")
    output_parts.append("")
    output_parts.append("> 生成于 " + datetime.now().strftime("%Y-%m-%d %H:%M") + " | ")
    output_parts.append("共 " + str(len(author_articles)) + " 位作者，" + str(total_raw) + " 篇原文，" + str(total_knowledge) + " 个知识节点")
    output_parts.append("")
    output_parts.append("---")
    output_parts.append("")
    
    all_authors = sorted(set(list(author_articles.keys()) + list(author_knowledge.keys())))
    for author in all_authors:
        articles = author_articles.get(author, [])
        knowledge = author_knowledge.get(author, [])
        total = len(articles) + len(knowledge)
        if total == 0:
            continue
        output_parts.append("## " + author)
        output_parts.append("")
        output_parts.append("共 " + str(total) + " 篇")
        output_parts.append("")
        if articles:
            for rel_path, title, date, tags, source in articles:
                date_str = " - " + date if date else ""
                tags_str = " [" + tags + "]" if tags else ""
                output_parts.append("- [" + title + "](" + rel_path + ")" + date_str + tags_str)
        if knowledge:
            for rel_path, title, date, tags in knowledge:
                date_str = " - " + date if date else ""
                tags_str = " [" + tags + "]" if tags else ""
                output_parts.append("- [" + title + " (知识节点)](" + rel_path + ")" + date_str + tags_str)
        output_parts.append("")
    
    # Institution index
    output_parts.append("## 机构索引")
    output_parts.append("")
    all_insts = sorted(inst_articles.keys())
    for inst in all_insts:
        articles = sorted(inst_articles[inst], key=lambda x: x[2] or "")
        output_parts.append("### " + inst + " (" + str(len(articles)) + " 篇)")
        output_parts.append("")
        for rel_path, title, date, author in articles:
            author_str = " (" + author + ")" if author else ""
            output_parts.append("- [" + title + "](" + rel_path + ")" + author_str + " - " + date)
        output_parts.append("")
    output_parts.append("")
    output_parts.append("---")
    output_parts.append("  共 " + str(len(all_insts)) + " 家机构，" + str(sum(len(inst_articles[i]) for i in all_insts)) + " 篇")
    output_parts.append("")
    
    output = chr(10).join(output_parts)
    out_path = vault_path / "knowledge" / "authors-index.md"
    
    if dry_run:
        print("[DRY-RUN] 将写入 " + str(out_path))
        print("         " + str(len(all_authors)) + " 位作者")
        print("         " + str(total_raw) + " 篇原文, " + str(total_knowledge) + " 个知识节点")
    else:
        out_path.write_text(output, encoding="utf-8")
        print("已写入 " + str(out_path))
        print("  " + str(len(all_authors)) + " 位作者, " + str(total_raw) + " 篇原文, " + str(total_knowledge) + " 个知识节点")


def main():
    parser = argparse.ArgumentParser(description="生成作者索引")
    parser.add_argument("vault_path", type=Path, help="vault 目录路径")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    args = parser.parse_args()
    build_authors_index(args.vault_path.resolve(), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
