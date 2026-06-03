import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

opath = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# Fix grant_pct_total for 东方创业 (should be 2.02)
c = c.replace(
    '"company": "东方创业",\n        "code": "600278.SH",\n        "plan_year": "2021", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "2021-11-30",\n        "grant_date": "2021-12-31", "grant_price": 3.95,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",\n        "validity": "最长约6年",\n        "status": "首批已解锁（首次+预留）",\n        "employees_total": "未收录", "incentive_count": 275, "incentive_pct": "未收录",\n        "grant_shares_wan": 1577.3, "grant_pct_total": "未收录",',
    '"company": "东方创业",\n        "code": "600278.SH",\n        "plan_year": "2021", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "2021-11-30",\n        "grant_date": "2021-12-31", "grant_price": 3.95,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",\n        "validity": "最长约6年",\n        "status": "首批已解锁（首次+预留）",\n        "employees_total": "未收录", "incentive_count": 275, "incentive_pct": "未收录",\n        "grant_shares_wan": 1577.3, "grant_pct_total": 2.02,'
)

# Fix 上港 incentive_pct
c = c.replace(
    '"incentive_count": 220, "incentive_pct": "未收录",',
    '"incentive_count": 220, "incentive_pct": 1.59,'
)

# Fix 东方创业 unlock_structure (was still "40%/30%/30%" in some places)
c = c.replace(
    '"unlock_structure": "40%/30%/30%",',
    '"unlock_structure": "33%/33%/34%",'
)

# Fix 国泰君安 per_person_wan divisor - 8159.3/451 = 18.09, verify
# Looks correct, keep it

# Fix 华谊集团 draft_date to not show 2024-07-02 (that was revision, not original)
c = c.replace(
    '"draft_date": "2020年->2024-07-02（修订稿）",',
    '"draft_date": "（2020年草案，2024年修订稿）",'
)

with open(opath, "w", encoding="utf-8") as f:
    f.write(c)
print("Final fixes applied!")