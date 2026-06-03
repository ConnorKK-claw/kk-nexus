import os, sys
sys.stdout.reconfigure(encoding="utf-8")

opath = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# Fix the 外服 entry - restore per_person_wan
old = '"grant_shares_wan": 2007.08, "grant_pct_total": 1.0,'
new = '"grant_shares_wan": 2007.08, "grant_pct_total": 1.0, "per_person_wan": 9.34,'

if old in c:
    c = c.replace(old, new)
    print("Fixed - restored per_person_wan")

with open(opath, "w", encoding="utf-8") as f:
    f.write(c)