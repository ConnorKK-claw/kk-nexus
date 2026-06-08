# -*- coding: utf-8 -*-
"""
006 Employee - ASI Pipeline (Integrated)
Orchestrates: WIND expansion -> Data crawl -> Pool classification -> Index generation
Usage: python asi_pipeline.py [--full] [--layer "半导体设备"] [--skip-l5] [--wind-wind-file ...]
"""
import sys, os, csv, datetime, subprocess, json, time
sys.stdout.reconfigure(encoding="utf-8")

VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
SCRIPTS = os.path.join(VAULT, "scripts")
RAW = os.path.join(VAULT, "vault", "raw", "agent")
KNOW = os.path.join(VAULT, "vault", "knowledge")
TODAY = datetime.date.today().strftime("%Y-%m-%d")

def run_script(cmd, desc):
    """Run a subprocess and report."""
    print(f"\n{'='*60}")
    print(f"Step: {desc}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=False, timeout=3600)
    if result.returncode == 0:
        print(f"  OK")
    else:
        print(f"  FAILED (code {result.returncode})")
    return result.returncode

def generate_company_registry(stocks_with_pools):
    """Generate zk-asi-company-registry.md from pool classification results."""
    lines = []
    lines.append("---")
    lines.append(f"title: ASI\u4e2a\u80a1\u767b\u8bb0\u603b\u8868")
    lines.append(f"date: {TODAY}")
    lines.append("source: agent")
    lines.append("status: auto_generated")
    lines.append(f"data_source: vault/raw/agent/{TODAY}-asi-pool-*.csv")
    lines.append("---")
    lines.append("")
    lines.append(f"# ASI\u4e2a\u80a1\u767b\u8bb0\u603b\u8868 ({TODAY})")
    lines.append("")
    lines.append("| \u4ee3\u7801 | \u540d\u79f0 | \u4ea7\u4e1a\u94fe\u5c42 | \u6838\u5fc3\u58c1\u5792\u6c60 | \u4f4e\u4f30\u503c\u6c60 | \u9ad8\u589e\u957f\u6c60 | \u9f99\u5934\u6c60 | WIND_L1 | WIND_L2 | \u5b9a\u6027\u58c1\u5792 |")
    lines.append("|------|------|---------|-----------|---------|---------|-------|---------|---------|---------|")
    
    for s in stocks_with_pools:
        lines.append(f"| {s['code']} | {s['name']} | {s['layer']} | {s.get('pool_core_moat','')} | {s.get('pool_low_val','')} | {s.get('pool_high_growth','')} | {s.get('pool_sector_leader','')} | {s.get('wind_l1','')} | {s.get('wind_l2','')} | {s.get('moat_proxy','')} |")
    
    path = os.path.join(KNOW, "zk-asi-company-registry.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Generated: {path}")
    return path

def generate_pool_index():
    """Generate zk-asi-pool-index.md with pool statistics."""
    # Read latest pool CSVs
    pools = {}
    for fname in os.listdir(RAW):
        if fname.endswith(".csv") and "-asi-pool-" in fname and fname.startswith(TODAY):
            pool_name = fname.split("-asi-pool-")[1].replace(".csv", "")
            with open(os.path.join(RAW, fname), "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            pools[pool_name] = rows
    
    lines = []
    lines.append("---")
    lines.append(f"title: ASI\u6c60\u5b50\u603b\u7d22\u5f15")
    lines.append(f"date: {TODAY}")
    lines.append("source: agent")
    lines.append("status: auto_update")
    lines.append(f"data_source: vault/raw/agent/{TODAY}-asi-pool-*.csv")
    lines.append("---")
    lines.append("")
    lines.append(f"# ASI\u6c60\u5b50\u603b\u7d22\u5f15 ({TODAY})")
    lines.append("")
    
    pool_names_cn = {
        "core-moat": "\u6838\u5fc3\u58c1\u5792\u6c60",
        "low-val": "\u4f4e\u4f30\u503c\u6c60",
        "high-growth": "\u9ad8\u589e\u957f\u6c60",
        "sector-leader": "\u7ec6\u5206\u9f99\u5934\u6c60",
        "power-upstream": "\u7535\u529b\u4e0a\u6e38\u6c60",
    }
    for pool_name, pool_stocks in sorted(pools.items()):
        cn_name = pool_names_cn.get(pool_name, pool_name)
        lines.append(f"\n## {cn_name} ({len(pool_stocks)} only)")
        lines.append("")
        
        # Stats
        mcaps = [float(s.get("mkt_cap", 0)) for s in pool_stocks if s.get("mkt_cap")]
        pes = [float(s.get("pe_ttm", 0)) for s in pool_stocks if 0 < float(s.get("pe_ttm", 0)) < 500]
        if mcaps: lines.append(f"- \u5e73\u5747\u5e02\u503c: {sum(mcaps)/len(mcaps):.0f}\u4ebf")
        if pes: lines.append(f"- \u5e73\u5747PE: {sum(pes)/len(pes):.0f}")
        lines.append("")
        lines.append("| \u4ee3\u7801 | \u540d\u79f0 | \u5c42 | \u5e02\u503c | PE | ROE |")
        lines.append("|------|------|----|------|----|----|")
        for s in sorted(pool_stocks, key=lambda x: float(x.get("mkt_cap", 0)), reverse=True)[:15]:
            lines.append(f"| {s['code']} | {s['name']} | {s.get('layer','')} | {s.get('mkt_cap','')} | {s.get('pe_ttm','')} | {s.get('roe','')} |")
    
    path = os.path.join(KNOW, "zk-asi-pool-index.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Generated: {path}")
    return path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ASI Pipeline")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument("--layer", help="Run only for specific layer")
    parser.add_argument("--wind-file", help="WIND Excel path for expansion")
    parser.add_argument("--skip-l5", action="store_true", help="Skip L5 research reports")
    parser.add_argument("--refresh-index", action="store_true", help="Only regenerate index nodes")
    args = parser.parse_args()
    
    print(f"==== ASI Pipeline v2 - {TODAY} ====")
    start_time = time.time()
    
    if args.refresh_index:
        print("\n[Index Refresh Only]")
        generate_pool_index()
        print(f"\nDone in {time.time()-start_time:.0f}s")
        return
    
    # Step 1: WIND expansion (if --wind-file provided)
    if args.wind_file:
        expand_script = os.path.join(SCRIPTS, "expand_asi_universe.py")
        cmd = f'python "{expand_script}" --wind-file "{args.wind_file}" --wind-layer 半导体 --min-mcap 20'
        run_script(cmd, "WIND\u6269\u5c55")
    
    # Step 2: Data fetch (full or per-layer)
    if args.full:
        fetch_script = os.path.join(SCRIPTS, "fetch_asi_market_data.py")
        run_script(f'python "{fetch_script}"', "\u6570\u636e\u704c\u6ce8")
    elif args.layer:
        layer_script = os.path.join(SCRIPTS, "run_layer_batch.py")
        l_arg = "--l1 --l2 --l3 --l4"
        if args.skip_l5:
            l_arg += " --skip-l5"
        cmd = f'python "{layer_script}" --layer "{args.layer}" {l_arg}'
        run_script(cmd, f"\u5c42\u6279\u91cf: {args.layer}")
    
    # Step 3: Valuation
    if args.full:
        val_script = os.path.join(SCRIPTS, "enrich_asi_valuation.py")
        run_script(f'python "{val_script}"', "\u4f30\u503c\u5206\u6790")
    
    # Step 4: Guidance
    if args.full and not args.skip_l5:
        gui_script = os.path.join(SCRIPTS, "enrich_asi_guidance.py")
        run_script(f'python "{gui_script}"', "\u4e1a\u7ee9\u6307\u5f15")
    
    # Step 5: Pool classification
    if args.full:
        pool_script = os.path.join(SCRIPTS, "classify_asi_pools_v2.py")
        run_script(f'python "{pool_script}"', "\u6c60\u5b50\u5206\u7c7b")
    
    # Step 6: Index generation
    print("\n[Index Generation]")
    generate_pool_index()
    # Load pool results for company registry
    pool_files = sorted([f for f in os.listdir(RAW) if f.endswith(".csv") and "-asi-pool-" in f and f.startswith(TODAY)])
    print(f"\nDone in {time.time()-start_time:.0f}s")

if __name__ == "__main__":
    main()
