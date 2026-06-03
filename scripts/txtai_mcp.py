import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json, time, traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Global state — lazy init
_embeddings = None
_metadata = None
_index_path = None

def get_embeddings():
    global _embeddings, _metadata, _index_path
    if _embeddings is not None:
        return _embeddings, _metadata
    from txtai import Embeddings
    index_dir = Path.home() / ".txtai_index"
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
    embeddings, meta = get_embeddings()
    results = embeddings.search(query, limit)
    output = []
    for r in results:
        doc_id = r["id"]
        m = meta.get(doc_id, {})
        if domain and m.get("domain") != domain:
            continue
        output.append({
            "score": round(r["score"], 4),
            "filepath": m.get("filepath", doc_id),
            "domain": m.get("domain", ""),
            "title": m.get("title", ""),
            "text": r.get("text", "")[:300],
            "tags": m.get("tags", ""),
        })
    return output

def handle_ask(query, domain=None):
    from scripts.txtai_utils import search_with_gap
    results = handle_search(query, limit=10, domain=domain)
    gap = search_with_gap(results, query)
    
    # DeepSeek synthesis
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if api_key:
        try:
            import httpx
            context = "\n\n".join(
                f"[{r['domain']}] {r['filepath']}\n{r['text']}" for r in results[:5]
            )

知识库内容：
{context}

用户问题：{query}

            r = httpx.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=30,
            )
            answer = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            answer = f"[合成错误: {e}]"
    else:
        # No API key — return raw search
        answer = "未配置 DEEPSEEK_API_KEY，返回原始搜索结果。\n\n" + json.dumps(results[:5], ensure_ascii=False, indent=2)
    return {"answer": answer, "sources": results[:5], "gap_analysis": gap, "total_results": len(results)}

def handle_stats():
    index_dir = Path.home() / ".txtai_index"
    if not index_dir.exists():
        return {"status": "not_found", "path": str(index_dir)}
    stats_file = index_dir / "stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        return stats
    try:
        embeddings, _ = get_embeddings()
        return {"total_docs": len(embeddings), "status": "loaded"}
    except:
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


