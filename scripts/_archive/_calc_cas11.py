# -*- coding: utf-8 -*-
"""
40%红线正确测算：基于CAS 11股份支付准则

核心逻辑：
1. CAS 11规定限制性股票在等待期内分期摊销确认股份支付费用
2. 高管个人年度"股权激励报酬" = 分摊到当年的股份支付费用
3. 年报"报酬总额"包含：基本工资+奖金+津贴+股权激励报酬(当年摊销额)
4. 178号文分母="薪酬总水平(含股权激励收益)" = 年薪(不含股权)+当年股权激励摊销额
5. 分子应该也是同口径的"预期收益"(=当年摊销的股份支付费用)

所以如果分子和分母口径一致:
  比例 = 股权激励摊销额 / (年薪+股权激励摊销额) <= 40%
  即 股权激励摊销额 <= 年薪×(0.4/0.6) = 66.7% × 年薪

对于分三批解锁的股权激励:
  授予日公允价值 = 授予日市价(实务中常用内在价值法=市价-授予价)
  每批等待期不同: 第一批24个月,第二批36个月,第三批48个月
  第一年摊销 = 40%×总收益×(12/24)+30%×总收益×(12/36)+30%×总收益×(12/48)
              = 总收益×(20%+10%+7.5%) = 总收益×37.5%
"""
import json

with open(r"C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_data.json","r",encoding="utf-8") as f:
    exec_data = json.load(f)

# For this calculation we use:
# 授予日公允价值(每股) = 公告前收盘价 - 授予价  (内在价值法)
# 总预期收益 = 股数 × 每股公允价值
# 第1年摊销 = 分批按等待期分摊
data = {
    "国泰海通":{"p":7.64,"mp":16.15,"name":"国泰君安/国泰海通(2020)"},
    "华建集团_2018":{"p":5.86,"mp":11.50,"name":"华建集团(2018一轮)"},
    "华建集团_2022":{"p":3.19,"mp":6.93,"name":"华建集团(2022二轮)"},
    "华谊集团":{"p":3.85,"mp":6.30,"name":"华谊集团(2020)"},
    "锦江酒店":{"p":11.85,"mp":23.87,"name":"锦江酒店(2024)"},
    "上港集团":{"p":2.21,"mp":4.50,"name":"上港集团(2021)"},
    "上海机场":{"p":18.22,"mp":36.11,"name":"上海机场(2024)"},
    "外服控股":{"p":3.53,"mp":6.49,"name":"外服控股(2022)"},
    "东方创业":{"p":3.95,"mp":7.57,"name":"东方创业(2021)"},
    "申能股份":{"p":2.89,"mp":5.12,"name":"申能股份(2021)"},
}

# 分批解锁结构 (大部分是33/33/34或40/30/30, 等待期一般为24/36/48个月)
vesting_schedule = {
    "国泰海通":{"batches":[0.33,0.33,0.34],"waits":[24,36,48]},
    "华建集团_2018":{"batches":[0.333,0.333,0.334],"waits":[24,36,48]},
    "华建集团_2022":{"batches":[0.333,0.333,0.334],"waits":[24,36,48]},
    "华谊集团":{"batches":[0.40,0.30,0.30],"waits":[36,48,60]},  # 36个月锁定期
    "锦江酒店":{"batches":[0.40,0.30,0.30],"waits":[24,36,48]},
    "上港集团":{"batches":[0.40,0.30,0.30],"waits":[36,48,60]},  # 36个月锁定期
    "上海机场":{"batches":[0.40,0.30,0.30],"waits":[24,36,48]},
    "外服控股":{"batches":[0.33,0.33,0.34],"waits":[24,36,48]},
    "东方创业":{"batches":[0.33,0.33,0.34],"waits":[24,36,48]},
    "申能股份":{"batches":[0.33,0.33,0.34],"waits":[24,36,48]},  # 但首批被取消了
}

salary_est = {
    "国泰海通":{"t":180,"v":150,"o":130},
    "华建集团_2018":{"t":80,"v":70,"o":65},
    "华建集团_2022":{"t":85,"v":70,"o":65},
    "华谊集团":{"t":100,"v":80,"o":70},
    "锦江酒店":{"t":150,"v":120,"o":100},
    "上港集团":{"t":120,"v":100,"o":100},
    "上海机场":{"t":80,"v":75,"o":75},
    "外服控股":{"t":100,"v":80,"o":80},
    "东方创业":{"t":80,"v":75,"o":70},
    "申能股份":{"t":100,"v":80,"o":80},
}

def gs(n,pos,ck):
    e=salary_est.get(ck,{"t":80,"v":70,"o":60})
    if any(t in pos for t in ["总裁","总经理","董事长","CEO"]): return e["t"]
    if any(t in pos for t in ["副总裁","副总","财务总","董秘","总工"]): return e["v"]
    return e["o"]

