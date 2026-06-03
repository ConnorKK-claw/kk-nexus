# -*- coding: utf-8 -*-
"""Refined calculation: expected gain vs salary for 40% limit"""
import json

with open(r"C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_data.json", "r", encoding="utf-8") as f:
    exec_data = json.load(f)

# Grant prices and current floating rates from comparison report
data = {
    "国泰海通": {"price": 7.64, "floating": 102.1, "announce_price": 16.15},
    "华建集团_2018": {"price": 5.86, "floating": 243.0, "announce_price": 11.50},
    "华建集团_2022": {"price": 3.19, "floating": 530.1, "announce_price": 6.93},
    "华谊集团": {"price": 3.85, "floating": 149.4, "announce_price": 6.30},
    "锦江酒店": {"price": 11.85, "floating": 89.9, "announce_price": 23.87},
    "上港集团": {"price": 2.21, "floating": 130.8, "announce_price": 4.50},
    "上海机场": {"price": 18.22, "floating": 43.1, "announce_price": 36.11},
    "外服控股": {"price": 3.53, "floating": 36.5, "announce_price": 6.49},
    "东方创业": {"price": 3.95, "floating": 78.5, "announce_price": 7.57},
    "申能股份": {"price": 2.89, "floating": 228.7, "announce_price": 5.12},
}

# Salary estimates (万/年)
salary_est = {
    "国泰海通": {"top": 180, "vp": 150, "other": 130},
    "华建集团_2018": {"top": 80, "vp": 70, "other": 65},
    "华建集团_2022": {"top": 85, "vp": 70, "other": 65},
    "华谊集团": {"top": 100, "vp": 80, "other": 70},
    "锦江酒店": {"top": 150, "vp": 120, "other": 100},
    "上港集团": {"top": 120, "vp": 100, "other": 100},
    "上海机场": {"top": 80, "vp": 75, "other": 75},
    "外服控股": {"top": 100, "vp": 80, "other": 80},
    "东方创业": {"top": 80, "vp": 75, "other": 70},
    "申能股份": {"top": 100, "vp": 80, "other": 80},
}

def get_salary(name, pos, company_key):
    """Get estimated salary for an executive"""
    est = salary_est.get(company_key, {"top": 80, "vp": 70, "other": 60})
    if any(t in pos for t in ["总裁","总经理","董事长","CEO"]):
        return est["top"] * 10000
    elif any(t in pos for t in ["副总裁","副总","财务总监","董秘","总工","总会计师"]):
        return est["vp"] * 10000
    else:
        return est["other"] * 10000

def parse_shares(s):
    s = s.replace("万股","").replace(",","").replace("约","").strip()
    try: return float(s)
    except:
        try: return float(s.replace("+",""))
        except: return 0

print("=" * 120)
print("上海国企股权激励178号文40%红线合规测算")
print("=" * 120)
print()
print("【测算方法】")
print("  - 预期收益 = 获授股数 × (授予日市价 - 授予价格)")
print("    即假设授予日即为预期收益基准")
print("  - 薪酬总水平 = 年薪（不含股权收益）—— 保守口径")
print("  - 40%红线：预期收益 / 年薪 ≤ 40%")
print("  - 薪酬数据取自可比年度报告公开数据（近似值，实际需精确核查）")
print()

results_summary = []

for ck in ["国泰海通", "华建集团_2018", "华建集团_2022", "华谊集团", 
            "锦江酒店", "上港集团", "上海机场", "外服控股", 
            "东方创业", "申能股份"]:
    
    d = data[ck]
    ed = exec_data.get(ck, {})
    execs = ed.get("execs", [])
    price = d["price"]
    ann_price = d["announce_price"]
    
    if not execs:
        continue
    
    print(f"\n{'─'*80}")
    print(f"▶ {ck}")
    print(f"   授予价={price}元/股, 公告前收盘价={ann_price}元/股, 授予日浮盈率={d["floating"]}%")
    print(f"{'─'*80}")
    print(f"  {'姓名':<8} | {'职务':<22} | {'获授(万股)':<10} | {'授予市值(万)':<10} | {'预期收益(万)':<10} | {'年薪(万)':<8} | {'收益/年薪':<8}")
    print(f"  {'':-<8}-+-{'':-<22}-+-{'':-<10}-+-{'':-<10}-+-{'':-<10}-+-{'':-<8}-+-{'':-<8}")
    
    total_gain = 0
    total_salary = 0
    
    for e in execs:
        name, pos, share_str = e[0], e[1], e[2]
        shares = parse_shares(share_str)
        if shares <= 0:
            continue
        salary = get_salary(name, pos, ck)
        market_value = shares * 10000 * price  # 授予市值
        gain = shares * 10000 * (ann_price - price)  # 预期收益（按公告前价）
        if gain < 0:
            gain = 0  # 折价授予不会亏
        ratio = gain / salary * 100
        total_gain += gain
        total_salary += salary
        flag = "⚠️" if ratio > 40 else "✅"
        print(f"  {name:<8} | {pos:<22} | {share_str:<10} | {market_value/10000:<8.1f}万 | {gain/10000:<8.1f}万 | {salary/10000:<6.0f}万 | {ratio:<5.1f}% {flag}")
    
    
    overall = total_gain / total_salary * 100 if total_salary > 0 else 0
    results_summary.append((ck, overall, total_gain, total_salary))
    flag = "⚠️ 突破" if overall > 40 else "✅ 合规"
    print(f"  {'─'*80}")
    print(f"  ▶ 高管合计: {total_gain/10000:.1f}万预期收益 vs {total_salary/10000:.0f}万年薪")
    print(f"  ▶ 整体比例: {overall:.1f}%  {flag}")

print()
print("=" * 80)
print("汇总：40%红线检查结果")
print("=" * 80)
print(f"  {'公司':<22} | {'预期收益/年薪':<12} | {'结果':<10}")
print(f"  {'':-<22}-+-{'':-<12}-+-{'':-<10}")
results_summary.sort(key=lambda x: x[1], reverse=True)
for ck, ratio, gain, sal in results_summary:
    flag = "⚠️ 突破" if ratio > 40 else "✅ 合规"
    print(f"  {ck:<22} | {ratio:<6.1f}%      | {flag}")

print()
print("【重要说明】")
print("  1. 薪酬数据为同行业可比公开数据近似值，实际需逐公司核查年报披露数")
print("  2. 证券公司薪酬普遍高于实业企业，故40%限制对券商影响更大")
print("  3. 预期收益按公告前收盘价-授予价计算，实际行权时收益可能更高或更低")
print("  4. 178号文分母=薪酬总水平（含股权收益）或(不含)存在争议，此处按保守口径(不含)计算")
print("  5. 上海建科因无按姓名列示数据，未纳入测算")
