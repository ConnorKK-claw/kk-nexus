# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8")

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6"

# 1. Copy updated case files to vault
src_dir = os.path.join(wrk, "updated_cases")
dst_dir = os.path.join(os.environ["USERPROFILE"], ".codex", "skills", "equity-incentive", "vault", "cases")

files = [
    "2026-05-17-东方创业-限制性股票激励计划-case.md",
    "2026-05-17-国泰君安-限制性股票激励计划-case.md",
    "2026-05-17-华建集团-限制性股票激励计划-case.md",
    "2026-05-17-华谊集团-限制性股票激励计划-case.md",
    "2026-05-17-上港集团-限制性股票激励计划-case.md",
    "2026-05-17-外服控股-限制性股票激励计划-case.md",
]

for f in files:
    src = os.path.join(src_dir, f)
    dst = os.path.join(dst_dir, f)
    if os.path.exists(src):
        c = open(src, "r", encoding="utf-8").read()
        open(dst, "w", encoding="utf-8").write(c)
        print(f"OK: {f}")
    else:
        print(f"SKIP (not found): {f}")

# 2. Copy report to vault knowledge
report_src = os.path.join(wrk, "zk-ei-bb0-0-11-cases-comparison-report.md")
report_dst = os.path.join(os.environ["USERPROFILE"], ".codex", "skills", "equity-incentive", "vault", "knowledge", "zk-ei-bb0-0-11-cases-comparison-report.md")
if os.path.exists(report_src):
    c = open(report_src, "r", encoding="utf-8").read()
    open(report_dst, "w", encoding="utf-8").write(c)
    print(f"OK: report copied")

# 3. Run build_index
os.system(f'python \"{os.path.join(wrk, \"scripts\", \"build_index.py\")}\" \"{os.path.join(os.environ[\"USERPROFILE\"], \".codex\", \"skills\", \"equity-incentive\", \"vault\")}\"')

print("Done!")