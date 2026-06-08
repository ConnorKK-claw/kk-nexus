# -*- coding: utf-8 -*-
"""
006 Employee - Run All Layers Batch Crawl
Sequentially crawl L1+L2+L3+L4 for every defined layer.
Usage:
  python run_all_layers.py                # L1+L2+L3+L4 for all layers (sequential)
  python run_all_layers.py --skip-l4       # Skip slow L4 consensus EPS
  python run_all_layers.py --layer "半导体设备"  # Single layer only
  python run_all_layers.py --parallel L1   # Run L1+L3 in parallel across layers
"""
import sys, os, subprocess, datetime, time
sys.stdout.reconfigure(encoding="utf-8")

SCRIPTS = "C:/Users/hexk/.codex/skills/serenity-a-share-investor/scripts"
sys.path.insert(0, SCRIPTS)
from asi_stocks import STOCKS

def get_layers_by_priority():
    """Return layers ordered by count ascending (small layers first)."""
    layers = {}
    for s in STOCKS:
        l = s["layer"]
        layers[l] = layers.get(l, 0) + 1
    # Sort: small layers (fast) first, large layers (slow) last
    return sorted(layers.items(), key=lambda x: x[1])

def run_layer(layer_name, skip_l4=False):
    """Run batch for a single layer."""
    flags = "--l1 --l2 --l3"
    if not skip_l4:
        flags += " --l4"
    cmd = [sys.executable, os.path.join(SCRIPTS, "run_layer_batch.py"),
           "--layer", layer_name] + flags.split()
    print(f"\n{'='*60}")
    print(f"LAYER: {layer_name}")
    print(f"CMD: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-l4", action="store_true", help="Skip L4 (consensus EPS)")
    parser.add_argument("--layer", help="Run single layer only")
    args = parser.parse_args()

    start_time = time.time()
    today = datetime.date.today().strftime("%Y-%m-%d")

    if args.layer:
        layers = [(args.layer, 0)]  # count unknown
    else:
        layers = get_layers_by_priority()

    print(f"="*60)
    print(f"006 ASI Full Layer Crawl - {today}")
    print(f"Total layers: {len(layers)}")
    print(f"Skip L4: {args.skip_l4}")
    print(f"="*60)

    success_count = 0
    fail_count = 0
    for i, (layer_name, count) in enumerate(layers):
        print(f"\n>>> [{i+1}/{len(layers)}] {layer_name} (~{count if count else '?'} stocks)")
        ok = run_layer(layer_name, args.skip_l4)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        print(f"<<< {layer_name}: {'OK' if ok else 'FAILED'}")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Crawl Complete!")
    print(f"  Layers: {success_count} OK, {fail_count} FAILED")
    print(f"  Elapsed: {elapsed/60:.1f} min ({elapsed:.0f}s)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
