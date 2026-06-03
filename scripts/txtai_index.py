import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json, argparse, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.txtai_utils import discover_md_files, read_md, build_index_text
from scripts import config

def build_index(model="BAAI/bge-small-zh-v1.5", full=False, output_dir=None):
    if output_dir is None:
        output_dir = config.TEXTAI_INDEX_DIR

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

    # Build index data
    texts = []
    ids = []
    all_meta = {}
    skipped = 0
    for fp, domain in files:
        title, content, meta = read_md(fp)
        if not content or content.isspace():
            skipped += 1
            continue
        text = build_index_text(title, content, meta)
        meta["filepath"] = str(fp)
        meta["domain"] = domain
        relpath = fp.relative_to(fp.anchor) if fp.is_absolute() else fp
        doc_id = str(relpath).replace("\\", "/")
        texts.append(text)
        ids.append(doc_id)
        all_meta[doc_id] = meta

    print(f"Indexing {len(texts)} documents ({skipped} skipped)...")
    t0 = time.time()

    if full or not (output_dir / "config.json").exists():
        embeddings = Embeddings(path=model, content=True, sqlite={})
        embeddings.index([(doc_id, text) for doc_id, text in zip(ids, texts)])
        embeddings.save(str(output_dir))
    else:
        embeddings = Embeddings()
        embeddings.load(str(output_dir))
        embeddings.upsert([(doc_id, text) for doc_id, text in zip(ids, texts)])

    elapsed = time.time() - t0
    elapsed_str = f"{elapsed:.0f}s" if elapsed < 120 else f"{elapsed/60:.1f}m"
    print(f"Index complete ({elapsed_str}): {len(texts)} docs, {len(files)} files scanned")

    # Save metadata
    meta_path = output_dir / "metadata.json"
    meta_path.write_text(json.dumps(all_meta, ensure_ascii=False, default=str), encoding="utf-8")

    # Save stats
    stats = {
        "total_docs": len(texts),
        "total_files": len(files),
        "skipped": skipped,
        "model": model,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "vaults": list(set(m.get("domain", "") for m in all_meta.values())),
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


