import os, sys
sys.stdout.reconfigure(encoding="utf-8")

opath = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# Find 外服 entry and fix line by line
lines = c.split("\n")
current_company = None
for i, line in enumerate(lines):
    if '"company": "外服控股"' in line:
        current_company = "外服"
    if current_company == "外服":
        if '"employees_total":' in line:
            lines[i] = '        "employees_total": 2998, "incentive_count": 215, "incentive_pct": 7.17,'
            print(f"Fixed employees line {i}")
            current_company = None
            break

c = "\n".join(lines)
with open(opath, "w", encoding="utf-8") as f:
    f.write(c)

# Also fix grant_pct_total
with open(opath, "r", encoding="utf-8") as f:
    c = f.read()
lines = c.split("\n")
current_company = None
for i, line in enumerate(lines):
    if '"company": "外服控股"' in line:
        current_company = "外服"
    if current_company == "外服" and '"grant_pct_total":' in line:
        lines[i] = '        "grant_shares_wan": 2007.08, "grant_pct_total": 1.0,'
        print(f"Fixed grant line {i}")
        current_company = None
        break

c = "\n".join(lines)
with open(opath, "w", encoding="utf-8") as f:
    f.write(c)

print("Done!")