import argparse, json, re, subprocess, sys
from datetime import datetime
from pathlib import Path

def find_vault_root(start: Path) -> Path:
    return start if (start / "vault").is_dir() else find_vault_root(start.parent)

def load_json(path: Path) -> dict:
    if path.exists() and path.stat().st_size > 0:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {}

def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def next_zk_id(vault: Path, domain: str, catseq: str) -> int:
    knowledge_dir = vault / "knowledge"
    if not knowledge_dir.is_dir(): return 0
    pattern = re.compile(rf"^zk-{re.escape(domain)}-{re.escape(catseq)}-(\d+)-.+\.md$")
    max_seq = -1
    for f in knowledge_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            seq = int(m.group(1))
            if seq > max_seq: max_seq = seq
    return max_seq + 1

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = text.strip("-_")
    return text[:60]

def parse_frontmatter(content: str) -> tuple:
    content = content.strip()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            meta = {}
            for line in fm_text.split(chr(10)):
                line = line.strip()
                if chr(58) in line:
                    key, _, val = line.partition(chr(58))
                    key = key.strip()
                    val = val.strip()
                    if val.startswith(chr(91)) and val.endswith(chr(93)):
                        items = val[1:-1].split(chr(44))
                        cleaned = []
                        for v in items:
                            v = v.strip()
                            v = v.strip(chr(34)).strip(chr(39))
                            if v: cleaned.append(v)
                        meta[key] = cleaned
                    else:
                        meta[key] = val.strip(chr(34)).strip(chr(39))
            return meta, body
    return {}, content

def build_kam_fm(title, date_str, tags, wiki_relpath, domain):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(tags, list): tag_str = chr(44).join(tags)
    else: tag_str = str(tags)
    parts = []
    parts.append("---")
    parts.append("title: " + title)
    parts.append("date: " + date_str)
    parts.append("source: distilled")
    parts.append("original_source: wiki")
    parts.append("distilled_from: _wiki_ingest/" + wiki_relpath)
    parts.append("domain: " + domain)
    parts.append("tags: [" + tag_str + ", wiki-ingest]")
    parts.append("status: distilled")
    parts.append("imported_by: wiki_to_kam.py")
    parts.append("imported_at: " + now)
    parts.append("---")
    return chr(10).join(parts) + chr(10)

def parse_time_ns(time_str: str) -> int:
    try:
        dt = datetime.fromisoformat(time_str)
        return int(dt.timestamp() * 1_000_000_000)
    except Exception:
        return 0

def distill_entity(vault, wiki_root, file, distilled, domain):
    rel = file.relative_to(wiki_root).as_posix()
    dt = distilled.get("distilled_pages",{}).get(rel)
    if dt and file.stat().st_mtime_ns <= parse_time_ns(dt): return None
    content = file.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    title = meta.get("title", file.stem)
    date_str = meta.get("created", datetime.now().strftime("%Y-%m-%d"))
    tags = meta.get("tags", [])
    if isinstance(tags, str): tags = [tags]
    seq = next_zk_id(vault, domain, "gg0")
    slug = slugify(title)
    zk_fn = f"zk-{domain}-gg0-{seq}-{slug}.md"
    kam_path = vault / "knowledge" / zk_fn
    fm = build_kam_fm(title, date_str, tags, rel, domain)
    kam_path.write_text(fm + body, encoding="utf-8")
    return rel, str(kam_path.relative_to(vault.parent).as_posix())

def distill_source(vault, wiki_root, file, distilled, domain):
    rel = file.relative_to(wiki_root).as_posix()
    dt = distilled.get("distilled_pages",{}).get(rel)
    if dt and file.stat().st_mtime_ns <= parse_time_ns(dt): return None
    content = file.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    title = meta.get("title", file.stem)
    date_str = meta.get("created", datetime.now().strftime("%Y-%m-%d"))
    tags = meta.get("tags", [])
    if isinstance(tags, str): tags = [tags]
    slug = slugify(title)
    raw_fn = f"{date_str}-{slug}-wiki.md"
    kam_path = vault / "raw" / "agent" / raw_fn
    fm = build_kam_fm(title, date_str, tags, rel, domain)
    kam_path.write_text(fm + body, encoding="utf-8")
    return rel, str(kam_path.relative_to(vault.parent).as_posix())

def distill_comparison(vault, wiki_root, file, distilled, domain):
    rel = file.relative_to(wiki_root).as_posix()
    dt = distilled.get("distilled_pages",{}).get(rel)
    if dt and file.stat().st_mtime_ns <= parse_time_ns(dt): return None
    content = file.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    title = meta.get("title", file.stem)
    date_str = meta.get("created", datetime.now().strftime("%Y-%m-%d"))
    tags = meta.get("tags", [])
    if isinstance(tags, str): tags = [tags]
    slug = slugify(title)
    case_fn = f"{date_str}-{slug}-comparison-case.md"
    kam_path = vault / "cases" / case_fn
    fm = build_kam_fm(title, date_str, tags + ["\u6bd4\u8f83\u6848\u4f8b"], rel, domain)
    kam_path.write_text(fm + body, encoding="utf-8")
    return rel, str(kam_path.relative_to(vault.parent).as_posix())

def distill_synthesis(vault, wiki_root, file, distilled, domain):
    content = file.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(content)
    title = meta.get("title", file.stem)
    if "\u6bd4\u8f83" in title or "\u8c03\u7814" in title:
        return distill_comparison(vault, wiki_root, file, distilled, domain)
    else:
        return distill_entity(vault, wiki_root, file, distilled, domain)

