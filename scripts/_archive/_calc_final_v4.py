# -*- coding: utf-8 -*-
"""
40%红线最终计算：按授予时点、一期合计、分母含权益授予价值

公式：权益授予价值(授予价×股数) / (现金年薪 + 权益授予价值) <= 40%
等价于：权益授予价值 <= 66.7% × 现金年薪
"""
import json

with open(r"C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_data.json","r",encoding="utf-8") as f:
    exec_data = json.load(f)

data = {
    "国泰海通":{"p":7.64,"name":"国泰君安/国泰海通(2020)"},
    "华建集团_2018":{"p":5.86,"name":"华建集团(2018一轮)"},
    "华建集团_2022":{"p":3.19,"name":"华建集团(2022二轮)"},
    "华谊集团":{"p":3.85,"name":"华谊集团(2020)"},
    "锦江酒店":{"p":11.85,"name":"锦江酒店(2024)"},
    "上港集团":{"p":2.21,"name":"上港集团(2021)"},
    "上海机场":{"p":18.22,"name":"上海机场(2024)"},
    "外服控股":{"p":3.53,"name":"外服控股(2022)"},
    "东方创业":{"p":3.95,"name":"东方创业(2021)"},
    "申能股份":{"p":2.89,"name":"申能股份(2021)"},
}

sal = {
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
    e=sal.get(ck,{"t":80,"v":70,"o":60})
    if any(t in pos for t in ["总裁","总经理","董事长","CEO"]): return e["t"]
    if any(t in pos for t in ["副总裁","副总","财务总","董秘","总工"]): return e["v"]
    return e["o"]

def ps(s):
    s=s.replace("万股","").replace(",","").replace("约","").strip()
    try: return float(s)
    except:
        try: return float(s.replace("+",""))
        except: return 0

print("="*120)
print("最终计算：权益授予价值/(现金年薪+权益授予价值) <= 40%")
print("="*120)
print()
print("【口径验证】")
print("  分子 = 权益授予价值（一期合计100%）= 授予价格 × 获授股数")
print("  分母 = 薪酬总水平（含权益授予价值）= 现金年薪 + 权益授予价值")
print("  等价于：权益授予价值 <= 66.7% × 现金年薪")
print()

results=[]

for ck in ["国泰海通","华建集团_2018","华建集团_2022","华谊集团","锦江酒店",
            "上港集团","上海机场","外服控股","东方创业","申能股份"]:
    
    d=data[ck]
    ed=exec_data.get(ck,{})
    execs=ed.get("execs",[])
    if not execs: continue
    
    price=d["p"]
    print(f"{'─'*90}")
    print(f"▶ {d['name']}（授予价={price}元/股）")
    print(f"{'─'*90}")
    print(f"  {'姓名':<8} | {'职务':<18} | {'获授(万股)':<10} | {'权益授予价值(万)':<16} | {'年薪(万)':<8} | {'含权薪酬(万)':<12} | {'占比'}")
    print(f"  {'':-<8}-+-{'':-<18}-+-{'':-<10}-+-{'':-<16}-+-{'':-<8}-+-{'':-<12}-+-{'':-<6}")
    
    tv=0; ts=0
    for e in execs:
        n,p,ss=e[0],e[1],e[2]
        sh=ps(ss)
        if sh<=0: continue
        sa=gs(n,p,ck)
        gv=sh*10000*price
        denom=sa*10000+gv
        ratio=gv/denom*100
        tv+=gv; ts+=sa*10000
        flag="⚠️" if ratio>40 else "✅"
        print(f"  {flag} {n:<8} | {p:<18} | {ss:<10} | {gv/10000:<14.1f}万 | {sa:<6.0f}万 | {denom/10000:<10.1f}万 | {ratio:>4.1f}%")
    
    overall=tv/(ts+tv)*100
    results.append((d["name"],overall))
    flag="⚠️ 突破" if overall>40 else "✅ 合规"
    print(f"  {'─'*90}")
    print(f"  ▶ 合计: {tv/10000:.0f}万 / ({ts/10000:.0f}万+{tv/10000:.0f}万)={ts/10000+tv/10000:.0f}万 = {overall:.1f}% {flag}")
    print()

print("="*70)
print("排名（权益授予价值/含权薪酬总水平）")
print("="*70)
print(f"  {'公司':<26} | {'占比':<6} | {'结论'}")
print(f"  {'':-<26}-+-{'':-<6}-+-{'':-<10}")
results.sort(key=lambda x:x[1],reverse=True)
for n,r in results:
    f="⚠️ 突破" if r>40 else "✅ 合规"
    print(f"  {n:<26} | {r:<5.1f}% | {f}")

print()
print("="*70)
print("结论")
print("="*70)
over = sum(1 for _,r in results if r>40)
comp = sum(1 for _,r in results if r<=40)
print(f"  10家上海国企中 {over}家超标, {comp}家合规")
print()
print("注意：薪酬数据为行业可比公开数近似值，精确值需逐公司核实年报披露数")
