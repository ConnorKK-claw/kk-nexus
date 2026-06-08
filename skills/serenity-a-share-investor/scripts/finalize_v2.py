# -*- coding: utf-8 -*-
"""Finalize: update references, zk-categories, index nodes, WAL"""
import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')

VAULT = os.path.join(os.path.dirname(__file__), '..')
RAW = os.path.join(VAULT, 'vault', 'raw', 'agent')
KNOWLEDGE = os.path.join(VAULT, 'vault', 'knowledge')
REFS = os.path.join(VAULT, 'references')
SCRIPTS = os.path.dirname(__file__)

sys.path.insert(0, SCRIPTS)
from asi_stocks import STOCKS

TODAY = '2026-06-06'

# ====== 1. Update zk-categories.md ======
cat_path = os.path.join(KNOWLEDGE, 'zk-categories.md')
cat_content = f'''---
title: zk-categories.md
date: {TODAY}
source: agent
domain: asi
status: raw
---

# zk-categories.md -- 分类码映射表(asi domain)

| 分类码 | 分类名 | 说明 |
|--------|--------|------|
| aa | 产业链卡点 | 供应链瓶颈/卡点层识别 |
| bb | 公司分析 | 个股基本面/估值/竞争格局 |
| cc | 设备材料 | 半导体设备/材料/耗材 |
| dd | 封装测试 | 先进封装/HBM/测试 |
| ee | 光通信 | CPO/硅光/激光器/光模块 |
| ff | EDA/IP | 设计工具/IP授权/设计服务 |
| gg | 政策地缘 | 出口管制/国产替代/产业政策 |
| hh | 宏观映射 | 资本开支周期/需求趋势/景气度 |
| ii | 估值分析 | PE/PB分位、估值方法论、横向对比 |
| jj | 业绩指引 | 一致预期、确定性评分、增速可预见性 |
| kk | 池子分组 | 三层池子+固定池分组结果 |
| ll | 市场数据 | 行情快照、交易数据、技术面 |
| mm | 芯片设计 | Fabless IC设计公司分析 |

## 组序号规则
- X0: 人工精化的参考级节点
- X: 自动蒸馏节点
'''
with open(cat_path, 'w', encoding='utf-8') as f:
    f.write(cat_content)
print('Updated: zk-categories.md')

# ====== 2. Update value-chain-seed.md ======
seed_path = os.path.join(REFS, 'value-chain-seed.md')

# Build layer stock lists
layer_stocks = {}
for s in STOCKS:
    l = s['layer']
    if l not in layer_stocks:
        layer_stocks[l] = []
    layer_stocks[l].append(s)

seed = f'''# A股AI半导体产业链种子图谱（v3统一版）

## 概述

层架构统一版本：221只股票，10个产业链层。
已排除7只非AI半导体标的（6只LED光电+1只OLED）。

## 产业链分层

'''

for l in ['算力芯片','芯片设计','存储互连','半导体设备','半导体材料','先进封测','光通信','EDA/IP','功率半导体','服务器配套']:
    ss = layer_stocks.get(l, [])
    seed += f'### {l}（{len(ss)}只）\n'
    for s in sorted(ss, key=lambda x: x['code']):
        seed += f'- {s["code"]} {s["name"]}\n'
    seed += '\n'

seed += '''## 排除清单

| 代码 | 名称 | 原因 |
|------|------|------|
| 300323 | 华灿光电 | LED照明，与AI半导体关联弱 |
| 300102 | 乾照光电 | LED照明 |
| 300303 | 聚飞光电 | LED照明 |
| 300708 | 聚灿光电 | LED照明 |
| 300241 | 瑞丰光电 | LED照明 |
| 002449 | 国星光电 | LED封装 |
| 688378 | 奥来德 | OLED显示材料，与AI算力关联弱 |

## 三层池子架构

| 层级 | 名称 | 筛选方式 | 当前数量 |
|------|------|---------|---------|
| Tier 1 | 候选关注池 | 自动宽筛(GM>层中位/营收>10亿/机构覆盖>0) | 175 |
| Tier 2 | 卡点观察池 | 半自动+人工确认(分析师>=3+指引>=50+4条件检查) | 22(pending) |
| Tier 3 | 重点跟踪池 | 人工(6维度评分>=20/30+case分析) | 0 |

## 固定池

| 池子 | 数量 | 逻辑 |
|------|------|------|
| 高增长池 | 103 | 营收增速>30%或利润增速>50% |
| 细分龙头池 | 20 | 每层市值前2 |
| 低估值池 | 0 | PE分位<30%+z<-0.5(条件偏严) |
| 电力上游池 | 0 | 层名含电源/散热(已合并到服务器配套层) |

## 使用说明

- 此图谱为006员工全量标的池（221只），覆盖10层
- 层名已统一（无WIND.前缀、(待归类)后缀）
- 与 scripts/asi_stocks.py 完全同步
'''

with open(seed_path, 'w', encoding='utf-8') as f:
    f.write(seed)
print('Updated: value-chain-seed.md')

# ====== 3. Regenerate company-registry ======
reg_path = os.path.join(KNOWLEDGE, 'zk-asi-company-registry.md')

def get_tier(code, tiers):
    for tag, rows in tiers:
        for r in rows:
            if r.get('code') == code:
                return tag
    return '未入池'

