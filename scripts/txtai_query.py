import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json, argparse
import sys, json, argparse
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

def load_index():
    from txtai import Embeddings
    index_dir = config.TEXTAI_INDEX_DIR
    if not (index_dir / "config.json").exists():
        print(f"ERROR: Index not found at {index_dir}. Run: python scripts/txtai_index.py --full")
        sys.exit(1)
    embeddings = Embeddings()
    embeddings.load(str(index_dir))
    meta_path = index_dir / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return embeddings, meta, index_dir

def cmd_search(args):
    from txtai_utils import rerank_with_bge
    embeddings, meta, _ = load_index()
    # 召回扩大到 limit*3 用于 rerank；reranker 不可用时降级为原序
    recall_n = max(args.limit * 3, 30)
    raw = embeddings.search(args.query, recall_n)
    docs = []
    for r in raw:
        doc_id = r["id"]
        m = meta.get(doc_id, {})
        docs.append({
            "id": doc_id,
            "score": round(r["score"], 4),
            "text": r.get("text", ""),
            "title": m.get("title", doc_id),
            "domain": m.get("domain", ""),
            "filepath": m.get("filepath", doc_id),
        })
    # 二阶段 rerank（reranker 不可用时 rerank_with_bge 内部降级为原序截断）
    reranked = rerank_with_bge(args.query, docs, top_n=args.limit, threshold=0.3)
    if not reranked:
        print("召回结果经 rerank 阈值过滤后为空，知识库可能无相关内容。")
        return
    for d in reranked:
        score = d.get("rerank_score", d.get("score", 0))
        text = d.get("text", "")[:200].replace("\n", " ")
        print(f"[{score:.4f}] ({d['domain']}) {d['title']}")
        print(f"       {text}...")
        print(f"       ? {d['filepath']}")
        print()

def cmd_ask(args):
    from txtai_utils import rerank_with_bge
    embeddings, meta, _ = load_index()
    # 召回 30 条用于 rerank
    raw = embeddings.search(args.query, 30)
    if not raw:
        print("无搜索结果")
        return
    docs = []
    for r in raw:
        doc_id = r["id"]
        m = meta.get(doc_id, {})
        docs.append({
            "id": doc_id,
            "score": round(r["score"], 4),
            "text": r.get("text", ""),
            "title": m.get("title", doc_id),
            "domain": m.get("domain", ""),
            "filepath": m.get("filepath", doc_id),
        })
    # 二阶段 rerank 取 top 5
    reranked = rerank_with_bge(args.query, docs, top_n=5, threshold=0.3)
    if not reranked:
        print("召回结果经 rerank 阈值过滤后为空，知识库可能无相关内容。")
        return
    # 构造带来源标注的 context（合规要求：每个指导性观点须附 [来源: 文件名]）
    context_block = "\n\n".join(
        f"[来源{i+1}: {d.get('filepath', d.get('title', ''))}]\n{d.get('text', '')[:500]}"
        for i, d in enumerate(reranked)
    )
    api_key = config.DEEPSEEK_API_KEY
    if api_key and not args.no_rag:
        prompt = f"""基于以下知识库来源回答问题。每个指导性观点必须以 [来源: 文件名] 标注。
若来源不足以回答，明确说明"知识库无充分依据"，不得编造。

{context_block}

问题：{args.query}

回答（含来源标注）："""
        try:
            # 统一 LLM client（限流 + OTel trace）
            from llm_client import call_llm
            answer, _usage = call_llm(
                messages=[{"role": "user", "content": prompt}],
                trace_name="txtai_query.rag_synthesis",
            )
            # 后处理：检查来源标注合规性，无标注则追加推测声明
            if "[来源:" not in answer and "[来源" not in answer:
                answer += "\n\n[自行推测观点] 本回答未能在知识库中找到充分来源标注，请核实。"
            print(answer)
        except Exception as e:
            print(f"[RAG 请求失败: {e}]")
            print("降级为纯语义搜索")
            cmd_search(args)
    else:
        print("未设置 DEEPSEEK_API_KEY 或使用 --no-rag，返回 rerank 后的搜索结果：\n")
        for d in reranked:
            score = d.get("rerank_score", d.get("score", 0))
            print(f"[{score:.4f}] ({d['domain']}) {d['title']}")
            print(f"       ? {d['filepath']}")
            print()

def cmd_stats(args):
    index_dir = config.TEXTAI_INDEX_DIR
    stats_file = index_dir / "stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        print(f"索引状态:")
        print(f"  文档数: {stats.get('total_docs', '?')}")
        print(f"  文件数: {stats.get('total_files', '?')}")
        print(f"  模型: {stats.get('model', '?')}")
        print(f"  构建时间: {stats.get('date', '?')}")
        vaults = stats.get("vaults", [])
        if vaults:
            print(f"  Domain 覆盖: {', '.join(vaults)}")
    else:
        print("stats.json 不存在，直接从 embeddings 读取...")
        embeddings, meta, _ = load_index()
        print(f"  向量数: {len(embeddings)}")
        domains = set(m.get("domain", "") for m in meta.values())
        print(f"  Domain 覆盖: {', '.join(sorted(domains)) if domains else ''}")

def main():
    parser = argparse.ArgumentParser(description="txtai 查询工具")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词")
    parser.add_argument("--limit", type=int, default=10, help="返回结果数")
    parser.add_argument("--rag", action="store_true", help="启用 RAG 回答")
    parser.add_argument("--no-rag", action="store_true", help="禁用 RAG，仅显示搜索结果")
    parser.add_argument("--stats", action="store_true", help="显示索引统计")
    parser.add_argument("--explain", action="store_true", help="搜索 + 解释")
    args = parser.parse_args()

    if args.stats:
        cmd_stats(args)
    elif args.query:
        if args.rag:
            cmd_ask(args)
        else:
            cmd_search(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()




