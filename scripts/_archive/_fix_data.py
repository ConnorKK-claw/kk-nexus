# -*- coding: utf-8 -*-
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8")

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6"
opath = os.path.join(wrk, "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# ---- Fix 1: stock_source values ----
# Define each company id and its correct stock_source
fixes = {
    # id: (company_key, correct_source)
    # We'll use regex on company name patterns
}

# Strategy: split by company entries and fix each
# Each entry starts with "{\n        "id": N,
parts = c.split('"id":')
# Rejoin with proper fixes
new_parts = [parts[0]]  # header before first company
for i in range(1, len(parts)):
    entry = '"id":' + parts[i]
    # Extract company name
    m = re.search(r'"company": "(.+?)"', entry)
    if m:
        co = m.group(1)
        # Determine correct stock source
        if co in ["上港集团", "华谊集团", "外服控股"]:
            entry = re.sub(r'"stock_source": "[^"]+"', '"stock_source": "定向增发"', entry)
        elif co == "华建集团":
            entry = re.sub(r'"stock_source": "[^"]+"', '"stock_source": "定向增发"', entry)
        elif co == "赢合科技":
            # Check plan_year
            if '"plan_year": "2017"' in entry:
                entry = re.sub(r'"stock_source": "[^"]+"', '"stock_source": "定向增发"', entry)
            else:
                entry = re.sub(r'"stock_source": "[^"]+"', '"stock_source": "二级市场回购"', entry)
        else:
            entry = re.sub(r'"stock_source": "[^"]+"', '"stock_source": "二级市场回购"', entry)
    new_parts.append(entry)

c = "".join(new_parts)

# ---- Fix 2: incentive_pct values ----
# Some got set to 1.59 incorrectly (from 上港's value)
# Fix them back
pct_fixes = {
    '"company": "上海建科"': ('"incentive_pct": 1.59,', '"incentive_pct": "未收录",'),
    '"company": "东方创业"': ('"incentive_pct": 1.59,', '"incentive_pct": "未收录",'),
    '"company": "国泰君安"': ('"incentive_pct": 1.59,', '"incentive_pct": 2.96,'),
    '"company": "华建集团"': ('"incentive_pct": 1.59,', '"incentive_pct": "未收录",'),  # 2018
    '"company": "华谊集团"': ('"incentive_pct": 1.59,', '"incentive_pct": "未收录",'),
    '"company": "外服控股"': ('"incentive_pct": 1.59,', '"incentive_pct": "未收录",'),
    '"company": "赢合科技"': ('"incentive_pct": 1.59,', '"incentive_pct": "未收录",'),
}
# Apply pct fixes by finding the right entry context
for co_key, (old_val, new_val) in pct_fixes.items():
    if co_key in c and old_val in c:
        c = c.replace(old_val, new_val)
        print(f"  Fixed incentive_pct for {co_key}")

# ---- Fix 3: employees_total that got corrupted ----
pct_fixes = {
    '"company": "东方创业"': ('"employees_total": 1.59,', '"employees_total": "未收录",'),
    '"company": "华建集团"': ('"employees_total": 1.59,', '"employees_total": "未收录",'),  # 2018
    '"company": "华谊集团"': ('"employees_total": 1.59,', '"employees_total": "未收录",'),
    '"company": "外服控股"': ('"employees_total": 1.59,', '"employees_total": "未收录",'),
    '"company": "赢合科技"': ('"employees_total": 1.59,', '"employees_total": "未收录",'),
}
for co_key, (old_val, new_val) in pct_fixes.items():
    if co_key in c and old_val in c:
        c = c.replace(old_val, new_val)
        print(f"  Fixed employees_total for {co_key}")

# ---- Fix 4: grant_pct_total that got corrupted to 2.02 ----
pct_fixes = {
    '"company": "华谊集团"': ('"grant_pct_total": 2.02,', '"grant_pct_total": "未收录",'),
    '"company": "外服控股"': ('"grant_pct_total": 2.02,', '"grant_pct_total": "未收录",'),
    '"company": "赢合科技"': ('"grant_pct_total": 2.02,', '"grant_pct_total": "未收录",'),  # 2022
}
for co_key, (old_val, new_val) in pct_fixes.items():
    if co_key in c and old_val in c:
        c = c.replace(old_val, new_val)
        print(f"  Fixed grant_pct_total for {co_key}")

# ---- Fix 5: 华建集团2022 get its correct employees_total ----
# Match the second 华建 entry (2022 round)
if c.count('"company": "华建集团"') > 1:
    # Find the second occurrence and its employees_total
    idx = c.find('"company": "华建集团"')
    idx2 = c.find('"company": "华建集团"', idx + 10)
    # Find employees_total in second entry
    sub = c[idx2:idx2+300]
    m = re.search(r'"employees_total": "[^"]+"', sub)
    if m and m.group(0) == '"employees_total": "未收录"':
        c = c[:idx2] + c[idx2:].replace('"employees_total": "未收录"', '"employees_total": 8350', 1)
        print("  Fixed 华建2022 employees_total")

# ---- Fix 6: 上港集团 employees_total ----
old_emp = '"employees_total": 1.59,'
new_emp = '"employees_total": 13796,'
if old_emp in c:
    c = c.replace(old_emp, new_emp)
    print("  Fixed 上港 employees_total")

# ---- Fix 7: 华建2022 incentive_pct ----
# The second 华建 entry's incentive_pct should be 1.22
idx = c.find('"company": "华建集团"')
idx2 = c.find('"company": "华建集团"', idx + 10)
sub = c[idx2:idx2+300]
# Check if incentive_pct has 未收录 (most likely)
m = re.search(r'"incentive_pct": "[^"]+"', sub)
if m:
    c = c[:idx2] + c[idx2:].replace(m.group(0), '"incentive_pct": 1.22', 1)
    print(f"  Fixed 华建2022 incentive_pct")

# ---- Write back ----
with open(opath, "w", encoding="utf-8") as f:
    f.write(c)

# ---- Verify ----
print("\nVerify:")
for kw in ["二级市场回购", "定向增发"]:
    print(f"  {kw}: {c.count(kw)}")

print("Done!")