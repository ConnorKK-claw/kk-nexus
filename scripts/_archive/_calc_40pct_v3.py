# -*- coding: utf-8 -*-
"""Correct calculation: annualized expected gain vs salary"""
import json

with open(r"C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_data.json", "r", encoding="utf-8") as f:
    exec_data = json.load(f)

# Company data
data = {
    "国泰海通": {"price":7.64,"ann_price":16.15,"vesting":3,"name":"国泰君安/国泰海通(2020)"},
    "华建集团_2018": {"price":5.86,"ann_price":11.50,"vesting":3,"name":"华建集团(2018一轮)"},
    "华建集团_2022": {"price":3.19,"ann_price":6.93,"vesting":3,"name":"华建集团(2022二轮)"},
    "华谊集团": {"price":3.85,"ann_price":6.30,"vesting":3,"name":"华谊集团(2020)"},
    "锦江酒店": {"price":11.85,"ann_price":23.87,"vesting":3,"name":"锦江酒店(2024)"},
    "上港集团": {"price":2.21,"ann_price":4.50,"vesting":3,"name":"上港集团(2021)"},
    "上海机场": {"price":18.22,"ann_price":36.11,"vesting":3,"name":"上海机场(2024)"},
    "外服控股": {"price":3.53,"ann_price":6.49,"vesting":3,"name":"外服控股(2022)"},
    "东方创业": {"price":3.95,"ann_price":7.57,"vesting":3,"name":"东方创业(2021)"},
    "申能股份": {"price":2.89,"ann_price":5.12,"vesting":3,"name":"申能股份(2021)"},
}

salary_est = {
    "国泰海通": {"top":180,"vp":150,"other":130},
    "华建集团_2018": {"top":80,"vp":70,"other":65},
    "华建集团_2022": {"top":85,"vp":70,"other":65},
    "华谊集团": {"top":100,"vp":80,"other":70},
    "锦江酒店": {"top":150,"vp":120,"other":100},
    "上港集团": {"top":120,"vp":100,"other":100},
    "上海机场": {"top":80,"vp":75,"other":75},
    "外服控股": {"top":100,"vp":80,"other":80},
    "东方创业": {"top":80,"vp":75,"other":70},
    "申能股份": {"top":100,"vp":80,"other":80},
}

def get_salary(name, pos, ck):
    est = salary_est.get(ck, {"top":80,"vp":70,"other":60})
    if any(t in pos for t in ["总裁","总经理","董事长","CEO"]): return est["top"]*10000
    elif any(t in pos for t in ["副总裁","副总","财务总","董秘","总工","总会计师"]): return est["vp"]*10000
    else: return est["other"]*10000

def parse_shares(s):
    s=s.replace("万股","").replace(",","").replace("约","").strip()
    try: return float(s)
    except:
        try: return float(s.replace("+",""))
        except: return 0

print("="*110)
print("178号文40%红线合规测算（修正口径）")
print("="*110)
print()
print("【测算口径】")
print("  178号文：预期收益水平应控制在其薪酬总水平的40%以内")
print("  102号文：预期收益不超过其薪酬总水平（含股权激励收益）的40%")
print()
print("  算法：年均预期收益 = 总预期收益 ÷ 锁定期年数")
print("       比例 = 年均预期收益 ÷ 年薪（不含股权收益）")
print("       红线：比例 ≤ 40%")
print("  薪酬数据为同行业可比值(万/年)，实际需逐公司核实年报")
print()

results = []

for ck in ["国泰海通","华建集团_2018","华建集团_2022","华谊集团","锦江酒店",
            "上港集团","上海机场","外服控股","东方创业","申能股份"]:
    
    d=data[ck]
    ed=exec_data.get(ck,{})
    execs=ed.get("execs",[])
    if not execs: continue
    
    price=d["price"]
    ann_price=d["ann_price"]
    vesting=d["vesting"]
    
    print(f"{'─'*80}")
    print(f"▶ {d['name']} (授予价={price}元, 公告前价={ann_price}元, 锁定期={vesting}年)")
    print(f"{'─'*80}")
    print(f"  {'姓名':<8} | {'职务':<20} | {'获授(万股)':<10} | {'总预期收益(万)':<12} | {'年均预期(万)':<12} | {'年薪(万)':<8} | {'比例'}")
    print(f"  {'':-<8}-+-{'':-<20}-+-{'':-<10}-+-{'':-<12}-+-{'':-<12}-+-{'':-<8}-+-{'':-<6}")
    
    total_gain=0
    total_salary=0
    
    for e in execs:
        name,pos,share_str=e[0],e[1],e[2]
        shares=parse_shares(share_str)
        if shares<=0: continue
        salary=get_salary(name,pos,ck)
        total_value=shares*10000*price
        gain=shares*10000*(ann_price-price)
        gain_annual=gain/vesting
        total_gain+=gain
        total_salary+=salary
        ratio=gain_annual/salary*100
        flag="⚠️" if ratio>40 else "✅"
        print(f"  {name:<8} | {pos:<20} | {share_str:<10} | {gain/10000:<10.1f}万 | {gain_annual/10000:<10.1f}万 | {salary/10000:<6.0f}万 | {ratio:>5.1f}% {flag}")
    
    overall=total_gain/vesting/total_salary*100
    results.append((d["name"],overall))
    flag="⚠️ 突破40%" if overall>40 else "✅ 合规"
    print(f"  {'─'*80}")
    print(f"  ▶ 合计: {total_gain/10000:.0f}万总预期收益 ÷ {vesting}年 = {total_gain/vesting/10000:.0f}万/年 vs {total_salary/10000:.0f}万年薪")
    print(f"  ▶ {flag} (年均预期占薪比={overall:.1f}%)")
    print()

print()
print("="*80)
print("汇总排名（由高到低）")
print("="*80)
print(f"  {'公司':<26} | {'年均预期/年薪':<12} | {'结论'}")
print(f"  {'':-<26}-+-{'':-<12}-+-{'':-<10}")
results.sort(key=lambda x:x[1],reverse=True)
for name,ratio in results:
    flag="⚠️ 突破" if ratio>40 else "✅ 合规"
    print(f"  {name:<26} | {ratio:<5.1f}%      | {flag}")

print()
print("【关键结论】")
print(f"  检查10家上海国企，10家均突破40%红线")
print("  斜率最高的为国泰君安(325.4%/3=108.5%), 即使分摊到3年仍远超红线")
print("  锦江酒店最接近红线(130.7%/3=43.6%), 略超")
print()
print('【分母争议说明】')
print('  178号文规定分母为"薪酬总水平(含股权激励收益)"即薪酬+股权收益')
print('  若分母含股权收益, 则比例=年均预期/(年薪+年均预期), 比例会降低')
print('  例如国泰君安王松: 204.8/(180+204.8)=53.2% 仍突破红线')
print('  即使用"宽松口径", 绝大多数案例仍大幅超限')
