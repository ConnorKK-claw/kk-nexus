"""
auto_distill.py - 自动蒸馏检查 (供 auto-update 调度)
"""
import subprocess, sys
from pathlib import Path

def main():
    vault = Path(__file__).parent / "vault"
    wiki = vault / "_wiki_ingest"
    if not wiki.exists():
        print("[auto_distill] _wiki_ingest not found at", wiki)
        return
    print("[auto_distill] Running wiki_to_kam.py...")
    result = subprocess.run([
        sys.executable,
        str(Path(__file__).parent / "wiki_to_kam.py"),
        "--vault", str(vault),
        "--wiki", str(wiki),
    ], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("[auto_distill] ERROR:", result.stderr)
    else:
        print("[auto_distill] Done")

if __name__ == "__main__":
    main()

