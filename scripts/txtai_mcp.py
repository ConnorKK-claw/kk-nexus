import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json, time, traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

# Global state — lazy init
_embeddings = None
_metadata = None
_index_path = None

def get_embeddings():
    global _embeddings, _metadata, _index_path
    if _embeddings is not None:
        return _embeddings, _metadata
    from txtai import Embeddings
    index_dir = config.TEXTAI_INDEX_DIR
    if not (index_dir / "config.json").exists():
        raise RuntimeError(f"Index not found at {index_dir}. Run: python scripts/txtai_index.py --full")
    _embeddings = Embeddings()
    _embeddings.load(str(index_dir))
    _index_path = index_dir
    meta_path = index_dir / "metadata.json"
    if meta_path.exists():
        _metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        _metadata = {}
    return _embeddings, _metadata

def handle_search(query, limit=10, domain=None):
    from txtai_utils import rerank_with_bge
    embeddings, meta = get_embeddings()
    # 召回扩大到 limit*3 用于 rerank
    recall_n = max(limit * 3, 30)
    raw = embeddings.search(query, recall_n)
    docs = []
    for r in raw:
        doc_id = r["id"]
        m = meta.get(doc_id, {})
        if domain and m.get("domain") != domain:
            continue
        docs.append({
            "id": doc_id,
            "score": round(r["score"], 4),
            "filepath": m.get("filepath", doc_id),
            "domain": m.get("domain", ""),
            "title": m.get("title", ""),
            "text": r.get("text", "")[:300],
            "tags": m.get("tags", ""),
        })
    # 二阶段 rerank（reranker 不可用时降级为原序截断）
    reranked = rerank_with_bge(query, docs, top_n=limit, threshold=0.3)
    return reranked

def handle_ask(query, domain=None):
    from txtai_utils import search_with_gap, rerank_with_bge
    # 召回 30 条用于 rerank，取 top 5 喂 LLM
    candidates = handle_search(query, limit=30, domain=domain)
    reranked = rerank_with_bge(query, candidates, top_n=5, threshold=0.3)
    gap = search_with_gap(reranked, query, min_score=0.3)

    # DeepSeek synthesis
    api_key = config.DEEPSEEK_API_KEY
    if api_key:
        if not reranked:
            return {
                "answer": "知识库无充分依据回答该问题。" + (gap or ""),
                "sources": [],
                "gap_analysis": gap or "召回结果经 rerank 阈值过滤后为空",
                "total_results": 0,
            }
        try:
            # 构造带来源标注的 context（合规要求）
            context_block = "\n\n".join(
                f"[来源{i+1}: {r.get('filepath', r.get('title', ''))}]\n{r.get('text', '')}"
                for i, r in enumerate(reranked)
            )
            prompt = f"""基于以下知识库来源回答问题。每个指导性观点必须以 [来源: 文件名] 标注。
若来源不足以回答，明确说明"知识库无充分依据"，不得编造。

{context_block}

用户问题：{query}

回答（含来源标注）："""
            # P2-4: 统一 LLM client（限流 + OTel trace）
            from llm_client import call_llm
            answer, _usage = call_llm(
                messages=[{"role": "user", "content": prompt}],
                trace_name="txtai_mcp.rag_synthesis",
            )
            # 后处理：检查来源标注合规性
            if "[来源:" not in answer and "[来源" not in answer:
                answer += "\n\n[自行推测观点] 本回答未能在知识库中找到充分来源标注，请核实。"
        except Exception as e:
            answer = f"[合成错误: {e}]"
    else:
        # No API key — return raw search
        answer = "未配置 DEEPSEEK_API_KEY，返回原始搜索结果。\n\n" + json.dumps(reranked[:5], ensure_ascii=False, indent=2)
    return {"answer": answer, "sources": reranked[:5], "gap_analysis": gap, "total_results": len(reranked)}

def handle_stats():
    index_dir = config.TEXTAI_INDEX_DIR
    if not index_dir.exists():
        return {"status": "not_found", "path": str(index_dir)}
    stats_file = index_dir / "stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        return stats
    try:
        embeddings, _ = get_embeddings()
        return {"total_docs": len(embeddings), "status": "loaded"}
    except Exception:
        return {"status": "error"}

# MCP protocol implementation
TOOLS = [
    {
        "name": "txtai_search",
        "description": "语义搜索 vault 知识库，返回相关文档片段及分数",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "number", "description": "返回结果数（默认10）"},
                "domain": {"type": "string", "description": "按 domain 过滤（可选）"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "txtai_ask",
        "description": "RAG 问答：搜索 vault 后用 LLM 合成带引用的回答",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "问题"},
                "domain": {"type": "string", "description": "按 domain 过滤（可选）"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "txtai_stats",
        "description": "查看 txtai 索引统计信息",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

def mcp_main():
    import sys
    stdin = sys.stdin
    stdout = sys.stdout
    
    # Initial message
    init_msg = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
    stdout.write(json.dumps(init_msg) + "\n")
    stdout.flush()

    for line in stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "kk-nexus-txtai", "version": "1.0.0"},
                },
            }
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            tool = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool == "txtai_search":
                    result = handle_search(args.get("query", ""), args.get("limit", 10), args.get("domain"))
                    content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                elif tool == "txtai_ask":
                    result = handle_ask(args.get("query", ""), args.get("domain"))
                    text = f"{result['answer']}\n\n---\n来源: {result['total_results']} 个文档\n"
                    if result["gap_analysis"]:
                        text += f"\n[Gap] {result['gap_analysis']}"
                    content = [{"type": "text", "text": text}]
                elif tool == "txtai_stats":
                    result = handle_stats()
                    content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                else:
                    content = [{"type": "text", "text": f"Unknown tool: {tool}"}]
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content}}
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32000, "message": str(e), "data": traceback.format_exc()},
                }
        elif method == "notifications/initialized":
            continue
        else:
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        
        stdout.write(json.dumps(resp) + "\n")
        stdout.flush()

if __name__ == "__main__":
    # If --test passed, run a single test query
    if "--test" in sys.argv:
        import json
        q = sys.argv[sys.argv.index("--test") + 1] if "--test" in sys.argv and len(sys.argv) > sys.argv.index("--test") + 1 else "测试"
        print(json.dumps(handle_search(q, 5), ensure_ascii=False, indent=2))
    else:
        mcp_main()



