# -*- coding: utf-8 -*-
"""005 financial-analysis domain distillation."""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

CATSEQ_LABELS = {
    "hh0": "作者观点",
    "ii0": "经济指标",
    "jj0": "政策预判",
    "kk0": "资产配置",
    "ll0": "事件影响",
}

KNOWN_AUTHORS = [
    "陶川", "林彦", "邵翔",
    "钟渝梅", "武朔", "陈艺鑫",
    "段萌", "李思琪", "张云杰",
    "裴明楠", "finn",
]

CLASS_RULES = [
    ("ii0", ["pmi","cpi","ppi","非农","通胀","进出口","外贸","工企利润",
              "gdp","经济数据","m2","社融","信贷","工业","消费","投资",
              "pce","物价","就业","失业","零售"]),
    ("jj0", ["政治局会议","中央经济工作","四中全会","十五五",
              "政府工作报告","两会","国常会","国务院","国新办",
              "政策","改革","规划","人大","政协","建议稿"]),
    ("kk0", ["黄金","美元","美债","a股","港股","美股","汇率","人民币",
              "国债","利率","降息","加息","资产配置","配置","金价",
              "石油","原油","商品","大宗","房价","地产","房地产"]),
    ("ll0", ["关税","贸易战","贸易谈判","中东","伊朗","地缘","制裁",
              "停摆","政府关门","选举","大选","换届","谈判","摩擦",
              "战争","冲突","避险"]),
]

INSTITUTIONS = [
    ("高盛", "Goldman Sachs"),
    ("摩根士丹利", "Morgan Stanley"),
    ("摩根大通", "JP Morgan"),
    ("瑞银", "UBS"),
    ("花旗", "Citi"),
]

DEFAULT_CATSEQ = "hh0"

def parse_filename(fn: str):
    m = re.match(r"\[(\d{4})(\d{2})(\d{2})\d{4}\](.+)\.[a-z]+$", fn)
    if not m:
        return None, None, None
    year, month, day = m.group(1), m.group(2), m.group(3)
    date = f"{year}-{month}-{day}"
    rest = m.group(4)
    author = ""
    for a in KNOWN_AUTHORS:
        if rest.endswith(a):
            author = a
            break
    return date, rest, author


def classify(title: str, content: str) -> str:
    text = (title + " " + content[:500]).lower()
    for catseq, keywords in CLASS_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return catseq
    return DEFAULT_CATSEQ


def extract_author_from_body(content: str) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    if k.strip().lower() == "author":
                        return v.strip().strip(chr(34)).strip(chr(39))
    return ""


def detect_institution(title: str, content: str) -> str:
    text = title + " " + content[:600]
    for cn, en in INSTITUTIONS:
        if cn in text:
            return cn
    return ""


def detect_source(content: str) -> str:
    """Detect the 公众号 source from file content."""
    head = content[:1500].lower()
    if "finn" in head or "原创  finn" in head or "finn的投研记录" in head:
        return "finn的投研记录"
    return "川阅全球宏观"


def slugify(text: str) -> str:
    """Convert text to URL-safe slug, preserving CJK characters."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    slug = text[:60].strip("-")
    if not slug:
        slug = "article"
    return slug


def next_seq(vault: Path, catseq: str) -> int:
    knowledge_dir = vault / "knowledge"
    if not knowledge_dir.is_dir():
        return 0
    pattern = re.compile(rf"^zk-fa-{re.escape(catseq)}-(\d+)-.+\.md$")
    max_seq = -1
    for f in knowledge_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            seq = int(m.group(1))
            if seq > max_seq:
                max_seq = seq
    return max_seq + 1


def read_frontmatter(content: str):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta = {}
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip(chr(34)).strip(chr(39))
            return meta, parts[2].strip()
    return {}, content.strip()


def summarize_content(content: str, max_chars: int = 500) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
        else:
            body = content
    else:
        body = content
    body = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    body = re.sub(r"\[.*?\]\(.*?\)", "", body)
    body = re.sub(r"#+", "", body)
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith(">")]
    summary = " ".join(lines)[:max_chars]
    return summary

def build_knowledge_node(vault: Path, fn: str, date: str, title: str, author: str, catseq: str, summary: str, institution: str = "", source: str = "川阅全球宏观"):
    seq = next_seq(vault, catseq)
    label = CATSEQ_LABELS.get(catseq, catseq)
    slug = slugify(title[:40])
    zk_id = f"zk-fa-{catseq}-{seq}-{slug}"
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    inst_tag = f", 机构-{institution}" if institution else ""
    tags_list = [f"公众号", source]
    if author and author != "未知":
        tags_list.append(author)
    tags_list.append(label)
    if inst_tag:
        tags_list.append(f"机构-{institution}")
    tags_str = ", ".join(tags_list)

    content = f"""---
