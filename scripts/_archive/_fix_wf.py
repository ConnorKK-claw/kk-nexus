import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6"
opath = os.path.join(wrk, "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# Fix 外服控股 data in COMPANIES list
# employees_total: 2998, incentive_pct: 7.17, grant_pct_total: 1.0, draft_date: (2022年)
# perf_targets: 外服 specific

# Fix employees_total
old = '"company": "外服控股",\n        "code": "600662.SH",\n        "plan_year": "2022", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "定向增发",\n        "draft_date": "未收录（2022年）",\n        "grant_date": "2022-03-16", "grant_price": 3.53,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",\n        "validity": "最长不超过6年",\n        "status": "首批+第二批均已解锁上市",\n        "employees_total": "未收录", "incentive_count": 215, "incentive_pct": "未收录",\n        "grant_shares_wan": 2007.08, "grant_pct_total": "未收录",'

new = '"company": "外服控股",\n        "code": "600662.SH",\n        "plan_year": "2022", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "定向增发",\n        "draft_date": "（2022年）",\n        "grant_date": "2022-03-16", "grant_price": 3.53,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",\n        "validity": "最长不超过6年",\n        "status": "首批+第二批均已解锁上市",\n        "employees_total": 2998, "incentive_count": 215, "incentive_pct": 7.17,\n        "grant_shares_wan": 2007.08, "grant_pct_total": 1.0,'

if old in c:
    c = c.replace(old, new)
    print("Fixed 外服控股 employees/pct/grant data")

# Fix perf_targets
old2 = '"perf_targets": "（待补充）",'
new2 = '"perf_targets": "EPS>=0.230/0.253/0.290元; 营收增长>=33%/52.9%/75.9%(较2020)+国际对标75分位; 新兴业务收入>=100.60/116.70/135.37亿",'
if old2 in c:
    c = c.replace(old2, new2)
    print("Fixed 外服控股 perf_targets")
else:
    print("old2 not found, searching for alternatives...")
    # search for 外服 perf line
    lines = c.split("\n")
    in_wf = False
    for i, line in enumerate(lines):
        if '"company": "外服控股"' in line:
            in_wf = True
        if in_wf and 'perf_targets' in line:
            print(f"Found at line {i}: {line.strip()}")
            break

with open(opath, "w", encoding="utf-8") as f:
    f.write(c)

print("Done!")