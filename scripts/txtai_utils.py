"""txtai shared utilities for KK Nexus"""
import os, re, sys, json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def vault_paths():
    """Read vault paths from UNIFIED_INDEX.md"""
    index_path = PROJECT_ROOT / "UNIFIED_INDEX.md"
    vaults = []
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        # Find vault paths: "- **Path**: `...`"
        for m in re.finditer(r'-\s+\*\*Path\*\*:\s+`(.+?)`', text):
            vaults.append(m.group(1))
    return vaults

def discover_md_files(vault_dirs=None):
    """Walk vault directories and yield (filepath, domain) pairs"""
    if vault_dirs is None:
        vault_dirs = vault_paths()
    if not vault_dirs:
        vault_dirs = list(Path(PROJECT_ROOT, ".codex", "skills").glob("*/vault"))
    for vd in vault_dirs:
        vpath = Path(vd)
        if not vpath.exists():
            continue
        domain = vpath.parent.name if vpath.parent.name != "skills" else "unknown"
        for md in vpath.rglob("*.md"):
            if "/." in str(md) or md.name.startswith("."):
                continue
            yield (md, domain)

def read_md(filepath):
    """Read markdown file, return (title, content, meta)"""
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return ("", "", {"error": str(e)})
    meta = {}
    title = filepath.stem
    content = text
    # Extract YAML frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            content = parts[2].strip()
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    if meta.get("title"):
        title = meta["title"]
    return (title, content, meta)

def build_index_text(title, content, meta):
    """Build the text that will be indexed from file content"""
    tags = meta.get("tags", "")
    domain = meta.get("domain", "")
    source = meta.get("source", "")
    date = meta.get("date", "")
    parts = [title, content]
    if domain:
        parts.insert(1, f"[领域: {domain}]")
    if tags:
        parts.insert(1, f"[标签: {tags}]")
    return "\n".join(parts)

def format_result(result, meta=None):
    """Format a search result for display"""
    text = result.get("text", "")
    score = result.get("score", 0)
    source = meta.get("source", "") if meta else ""
    domain = meta.get("domain", "") if meta else ""
    return {
        "score": round(score, 4),
        "text": text[:200] + "..." if len(text) > 200 else text,
        "domain": domain,
        "source": source,
    }

def search_with_gap(results, query):
    """Simple gap analysis: check if results are comprehensive"""
    if not results:
        return "脑内暂无相关信息。请确认是否已导入相关文档到 vault。"
    if len(results) < 3:
        return "找到少量相关文档，建议补充更多资料以获取全面答案。"
    return None
