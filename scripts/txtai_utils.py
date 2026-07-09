"""txtai shared utilities for KK Nexus"""
import os, re, sys, json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def vault_paths():
    """Read vault paths from UNIFIED_INDEX.md, with cross-machine fallback."""
    index_path = PROJECT_ROOT / "UNIFIED_INDEX.md"
    vaults = []
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        # Find vault paths: "- **Path**: `...`"
        for m in re.finditer(r'-\s+\*\*Path\*\*:\s+`(.+?)`', text):
            raw_path = m.group(1)
            # Cross-user fallback: if path points to a different user home,
            # remap to current user home while keeping the relative tail.
            p = Path(raw_path)
            if not p.exists():
                parts = p.parts
                if len(parts) >= 3 and parts[0].lower().startswith("c:") and parts[1].lower() == "users":
                    remapped = Path.home() / Path(*parts[3:])
                    if remapped.exists():
                        vaults.append(str(remapped))
                        continue
            vaults.append(raw_path)
    return vaults

def discover_md_files(vault_dirs=None):
    """Walk vault directories and yield (filepath, domain) pairs"""
    if vault_dirs is None:
        vault_dirs = vault_paths()
    if not vault_dirs:
        vault_dirs = []
    # Always include project-local skills vaults (e.g. overseas-research)
    local_skills = PROJECT_ROOT / "skills"
    if local_skills.exists():
        vault_dirs.extend(str(d) for d in local_skills.glob("*/vault") if d.is_dir())
    # Legacy fallback
    legacy = Path(PROJECT_ROOT, ".codex", "skills")
    if legacy.exists():
        vault_dirs.extend(str(d) for d in legacy.glob("*/vault") if d.is_dir())
    seen = set()
    for vd in vault_dirs:
        vpath = Path(vd)
        if not vpath.exists():
            continue
        real = vpath.resolve()
        if real in seen:
            continue
        seen.add(real)
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


def chunk_markdown(content: str, max_chunk: int = 800, overlap: int = 100) -> list:
    """P1-2: 按 ## 标题切分 markdown，返回 [{text, section}]。

    保留语义边界（二级标题作为分块边界），长段落再按 max_chunk 切分并带 overlap。

    Args:
        content: markdown 正文（已去除 frontmatter）
        max_chunk: 单块最大字符数
        overlap: 长段落切分时的重叠字符数

    Returns:
        [{text: str, section: str}] 分块列表
    """
    if not content or not content.strip():
        return [{"text": "", "section": "root"}]
    # 按 ## 标题切分（保留标题作为 section 名）
    sections = re.split(r'^(##\s+.+)$', content, flags=re.M)
    chunks = []
    current_section = "root"
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if sec.startswith('## '):
            current_section = sec
            continue
        # 长段落再按 max_chunk 切分
        if len(sec) > max_chunk:
            step = max(max_chunk - overlap, 1)
            for j in range(0, len(sec), step):
                chunk_text = sec[j:j + max_chunk]
                if chunk_text.strip():
                    chunks.append({"text": chunk_text, "section": current_section})
                if j + max_chunk >= len(sec):
                    break
        else:
            chunks.append({"text": sec, "section": current_section})
    return chunks if chunks else [{"text": content, "section": "root"}]

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

def search_with_gap(results, query, min_score=0.0):
    """Gap 分析：检查结果是否充分。可选按 min_score 过滤低质召回。"""
    if min_score > 0 and results:
        results = [r for r in results if r.get("score", 0) >= min_score]
    if not results:
        return "脑内暂无相关信息。请确认是否已导入相关文档到 vault。"
    if len(results) < 3:
        return "找到少量相关文档，建议补充更多资料以获取全面答案。"
    return None


# ============ Reranker (P0-1) ============
_reranker = None
_reranker_disabled = False


def get_reranker():
    """懒加载 bge-reranker-base 单例。失败则返回 None 并标记禁用。"""
    global _reranker, _reranker_disabled
    if _reranker_disabled:
        return None
    if _reranker is None:
        try:
            from FlagEmbedding import FlagReranker
            model_path = PROJECT_ROOT / "models" / "bge-reranker-base"
            use_path = str(model_path) if model_path.exists() else "BAAI/bge-reranker-base"
            _reranker = FlagReranker(use_path, use_fp16=False)
        except Exception as e:
            print(f"[WARN] bge-reranker-base 加载失败，降级为无 rerank: {e}", file=sys.stderr)
            _reranker_disabled = True
            return None
    return _reranker


def rerank_with_bge(query, docs, top_n=5, threshold=0.3):
    """
    用 bge-reranker-base 对召回结果做二阶段重排。

    Args:
        query: 查询字符串
        docs: list of dict，每个 dict 须含 'text' 字段
        top_n: 重排后保留的前 N 条
        threshold: rerank score 归一化阈值，低于此值的丢弃

    Returns:
        list of dict，含原 doc 字段 + 'rerank_score'。若 reranker 不可用则原样返回（截断 top_n）。
    """
    if not docs:
        return []
    reranker = get_reranker()
    if reranker is None:
        return docs[:top_n]

    pairs = [[query, d.get("text", "")] for d in docs]
    try:
        scores = reranker.compute_score(pairs, normalize=True)
    except Exception as e:
        print(f"[WARN] rerank compute_score 失败，降级为原序: {e}", file=sys.stderr)
        return docs[:top_n]

    if isinstance(scores, float):
        scores = [scores]

    ranked = sorted(zip(docs, scores), key=lambda x: -x[1])
    result = []
    for d, s in ranked[:top_n]:
        if s >= threshold:
            enriched = dict(d)
            enriched["rerank_score"] = round(float(s), 4)
            result.append(enriched)
    return result
