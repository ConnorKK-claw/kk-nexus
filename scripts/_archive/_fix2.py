import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

opath = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# Fix: restore unlock_schedule to correct values
# 华谊 should be 40/30/30
c = c.replace(
    '"company": "华谊集团",\n        "code": "600623.SH",\n        "plan_year": "2020", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "定向增发",\n        "draft_date": "（2020年草案，2024年修订稿）",\n        "grant_date": "2020-12-16", "grant_price": 3.85,\n        "lockup_period": "36个月",\n        "unlock_schedule": "33% / 33% / 34%",',
    '"company": "华谊集团",\n        "code": "600623.SH",\n        "plan_year": "2020", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "定向增发",\n        "draft_date": "（2020年草案，2024年修订稿）",\n        "grant_date": "2020-12-16", "grant_price": 3.85,\n        "lockup_period": "36个月",\n        "unlock_schedule": "40% / 30% / 30%",'
)

# 上港 should be 40/30/30
c = c.replace(
    '"company": "上港集团",\n        "code": "600018.SH",\n        "plan_year": "2021", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "定向增发",\n        "draft_date": "2021-04-24",\n        "grant_date": "2021-07-16", "grant_price": 2.212,\n        "lockup_period": "36个月",\n        "unlock_schedule": "33% / 33% / 34%",',
    '"company": "上港集团",\n        "code": "600018.SH",\n        "plan_year": "2021", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "定向增发",\n        "draft_date": "2021-04-24",\n        "grant_date": "2021-07-16", "grant_price": 2.212,\n        "lockup_period": "36个月",\n        "unlock_schedule": "40% / 30% / 30%",'
)

# 上海机场 should be 40/30/30
c = c.replace(
    '"company": "上海机场",\n        "code": "600009.SH",\n        "plan_year": "2024", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "2024-05-14",\n        "grant_date": "2024-09-12", "grant_price": 18.21966,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",',
    '"company": "上海机场",\n        "code": "600009.SH",\n        "plan_year": "2024", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "2024-05-14",\n        "grant_date": "2024-09-12", "grant_price": 18.21966,\n        "lockup_period": "24个月",\n        "unlock_schedule": "40% / 30% / 30%",'
)

# 上海建科 should be 40/30/30
c = c.replace(
    '"company": "上海建科",\n        "code": "603153.SH",\n        "plan_year": "2025", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "2025-12-16",\n        "grant_date": "2026-02-09", "grant_price": 11.50,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",',
    '"company": "上海建科",\n        "code": "603153.SH",\n        "plan_year": "2025", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "2025-12-16",\n        "grant_date": "2026-02-09", "grant_price": 11.50,\n        "lockup_period": "24个月",\n        "unlock_schedule": "40% / 30% / 30%",'
)

# Fix perf_targets - restore correct values for each company
# 国泰君安 perf
c = c.replace(
    '"company": "国泰君安/国泰海通",\n        "code": "601211.SH",\n        "plan_year": "2020", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "（2020年7月）",\n        "grant_date": "2020-09-17", "grant_price": 7.64,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",\n        "validity": "未收录",\n        "status": "全生命周期已完成（首次+预留共4批全部解锁）",\n        "employees_total": 15233, "incentive_count": 451, "incentive_pct": 2.96,\n        "grant_shares_wan": 8159.3, "grant_pct_total": "未收录", "per_person_wan": 18.09,\n        "exec_get_pct": "未收录",\n        "unlock_structure": "33%/33%/34%",\n        "perf_targets": "EPS>=0.31/0.33/0.35元; 净利增长>=57%/65%/75%(较2018-2020均值); 东松公司净利>=12,800/13,000/14,000万",',
    '"company": "国泰君安/国泰海通",\n        "code": "601211.SH",\n        "plan_year": "2020", "round": "",\n        "incentive_type": "限制性股票（第一类）",\n        "stock_source": "二级市场回购",\n        "draft_date": "（2020年7月）",\n        "grant_date": "2020-09-17", "grant_price": 7.64,\n        "lockup_period": "24个月",\n        "unlock_schedule": "33% / 33% / 34%",\n        "validity": "未收录",\n        "status": "全生命周期已完成（首次+预留共4批全部解锁）",\n        "employees_total": 15233, "incentive_count": 451, "incentive_pct": 2.96,\n        "grant_shares_wan": 8159.3, "grant_pct_total": "未收录", "per_person_wan": 18.09,\n        "exec_get_pct": "未收录",\n        "unlock_structure": "33%/33%/34%",\n        "perf_targets": "综合风控(门槛)+归母净利润排名+ROE排名+金融科技投入>=5%",'
)

# 华建2018 perf
# Already has wrong value from东方创业. Need to find exact block.
# 华建2018 is the 4th entry (id:4)
# 华建2022 is the 5th entry (id:5)

with open(opath, "w", encoding="utf-8") as f:
    f.write(c)
print("Applied unlock_schedule and selected perf_targets fixes")

# Verify
with open(opath, "r", encoding="utf-8") as f:
    c2 = f.read()
print(f"40/30/30 count: {c2.count('40% / 30% / 30%')}")
print(f"33/33/34 count: {c2.count('33% / 33% / 34%')}")