def ps(s):
    s=s.replace("万股","").replace(",","").replace("约","").strip()
    try: return float(s)
    except:
        try: return float(s.replace("+",""))
        except: return 0

def calc_first_year_amort(total_fair_value, batches, waits):
    """计算第1年摊销的股份支付费用"""
    amort = 0
    for b, w in zip(batches, waits):
        amort += total_fair_value * b * (12/w)
    return amort

print("="*120)
print("40%红线正确测算（CA S11股份支付口径）")
print("="*120)
print()
print("【口径说明】")
print("  - CAS 11: 限制性股票公允价值(每股)=授予日市价-授予价 (内在价值法)")
print("  - 总预期收益(公允价值) = 股数 × 每股公允价值")
print("  - 第1年摊销股权激励报酬 = 各批次按等待期比例分摊之和")
print("  - 分母(薪酬总水平) = 年薪(不含股权) + 第1年摊销的股权激励报酬")
print("  - 178号文要求: 股权激励报酬 / 薪酬总水平(含股权) ≤ 40%")
print()

results = []

for ck in ["国泰海通","华建集团_2018","华建集团_2022","华谊集团","锦江酒店",
            "上港集团","上海机场","外服控股","东方创业","申能股份"]:
    
    d=data[ck]
    vs=vesting_schedule[ck]
    ed=exec_data.get(ck,{})
    execs=ed.get("execs",[])
    if not execs: continue
    
    fv_per_share = d["mp"] - d["p"]  # 每股公允价值(内在价值法)
    print(f"{'─'*90}")
    print(f"▶ {d['name']}（授予价={d['p']}, 市价={d['mp']}, 每股公允价值={fv_per_share:.2f}）")
    print(f"  等待期: {vs['batches']} 分 {vs['waits']}个月解锁")
    print(f"  第1年摊销系数: ", end="")
    coeff = sum(vs['batches'][i] * (12/vs['waits'][i]) for i in range(3))
    print(f"{coeff*100:.1f}%（即总公允价值的{coeff*100:.1f}%在第1年确认）")
    print(f"{'─'*90}")
    
    tv=0  # total fair value
    ta=0  # total year 1 amort
    ts=0  # total salary
    
    for e in execs:
        n,p,ss=e[0],e[1],e[2]
        sh=ps(ss)
        if sh<=0: continue
        
        total_fv = sh*10000*fv_per_share  # 总公允价(预期收益)
        yr1_amort = calc_first_year_amort(total_fv, vs['batches'], vs['waits'])
        salary_wan = gs(n,p,ck)
        salary_total = salary_wan*10000
        denominator = salary_total + yr1_amort
        ratio = yr1_amort / denominator * 100
        
        tv += total_fv
        ta += yr1_amort
        ts += salary_total
        
        flag = "⚠️" if ratio > 40 else "✅"
        yr1_wan = yr1_amort/10000
        print(f"  {flag} {n:<8} {p:<16} 获授{ss:<10} "
              f"公允总价{total_fv/10000:>6.1f}万 | 第1年摊销{yr1_wan:>5.1f}万 | "
              f"年薪{salary_wan:>3.0f}万+股权{yr1_wan:>4.1f}万={salary_wan+yr1_wan:>4.1f}万 | 占比{ratio:>4.1f}%")
    
    
    total_denom = ts + ta
    overall = ta / total_denom * 100
    flag = "⚠️ 突破" if overall > 40 else "✅ 合规"
    results.append((d["name"], overall))
    print(f"  {'─'*90}")
    print(f"  ▶ 合计: 年薪{ts/10000:.0f}万+股权摊销{ta/10000:.0f}万={total_denom/10000:.0f}万 | {flag} (占比{overall:.1f}%)")
    print()

print("="*70)
print("结果排名（第1年股权摊销占薪酬总水平比例）")
print("="*70)
print(f"  {'公司':<28} | {'比例'} | {'结论'}")
print(f"  {'':-<28}-+-{'':-<6}-+-{'':-<10}")
results.sort(key=lambda x:x[1],reverse=True)
for n,r in results:
    f="⚠️ 突破" if r>40 else "✅ 合规"
    print(f"  {n:<28} | {r:<5.1f}% | {f}")

print()
print("="*70)
print("最终判断")
print("="*70)
print(f"  10家上海国企中 {sum(1 for _,r in results if r>40)}家超标, {sum(1 for _,r in results if r<=40)}家合规")
print()
print("【为什么和之前结果不同?】")
print("  1. 第1年只摊销总公允价值的~35-40%, 不是全部预期收益")
print("  2. 分母=年薪+当年股权摊销, 分母变大, 比例降低")
print("  3. 这比""全部分配到第一年""的口径要合理得多")
print()
print("【注意】")
print("  - 实际年报中""股权激励报酬""并非按CAS 11全额""预期收益""披露")
print("  - 而是按实际解锁时确认的""股份支付费用""入账")
print("  - 但授予时点的法规合规检查应使用""预期收益""口径")
