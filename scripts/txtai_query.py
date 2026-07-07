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
    embeddings, meta, _ = load_index()
    results = embeddings.search(args.query, args.limit)
    for r in results:
        doc_id = r["id"]
        m = meta.get(doc_id, {})
        score = round(r["score"], 4)
        title = m.get("title", doc_id)
        domain = m.get("domain", "")
        filepath = m.get("filepath", doc_id)
        text = r.get("text", "")[:200].replace("\n", " ")
        print(f"[{score:.4f}] ({domain}) {title}")
        print(f"       {text}...")
        print(f"       ? {filepath}")
        print()

def cmd_ask(args):
    embeddings, meta, _ = load_index()
    results = embeddings.search(args.query, 10)
    if not results:
        print("无搜索结果")
        return
    context = "\n\n".join(
        f"[{meta.get(d['id'], {}).get('domain', '?')}] {meta.get(d['id'], {}).get('title', d['id'])}\n{d.get('text', '')[:500]}"
        for d in results[:5]
    )
    api_key = config.DEEPSEEK_API_KEY
    if api_key and not args.no_rag:
        import httpx

        prompt = f"""根据以下检索到的知识回答用户问题：

        {context}

        用户问题：{args.query}

        请基于检索到的知识回答问题，如果知识不足以回答请明确说明。"""
        try:
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
            print(answer)
        except Exception as e:
            print(f"[RAG 请求失败: {e}]")
            print("降级为纯语义搜索")
            cmd_search(args)
    else:
        print("未设置 DEEPSEEK_API_KEY 或使用 --no-rag无搜索结果\n")
        cmd_search(args)

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



