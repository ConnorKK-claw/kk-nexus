#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
006\u5458\u5de5 - \u5168\u91cf\u4e00\u7ad9\u5f0f\u8fd0\u884c\u811a\u672c
\u6309\u987a\u5e8f\u6267\u884c\u6570\u636e\u62c9\u53d6+\u4f30\u503c\u5206\u6790+\u4e1a\u7ee9\u6307\u5f15+\u6c60\u5b50\u5206\u7c7b
"""
import os, sys, subprocess, datetime
sys.stdout.reconfigure(encoding="utf-8")

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")

def run_step(script, label, args=None):
    """\u8fd0\u884c\u5355\u6b65\u811a\u672c"""
    path = os.path.join(SCRIPTS, script)
    cmd = [sys.executable, path]
    if args:
        cmd.extend(args)
    print(f"\n{'='*50}")
    print(f"Step: {label}")
    print(f"{path}")
    print(f"{'='*50}")
    print()
    result = subprocess.run(cmd, cwd=VAULT)
    if result.returncode != 0:
        print(f"\n[ERROR] Step '{label}' failed with code {result.returncode}")
        return False
    print(f"  OK")
    return True

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"006 Full Scan Pipeline - {today}")
    print(f"Scripts dir: {SCRIPTS}")

    steps = [
        ("fetch_asi_market_data.py", "1/4 \u5b9e\u65f6\u884c\u60c5+\u8d22\u52a1\u6570\u636e", ["--force"]),
        ("enrich_asi_valuation.py", "2/4 \u4f30\u503c\u6df1\u5ea6\u5206\u6790", ["--force"]),
        ("enrich_asi_guidance.py", "3/4 \u4e1a\u7ee9\u6307\u5f15\u786e\u5b9a\u6027", ["--force"]),
        ("classify_asi_pools_v2.py", "4/4 \u589e\u5f3a\u7248\u6c60\u5b50\u5206\u7c7b", []),
    ]

    for script, label, args in steps:
        ok = run_step(script, label, args)
        if not ok:
            print(f"\nPipeline aborted at: {label}")
            sys.exit(1)

    print(f"\n{'='*50}")
    print(f"Full pipeline complete! - {today}")
    print(f"Results in: vault/raw/agent/")
    print(f"Report in: vault/knowledge/")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