title: {title}
date: {date}
source: distilled
original_source: user
distilled_from: raw/user/{fn}
domain: financial-analysis
author: {author}
institution: {institution}
category: {label}
tags: [{tags_str}]
status: verified
imported_by: distill_fa.py
imported_at: {now}
---

# {title}

> 作者: {author} | 发表日期: {date}
> 分类: {label}

## 核心观点

{summary}

## 原文

`[[{fn}]]`

## 标签

- 作者: {author}
- 机构: {institution}
- 分类: {label}
- 日期: {date}
"""

    out_path = vault / "knowledge" / (zk_id + ".md")
    return out_path, content


def mark_raw_distilled(raw_path: Path):
    content = raw_path.read_text(encoding="utf-8", errors="replace")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            body = parts[2]
            if re.search(r"^status:", fm, re.M):
                fm = re.sub(r"^status:.*$", "status: distilled", fm, flags=re.M)
            else:
                fm += "\nstatus: distilled\n"
            content = "---" + fm + "---" + body
            raw_path.write_text(content, encoding="utf-8")
            return True
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    nl = chr(10)
    fm = f"date: {now[:10]}{nl}source: user{nl}status: distilled{nl}imported_by: distill_fa.py{nl}imported_at: {now}{nl}"
    content = f"---{nl}{fm}---{nl}" + content
    raw_path.write_text(content, encoding="utf-8")
    return True


import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    parser = argparse.ArgumentParser(description="005 financial-analysis domain distillation")
    parser.add_argument("--vault", type=Path, required=True, help="vault directory path")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    parser.add_argument("--limit", type=int, default=0, help="Max articles to process (0=all)")
    args = parser.parse_args()

    vault = args.vault.resolve()
    raw_dir = vault / "raw" / "user"
    knowledge_dir = vault / "knowledge"

    if not raw_dir.is_dir():
        print(f"[ERROR] raw/user/ not found: {raw_dir}")
        return 1

    raw_files = []
    for f in sorted(raw_dir.glob("*.md")):
        if f.name == ".gitkeep":
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        meta, _ = read_frontmatter(content)
        if meta.get("status", "raw") == "raw":
            raw_files.append((f, content))

    if not raw_files:
        print(f"[OK] No raw files to distill in {vault}")
        return 0

    print(f"Found {len(raw_files)} files to distill", flush=True)

    if args.limit > 0:
        raw_files = raw_files[:args.limit]
        print(f"  (limit={args.limit})", flush=True)

    stats = {}
    created = 0
    skipped = 0

    for f, content in raw_files:
        date, title, author = parse_filename(f.name)
        if not title:
            title = f.stem
            date = ""
        if not author:
            author = extract_author_from_body(content)
        if not author:
            author = "未知"
        catseq = classify(title, content)
        stats[catseq] = stats.get(catseq, 0) + 1
        summary = summarize_content(content)
        inst = detect_institution(title, content)
        source = detect_source(content)
        out_path, node_content = build_knowledge_node(vault, f.name, date or "unknown", title, author, catseq, summary, inst, source)

        if args.dry_run:
            print(f"  [DRY] {f.name[:50]:50s} -> {catseq}/{out_path.name[:55]}", flush=True)
        else:
            if out_path.exists():
                print(f"  [SKIP] {out_path.name} already exists", flush=True)
                skipped += 1
                continue
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_text(node_content, encoding="utf-8")
            mark_raw_distilled(f)
            print(f"  [OK] {f.name[:50]:50s} -> {catseq}/{out_path.name[:55]},{inst}", flush=True)
            created += 1

    print(flush=True)
    print(f"Done: {created} created, {skipped} skipped", flush=True)
    print(flush=True)
    print("Classification breakdown:", flush=True)
    for cat, cnt in sorted(stats.items()):
        if cnt > 0:
            print(f"  {cat} ({CATSEQ_LABELS.get(cat, '')}): {cnt}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
