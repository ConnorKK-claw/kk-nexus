import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
cases_dir = Path(r"C:\Users\hexk\.codex\skills\equity-incentive\vault\cases")

# Extract key data from each case file
data = {
    "上海建科": {"price": 11.50, "shares_plan": 6124910, "people_plan": 219, "shares_actual": 6080937, "people_actual": 198, "note": "实际比计划少21人"},
    "东方创业": {"price": 3.95, "shares_plan": 15773000, "people_plan": 275, "shares_actual": 15068000, "people_actual": 275, "note": ""},
    "国泰君安": {"price": 7.64, "shares_plan": 81593000, "people_plan": 451, "shares_actual": 79000000, "people_actual": 440, "note": ""},
    "华建集团(2018)": {"price": 5.86, "shares_plan": 12966200, "people_plan": 379, "shares_actual": 12919400, "people_actual": 339, "note": ""},
    "华建集团(2022)": {"price": 3.19, "shares_plan": 22406800, "people_plan": 102, "shares_actual": 21731800, "people_actual": 99, "note": ""},
    "华谊集团": {"price": 3.85, "shares_plan": 25271200, "people_plan": 284, "shares_actual": 25084600, "people_actual": 284, "note": ""},
    "锦江酒店": {"price": 11.85, "shares_plan": 6477000, "people_plan": 148, "shares_actual": 6477000, "people_actual": 142, "note": "首次授予;预留84.54万股/108人@11.15元"},
    "上港集团": {"price": 2.212, "shares_plan": 114146500, "people_plan": 220, "shares_actual": 105005100, "people_actual": 209, "note": "首次授予;预留546.5万股/28人@3.10元(实际)"},
    "上海机场": {"price": 18.21966, "shares_plan": 8262500, "people_plan": 289, "shares_actual": 8262500, "people_actual": 289, "note": ""},
    "外服控股": {"price": 3.53, "shares_plan": 20070800, "people_plan": 215, "shares_actual": 20070800, "people_actual": 215, "note": "首次授予;预留90.29万股/16人@3.33元"},
    "赢合科技(2017)": {"price": 17.05, "shares_plan": 6280000, "people_plan": 83, "shares_actual": 4885000, "people_actual": 73, "note": "预留100万股/2人"},
    "赢合科技(2022)": {"price": 10.68, "shares_plan": 7382185, "people_plan": 411, "shares_actual": 3465900, "people_actual": 168, "note": "认购缩水53%"},
    "申能股份": {"price": 2.89, "shares_plan": 46228000, "people_plan": 289, "shares_actual": 44024000, "people_actual": 289, "note": "首次授予;预留78.3万股/2人@3.48元(实际)"},
    "上海电气": {"price": 3.03, "shares_plan": 147251800, "people_plan": 2500, "shares_actual": 133578000, "people_actual": 2194, "note": "后全部终止回购"},
}

print(f"{'#':<2} {'公司':<16} {'授予价':>6} {'计划总股数(万)':>14} {'计划人数':>8} {'计划总额(万)':>12} {'计划人均(万)':>12} {'实际总额(万)':>12} {'实际人均(万)':>12} {'备注':<20}")
print("-"*114)

total_plan_amount = 0
total_plan_people = 0

for i, (name, d) in enumerate(data.items(), 1):
    pa = d["price"] * d["shares_plan"] / 10000  # 计划总额(万元)
    pp = pa / d["people_plan"] if d["people_plan"] > 0 else 0
    aa = d["price"] * d["shares_actual"] / 10000
    ap = aa / d["people_actual"] if d["people_actual"] > 0 else 0
    
    total_plan_amount += pa
    total_plan_people += d["people_plan"]
    
    print(f"{i:<2} {name:<16} {d['price']:>6.2f} {d['shares_plan']/10000:>12.2f} {d['people_plan']:>8} {pa:>10.0f} {pp:>10.1f} {aa:>10.0f} {ap:>10.1f} {d['note']:<20}")

print("-"*114)
plan_avg = total_plan_amount / total_plan_people if total_plan_people > 0 else 0
print(f"{'合计(计划)':<24} {'':>6} {'':>14} {total_plan_people:>8} {total_plan_amount:>10.0f} {plan_avg:>10.1f}")
