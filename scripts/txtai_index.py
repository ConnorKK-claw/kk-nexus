import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json, argparse, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from txtai_utils import discover_md_files, read_md, build_index_text, chunk_markdown
from config import TEXTAI_INDEX_DIR, load_config

def _progress_iter(items, total, step=100):
    """分批进度生成器：每处理 step 条打印一次进度。"""
    for i, item in enumerate(items, 1):
        if i % step == 0:
            print(f"Indexed {i}/{total} documents...")
        yield item


def build_index(model="BAAI/bge-small-zh-v1.5", full=False, output_dir=None):
    if output_dir is None:
        output_dir = TEXTAI_INDEX_DIR

    from txtai import Embeddings
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all files
    print("Scanning vault files...")
    files = list(discover_md_files())
    print(f"Found {len(files)} markdown files")

    if not files:
        print("ERROR: No vault files found. Check vault paths.")
        return False

    # Build index data — P1-2: 按 ## 标题分块索引
    texts = []
    ids = []
    all_meta = {}
    skipped = 0
    total_files_indexed = 0
    for fp, domain in files:
        title, content, meta = read_md(fp)
        if not content or content.isspace():
            skipped += 1
            continue
        meta["filepath"] = str(fp)
        meta["domain"] = domain
        relpath = fp.relative_to(fp.anchor) if fp.is_absolute() else fp
        base_doc_id = str(relpath).replace("\\", "/")

        # P1-2: 分块索引，每个 chunk 作为一个 doc_id
        chunks = chunk_markdown(content)
        for idx, chunk in enumerate(chunks):
            if not chunk["text"].strip():
                continue
            text = build_index_text(title, chunk["text"], meta)
            doc_id = f"{base_doc_id}#{idx}" if len(chunks) > 1 else base_doc_id
            chunk_meta = dict(meta)
            chunk_meta["section"] = chunk["section"]
            chunk_meta["parent_file"] = base_doc_id
            chunk_meta["chunk_idx"] = idx
            texts.append(text)
            ids.append(doc_id)
            all_meta[doc_id] = chunk_meta
        total_files_indexed += 1

    print(f"Indexing {len(texts)} chunks from {total_files_indexed} files ({skipped} skipped)...")
    t0 = time.time()

    data = list(zip(ids, texts))
    total = len(data)

    if full or not (output_dir / "config.json").exists():
        # P1-1: 启用 hybrid 检索（BM25 关键词 + 向量双路融合）
        embeddings = Embeddings(path=model, content=True, sqlite={}, hybrid=True, scoring={"method": "bm25"})
        embeddings.index(_progress_iter(data, total, step=100))
        embeddings.save(str(output_dir))
    else:
        embeddings = Embeddings()
        embeddings.load(str(output_dir))
        embeddings.upsert(_progress_iter(data, total, step=100))

    elapsed = time.time() - t0
    elapsed_str = f"{elapsed:.0f}s" if elapsed < 120 else f"{elapsed/60:.1f}m"
    print(f"Index complete ({elapsed_str}): {len(texts)} docs, {len(files)} files scanned")

    # Save metadata
    meta_path = output_dir / "metadata.json"
    meta_path.write_text(json.dumps(all_meta, ensure_ascii=False, default=str), encoding="utf-8")

    # Save stats
    stats = {
        "total_docs": len(texts),
        "total_files": total_files_indexed,
        "total_files_scanned": len(files),
        "skipped": skipped,
        "model": model,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "vaults": list(set(m.get("domain", "") for m in all_meta.values())),
        "chunking": True,
        "hybrid": True,
    }
    (output_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")
    print(f"Index saved to {output_dir}")
    print(f"Stats: {stats}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Build txtai index from vault files")
    parser.add_argument("--full", action="store_true", help="Full rebuild")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="Embedding model")
    parser.add_argument("--output", default=None, help="Output directory")
    args = parser.parse_args()
    build_index(model=args.model, full=args.full, output_dir=args.output)

if __name__ == "__main__":
    main()