def append_journal(vault, entries):
    today = datetime.now().strftime("%Y-%m-%d")
    jp = vault / "journal" / f"{today}.md"
    ts = datetime.now().strftime("%H:%M:%S")
    lines2 = []
    for e in entries:
        lines2.append(f"- {ts} | wiki_to_kam.py | {e}")
    text = chr(10).join(lines2) + chr(10)
    if jp.exists():
        jp.write_text(jp.read_text(encoding="utf-8") + text, encoding="utf-8")
    else:
        hdr = f"---{chr(10)}date: {today}{chr(10)}source: agent{chr(10)}domain: equity-incentive{chr(10)}tags: [wiki-ingest]{chr(10)}status: raw{chr(10)}---{chr(10)}{chr(10)}# {today}{chr(10)}{chr(10)}{text}"
        jp.write_text(hdr, encoding="utf-8")

def run_build_index(vault):
    script = vault.parent / "scripts" / "build_index.py"
    if script.exists():
        subprocess.run([sys.executable, str(script), str(vault)], capture_output=True)


def reverse_mode(vault, wiki_root):
    """
    --reverse mode: scan vault/knowledge/ for nodes with "wiki-ingest" in tags,
    and create a reverse reference file in _wiki_ingest/wiki/entities/.
    """
    knowledge_dir = vault / "knowledge"
    if not knowledge_dir.is_dir():
        print("No knowledge/ directory found in vault")
        return 0

    entities_dir = wiki_root / "wiki" / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for f in sorted(knowledge_dir.glob("*.md")):
        if f.name == "index.md":
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(content)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        if "wiki-ingest" not in tags:
            skipped += 1
            continue

        distilled_from = meta.get("distilled_from", "")
        title = meta.get("title", f.stem)
        date_str = meta.get("date", "")

        # Build reverse reference filename from KAM file
        slug = slugify(title)
        ref_fn = f".kam-ref-{slug}.md"
        ref_path = entities_dir / ref_fn

        # Extract original wiki reference from distilled_from
        wiki_rel = ""
        if distilled_from:
            # distilled_from format: _wiki_ingest/wiki/entities/xxx.md
            wiki_rel = distilled_from.replace("_wiki_ingest/", "")

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        ref_content = (
            f"---\n"
            f"title: KAM Reverse Reference - {title}\n"
            f"kam_node: {f.name}\n"
            f"kam_title: {title}\n"
            f"kam_date: {date_str}\n"
            f"wiki_source: {wiki_rel}\n"
            f"date: {date_str}\n"
            f"source: agent\n"
            f"domain: ei\n"
            f"tags: [kam-ref, reverse-link]\n"
            f"status: raw\n"
            f"created_at: {now}\n"
            f"---\n\n"
            f"# KAM Reverse Reference: {title}\n\n"
            f"This knowledge node in the KAM vault was distilled from a wiki source.\n\n"
            f"## Original Wiki Source\n"
            f"- **Wiki path**: `{wiki_rel}`\n"
            f"- **KAM node**: `{f.name}`\n"
            f"- **KAM path**: `{f.relative_to(vault).as_posix()}`\n"
            f"- **Distilled on**: {now}\n\n"
            f"## Tags\n"
            f"- KAM tags: {', '.join(tags)}\n"
        )
        ref_path.write_text(ref_content, encoding="utf-8")
        created += 1
        print(f"  [CREATED] .kam-ref-{slug}.md -> {title}")

    print(f"\nReverse mode complete: {created} references created, {skipped} skipped (no wiki-ingest tag)")
    return created


def main():
    parser = argparse.ArgumentParser(description="LLM-Wiki to KAM distillation")
    parser.add_argument("--vault", help="vault path")
    parser.add_argument("--wiki", help="LLM-Wiki wiki path")
    parser.add_argument("--reverse", action="store_true", help="Create reverse references from KAM back to wiki")
    args = parser.parse_args()

    if args.vault:
        vault = Path(args.vault).resolve()
    else:
        vault = find_vault_root(Path.cwd())

    if args.wiki:
        wiki_root = Path(args.wiki).resolve()
    else:
        wiki_root = vault / "_wiki_ingest"

    # --reverse mode
    if args.reverse:
        print(f"[wiki_to_kam] Reverse mode: scanning KAM knowledge/ for wiki-ingest tags...")
        print(f"  Vault: {vault}")
        print(f"  Wiki: {wiki_root}")
        return reverse_mode(vault, wiki_root)

    # Normal forward distillation
    if not wiki_root.is_dir():
        print(f"Wiki dir not found: {wiki_root}")
        return 1

    distilled_path = wiki_root / ".distilled.json"
    distilled = load_json(distilled_path)
    domain = "ei"
    created = []
    skipped = 0

    handlers = [
        ("wiki/entities/", distill_entity),
        ("wiki/topics/", distill_entity),
        ("wiki/sources/", distill_source),
        ("wiki/comparisons/", distill_comparison),
        ("wiki/synthesis/", distill_synthesis),
    ]
    for subdir, handler in handlers:
        dp = wiki_root / subdir
        if not dp.is_dir(): continue
        for f in sorted(dp.glob("*.md")):
            result = handler(vault, wiki_root, f, distilled, domain)
            if result:
                wrel, krel = result
                created.append((wrel, krel))
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                distilled.setdefault("distilled_pages", {})[wrel] = now
                distilled.setdefault("newly_created", {})[krel] = now
            else:
                skipped += 1

    distilled["last_distilled_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    save_json(distilled_path, distilled)

    if created:
        print(f"Distilled: {len(created)} new, {skipped} skipped")
        for wrel, krel in created:
            print(f"  -> {krel}")
        append_journal(vault, [f"Distilled {len(created)} files"])
        run_build_index(vault)
    else:
        print(f"Nothing to distill ({skipped} skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