# Load tier CSVs
tiers = []
for tag in ['deep-tracked', 'chokepoint-pending', 'proxy-screened']:
    p = os.path.join(RAW, f'{TODAY}-asi-tier-{tag}.csv')
    if os.path.exists(p):
        rows = list(csv.DictReader(open(p, 'r', encoding='utf-8')))
        tiers.append((tag, rows))

# Load pool CSVs
pool_sets = {}
for pf in os.listdir(RAW):
    if f'{TODAY}-asi-pool-' in pf and pf.endswith('.csv'):
        name = pf.replace(f'{TODAY}-asi-pool-','').replace('.csv','')
        pool_sets[name] = set(r['code'] for r in csv.DictReader(open(os.path.join(RAW,pf),'r',encoding='utf-8')))

reg = '---\ntitle: ASI个股登记总表\ndate: ' + TODAY + '\nsource: agent\nstatus: verified\n---\n\n# ASI个股登记总表\n\n| 代码 | 名称 | 产业链层 | 三层归属 | 高增长 | 龙头 | PE |\n|------|------|---------|---------|--------|------|----|\n'

fd = {}
for f in os.listdir(RAW):
    if f == f'{TODAY}-asi-data-full.csv':
        for r in csv.DictReader(open(os.path.join(RAW,f),'r',encoding='utf-8')):
            fd[r['code']] = r

for s in STOCKS:
    code = s['code']
    tier = get_tier(code, tiers)
    hg = 'Y' if code in pool_sets.get('high-growth', set()) else ''
    sl = 'Y' if code in pool_sets.get('sector-leader', set()) else ''
    f = fd.get(code, {})
    pe = sf(f.get('pe_ttm')) if f else 0
    reg += f'| {code} | {s["name"]} | {s["layer"]} | {tier} | {hg} | {sl} | {pe:.0f} |\n'

with open(reg_path, 'w', encoding='utf-8') as f:
    f.write(reg)
print('Regenerated: company-registry (' + str(len(STOCKS)) + ' entries)')

# ====== 4. WAL: SESSION-STATE + memory + index ======
ss_path = os.path.join(VAULT, 'SESSION-STATE.md')
ss = f'''# Session State - {TODAY} (Universe Restructure Complete)

## Completed
- L1+L2+L3+L4 crawl (228 stocks, now filtered to 221)
- Layer unfication: 13→10 layers, no WIND. prefix, no (待归类) suffix
- Excluded 7 non-AI-semiconductor stocks (6 LED + 1 OLED)
- WIND manual reclassification: 16 stocks → correct layers
- Chip design layer created: 78 stocks (was 芯片设计(待归类))
- Three-tier system: 候选关注池(175) → 卡点观察池(22) → 重点跟踪池(0)
- 4 fixed pools: 高增长(103) / 龙头(20) / 低估值(0) / 电力上游(0)
- Updated references, zk-categories, company-registry

## Pending
- L5 (AKShare research) - batch for tier2 stocks
- Manual chokepoint confirmation for tier2 (22 stocks)
- Tier3 case analysis (manual)
- Power-upstream pool: 0 stocks, check layer name matching
- Low-val pool: 0 stocks, criteria too strict

---
Universe: 221 stocks, 10 layers
Latest: {TODAY}
'''
with open(ss_path, 'w', encoding='utf-8') as f:
    f.write(ss)
print('Updated: SESSION-STATE.md')

# Memory
mem_path = os.path.join(VAULT, 'vault', 'memory', f'{TODAY}.md')
os.makedirs(os.path.dirname(mem_path), exist_ok=True)
mem = f'''# Memory Log - {TODAY}

## Key Changes
1. Universe: 228→221 stocks, 13→10 unified layers
2. WIND.xxx prefix removed, 16 stocks manually reclassified
3. LED (6) + OLED (1) excluded
4. Three-tier system replaced one-dimensional core-moat pool
5. Layer-specific GM medians used for tier1 screening (not global median)

## Layer Counts
'''
for l, ss in sorted(layer_stocks.items(), key=lambda x: -len(x[1])):
    mem += f'- {l}: {len(ss)}\n'

mem += f'''
## Tier Status
- Tier1 (proxy_screened): 175
- Tier2 (chokepoint_pending): 22
- Tier3 (deep_tracked): 0

## Issues
- power-upstream pool was 0 because layer names changed (服务器配套)
- low-val pool: 0 stocks, threshold needs review
- Some WIND L3=半导体材料与设备 stocks may have incorrect layer assignments
'''
with open(mem_path, 'w', encoding='utf-8') as f:
    f.write(mem)
print('Updated: memory log')

# Index
idx_path = os.path.join(KNOWLEDGE, 'index.md')
idx_content = f'---\ntitle: 知识索引\ndate: {TODAY}\nsource: agent\n---\n\n# ASI 知识索引\n\n## 层结构\n- [zk-asi-company-registry.md](zk-asi-company-registry.md) - 221只个股登记表\n- [zk-asi-layer-index.md](zk-asi-layer-index.md) - 10层对比表\n\n## 池子\n- [zk-asi-pools-tiers-scan-{TODAY}.md](zk-asi-pools-tiers-scan-{TODAY}.md) - 三层+固定池\n- [zk-asi-tier-scan-{TODAY}.md](zk-asi-tier-scan-{TODAY}.md) - 三层详细扫描\n\n## 分类\n- [zk-categories.md](zk-categories.md) - 分类码映射\n'
with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(idx_content)
print('Updated: knowledge/index.md')

print('\\nALL DONE!')
