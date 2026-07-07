#!/usr/bin/env python3
"""
unified_index.py - Generate unified index across KAM vaults and llm-wiki stores.

Usage:
    python scripts/unified_index.py                  # Build index (cached)
    python scripts/unified_index.py --refresh        # Force rebuild
    python scripts/unified_index.py --check-stale    # Exit 1 if >24h old
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = Path.home() / ".codex" / "memories" / "ontology" / "graph.jsonl"
CACHE_PATH = PROJECT_ROOT / ".unified_index_cache.json"
INDEX_PATH = PROJECT_ROOT / "UNIFIED_INDEX.md"

WIKI_SUBDIRS = [
    "_wiki_ingest/wiki/entities/",
    "_wiki_ingest/wiki/topics/",
    "_wiki_ingest/wiki/sources/",
]


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    meta = {}
    content = content.strip()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            for line in fm_text.splitlines():
                line = line.strip()
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if val.startswith("[") and val.endswith("]"):
                        items = val[1:-1].split(",")
                        cleaned = []
                        for v in items:
                            v = v.strip().strip("\"").strip("'")
                            if v:
                                cleaned.append(v)
                        meta[key] = cleaned
                    else:
                        meta[key] = val.strip("\"").strip("'")
    return meta


def load_ontology_vaults() -> list[dict]:
    """Load Vault entities from ontology graph.jsonl."""
    vaults = []
    if not ONTOLOGY_PATH.exists():
        print(f"[WARN] Ontology not found: {ONTOLOGY_PATH}", file=sys.stderr)
        return vaults
    for line in ONTOLOGY_PATH.read_text(encoding="utf-8-sig").strip().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        entity = obj.get("entity", {})
        if entity.get("type") == "Vault":
            props = entity.get("properties", {})
            vault_path = Path(props.get("path", ""))
            vaults.append({
                "id": entity.get("id", ""),
                "name": props.get("name", vault_path.name),
                "path": vault_path,
                "domain": props.get("domain", ""),
            })
    return vaults


def scan_vault_files(vault: dict) -> list[dict]:
    """Scan vault directories for .md files and extract frontmatter."""
    files = []
    vpath = vault["path"]
    if not vpath.is_dir():
        return files

    for subdir in ["knowledge", "cases", "templates"]:
        dp = vpath / subdir
        if not dp.is_dir():
            continue
        for f in sorted(dp.glob("*.md")):
            if f.name == "index.md":
                continue
            entry = _file_entry(f, vault, subdir)
            if entry:
                files.append(entry)

    for rel_dir in WIKI_SUBDIRS:
        dp = vpath / rel_dir
        if not dp.is_dir():
            continue
        source_label = rel_dir.rstrip("/").replace("_wiki_ingest/wiki/", "wiki/")
        for f in sorted(dp.glob("*.md")):
            entry = _file_entry(f, vault, source_label)
            if entry:
                files.append(entry)

    return files


def _file_entry(fpath: Path, vault: dict, section: str) -> dict | None:
    """Extract metadata from one markdown file."""
    try:
        content = fpath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    meta = parse_frontmatter(content)
    title = meta.get("title", fpath.stem)
    date_val = meta.get("date") or meta.get("created", "")
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    status = meta.get("status", "")
    domain = meta.get("domain", vault.get("domain", ""))
    return {
        "vault": vault["name"],
        "section": section,
        "file": str(fpath.relative_to(vault["path"]).as_posix()),
        "title": title,
        "date": date_val,
        "tags": tags,
        "status": status,
        "domain": domain,
        "updated": datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def build_index(vaults: list[dict]) -> str:
    """Build the UNIFIED_INDEX.md content."""
    lines = []
    lines.append("# Unified Index - All Vaults")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("> Use this index to determine which vault contains relevant content.")
    lines.append("> Then consult the vault's own `knowledge/index.md` for O(1) retrieval.")
    lines.append("")

    total_files = 0
    for vault in vaults:
        files = vault.get("_files", [])
        lines.append(f"## {vault['name']}")
        lines.append("")
        lines.append(f"- **Path**: `{vault['path']}`")
        lines.append(f"- **Domain**: {vault.get('domain', 'N/A')}")
        lines.append(f"- **Files**: {len(files)}")
        lines.append("")

        if not files:
            lines.append("_No indexed files._")
            lines.append("")
            continue

        sections = {}
        for f in files:
            sections.setdefault(f["section"], []).append(f)

        for section_name, sec_files in sorted(sections.items()):
            lines.append(f"### {section_name}/ ({len(sec_files)} files)")
            lines.append("")
            for f in sec_files:
                tags_str = ", ".join(f["tags"][:5]) if f["tags"] else ""
                date_str = f["date"] if f["date"] else "?"
                status_str = f" [{f['status']}]" if f["status"] else ""
                tag_suffix = f" - tags: {tags_str}" if tags_str else ""
                lines.append(f"- `{f['file']}`{status_str} - {f['title']} ({date_str}){tag_suffix}")
            lines.append("")
        total_files += len(files)

    lines.append("---")
    lines.append("")
    lines.append(f"**Total**: {total_files} files across {len(vaults)} vaults")
    return "\n".join(lines)


def save_cache(vaults: list[dict]):
    """Save serializable cache of index data."""
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vault_count": len(vaults),
        "vaults": [
            {
                "name": v["name"],
                "path": str(v["path"]),
                "domain": v.get("domain", ""),
                "file_count": len(v.get("_files", [])),
            }
            for v in vaults
        ],
    }
    CACHE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_cache() -> dict | None:
    """Load cached index metadata if fresh."""
    if not CACHE_PATH.exists():
        return None
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception):
        return None
    generated = data.get("generated_at", "")
    try:
        dt = datetime.fromisoformat(generated)
        age = datetime.now(timezone.utc) - dt
        if age.total_seconds() < 86400:
            return data
    except Exception:
        pass
    return None



def get_txtai_status():
    """Get txtai index status for UNIFIED_INDEX.md"""
    txtai_dir = PROJECT_ROOT / ".txtai" / "index"
    if not txtai_dir.exists():
        return "**txtai**: Not indexed"
    stats_file = txtai_dir / "stats.json"
    if stats_file.exists():
        try:
            import json
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
            docs = stats.get("total_docs", "?")
            model = stats.get("model", "?")
            date = stats.get("date", "?")
            return f"**txtai**: {docs} docs, {model}, built {date}"
        except Exception:
            return "**txtai**: Index corrupted"
    return "**txtai**: Index files missing"
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Unified index across KAM vaults and llm-wiki")
    parser.add_argument("--refresh", action="store_true", help="Force rebuild index")
    parser.add_argument("--check-stale", action="store_true", help="Exit 1 if index older than 24h")
    args = parser.parse_args()

    if args.check_stale:
        cached = load_cache()
        if cached:
            print(f"[OK] Index is fresh (generated: {cached['generated_at']})")
            return 0
        else:
            print("[ERR] Index is stale or missing (older than 24h)")
            return 1

    if not args.refresh:
        cached = load_cache()
        if cached:
            print("[OK] Using cached index. Use --refresh to rebuild.")
            return 0

    vault_data = load_ontology_vaults()
    # Fallback vaults: 既补全 ontology 中缺失的 KAM vault，也保留项目内独立 vault
    fallback_vaults = [
        Path.home() / ".codex" / "skills" / "equity-incentive" / "vault",
        Path.home() / ".codex" / "skills" / "financial-analysis" / "vault",
        Path.home() / ".codex" / "skills" / "tax-compliance-expert" / "vault",
        Path.home() / ".codex" / "skills" / "weekly-report" / "vault",
        Path.home() / ".codex" / "skills" / "hk-ipo" / "vault",
        Path.home() / ".codex" / "skills" / "trading-agents-007" / "vault",
        Path.home() / ".codex" / "skills" / "serenity-a-share-investor" / "vault",
        Path.home() / ".codex" / "skills" / "ima-knowledge" / "vault",
        Path.home() / ".codex" / "skills" / "quant-factor-skill" / "vault",
        Path.home() / ".codex" / "skills" / "trading-analysis" / "vault",
        PROJECT_ROOT / "skills" / "overseas-research-20260706-001" / "vault",
    ]
    existing_paths = {str(v["path"]).lower() for v in vault_data}
    added_fallback = False
    for vp in fallback_vaults:
        if vp.is_dir() and str(vp).lower() not in existing_paths:
            if not added_fallback:
                print("[INFO] Merging fallback vault paths...", file=sys.stderr)
                added_fallback = True
            vault_data.append({
                "id": f"vault_{vp.parent.name}",
                "name": vp.parent.name,
                "path": vp,
                "domain": vp.parent.name,
            })

    for v in vault_data:
        v["_files"] = scan_vault_files(v)

    index_content = build_index(vault_data)
    INDEX_PATH.write_text(index_content, encoding="utf-8")
    save_cache(vault_data)

    total = sum(len(v.get("_files", [])) for v in vault_data)
    print(f"[OK] UNIFIED_INDEX.md written ({len(vault_data)} vaults, {total} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
