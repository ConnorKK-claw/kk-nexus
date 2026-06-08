# -*- coding: utf-8 -*-
"""Three-tier ASI classifier: proxy_screened -> chokepoint_confirmed -> deep_tracked"""
import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')

VAULT = os.path.join(os.path.dirname(__file__), '..')
RAW = os.path.join(VAULT, 'vault', 'raw', 'agent')
KNOWLEDGE = os.path.join(VAULT, 'vault', 'knowledge')
SCRIPTS = os.path.dirname(__file__)

# Excluded codes
EXCLUDED = {'300323','300102','300303','300708','300241','002449','688378'}

# Old->new layer name mapping
RENAME = {
    '算力芯片(ASIC)': '算力芯片',
    '算力芯片(FPGA)': '算力芯片',
    '芯片设计(待归类)': '芯片设计',
    '服务器配套(PCB)': '服务器配套',
    '服务器配套(电源散热)': '服务器配套',
    'WIND.半导体材料与设备': '半导体材料',  # rough default, manual map below
    'WIND.半导体产品': '芯片设计',
    'WIND.半导体': '芯片设计',
}

# Manual code->layer map for WIND stocks
MANUAL = {
    '688729':'半导体设备','688785':'半导体设备','688652':'半导体设备',
    '688605':'半导体设备','688478':'半导体设备','301297':'半导体设备',
    '688783':'半导体材料','688545':'半导体材料','688432':'半导体材料',
    '688549':'半导体材料','688727':'半导体材料','688233':'半导体材料',
    '688167':'光通信','002213':'存储互连','688662':'服务器配套',
}

def load_csv(name):
    p = os.path.join(RAW, name)
    if os.path.exists(p):
        return list(csv.DictReader(open(p, 'r', encoding='utf-8')))
    return []

def sf(v):
    try: return float(v) if v else 0
    except: return 0

def med(vals):
    v = sorted([x for x in vals if x > 0])
    return v[len(v)//2] if v else 0

def unify_layer(code, old_layer):
    if code in MANUAL:
        return MANUAL[code]
    if old_layer in RENAME:
        return RENAME[old_layer]
    if old_layer.startswith('WIND.'):
        return '芯片设计'
    return old_layer

def main():
    TODAY = '2026-06-06'
    
    # Load all data
    full = load_csv(f'{TODAY}-asi-data-full.csv')
    val = load_csv(f'{TODAY}-asi-valuation.csv')
    gui = load_csv(f'{TODAY}-asi-guidance.csv')
    l1 = load_csv(f'{TODAY}-asi-layer-l1-full.csv')
    l2 = load_csv(f'{TODAY}-asi-layer-l2-full.csv')
    l4 = load_csv(f'{TODAY}-asi-layer-l4-full.csv')
    
    # Build dicts by code
    def idx(lst, key='code'):
        return {r[key]: r for r in lst}
    
    fd = idx(full)
    vd = idx(val)
    gd = idx(gui)
    l1d = idx(l1)
    l2d = idx(l2)
    l4d = idx(l4)
    
    # Load new asi_stocks to get correct layer mapping
    sys.path.insert(0, SCRIPTS)
    from asi_stocks import STOCKS
    new_layer_map = {s['code']: s['layer'] for s in STOCKS}
    
    print(f'Loaded: full={len(full)} val={len(val)} gui={len(gui)}')
    
    # Build layer groups for per-layer medians
    layer_groups = {}
    for s in STOCKS:
        l = s['layer']
        if l not in layer_groups:
            layer_groups[l] = []
        layer_groups[l].append(s['code'])
    
    # Per-layer GM medians
    layer_gm_med = {}
    for l, codes in layer_groups.items():
        gm_vals = []
        for c in codes:
            if c in l2d:
                gm = sf(l2d[c].get('gross_margin'))
                if 0 < gm < 100:
                    gm_vals.append(gm)
        layer_gm_med[l] = med(gm_vals)
    
    # Also compute per-layer revenue medians for revenue filter
    layer_rev_med = {}
    for l, codes in layer_groups.items():
        rev_vals = []
        for c in codes:
            if c in l2d:
                rev = sf(l2d[c].get('revenue'))
                if rev > 0:
                    rev_vals.append(rev)
        layer_rev_med[l] = med(rev_vals)
    
    print(f'\nPer-layer GM medians:')
    for l in sorted(layer_gm_med.keys()):
        print(f'  {l}: GM={layer_gm_med[l]:.1f}% Rev={layer_rev_med[l]/1e8:.1f}亿')
    
    # ====== Tier 1: Proxy Screened ======
    tier1 = []  # (stock_dict, layer)
    for s in STOCKS:
        code = s['code']
        layer = s['layer']
        
        if code not in l2d:
            continue
        
        gm = sf(l2d[code].get('gross_margin'))
        rev = sf(l2d[code].get('revenue'))
        ac = int(gd.get(code, {}).get('analyst_count', 0) or 0) if code in gd else 0
        
        gm_ok = gm > layer_gm_med.get(layer, 0) and gm > 0
        rev_ok = rev > 1e9  # 10亿
        cov_ok = ac > 0
        
        if gm_ok or rev_ok or cov_ok:
            tier1.append(s)
    
    print(f'\nTier 1 (候选关注池): {len(tier1)}/{len(STOCKS)} stocks')
    
    # ====== Tier 2: Chokepoint Confirmed (semi-auto) ======
    # For now: use L4 analyst coverage + PE digest as proxy for (a)(b)(c)
    # Manual confirmation needed to mark as confirmed
    tier2 = []
    for s in tier1:
        code = s['code']
        g = gd.get(code, {})
        
        ac = int(g.get('analyst_count', 0) or 0) if g else 0
        digest = g.get('pe_digest_years', 'N/A') if g else 'N/A'
        gs = sf(g.get('guidance_score')) if g else 0
        
        # Proxy for (a)+(b)+(c): has analyst coverage + guidance score > 50
        # Full confirmation requires manual check
        if ac >= 3 and gs >= 50:
            tier2.append({
                'code': code,
                'name': s['name'],
                'layer': s['layer'],
                'analyst_count': ac,
                'guidance_score': gs,
                'pe_digest_years': digest,
                'status': 'chokepoint_pending',  # needs manual confirm
                'verified_conditions': '部分自动覆盖(analyst+L4)',
            })
    
    print(f'Tier 2 (卡点观察池-pending): {len(tier2)} stocks (need manual confirm)')
    
    # ====== Tier 3: Deep Tracked (manual only, empty for now) ======
    tier3 = []
    print(f'Tier 3 (重点跟踪池): {len(tier3)} stocks (manual only)')
    
    # ====== Output ======
    os.makedirs(RAW, exist_ok=True)
    
    # Save tier results
    def save_tier_csv(tag, rows, extra_fields=None):
        if not rows:
            path = os.path.join(RAW, f'{TODAY}-asi-tier-{tag}.csv')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('code,name,layer,status\n')
            print(f'  Saved: {os.path.basename(path)} (empty)')
            return
        fieldnames = ['code','name','layer','status']
        if extra_fields:
            fieldnames.extend(extra_fields)
        path = os.path.join(RAW, f'{TODAY}-asi-tier-{tag}.csv')
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
        print(f'  Saved: {os.path.basename(path)} ({len(rows)} records)')
    
    t1_rows = [{'code':s['code'],'name':s['name'],'layer':s['layer'],'status':'proxy_screened'} for s in tier1]
    save_tier_csv('proxy-screened', t1_rows)
    save_tier_csv('chokepoint-pending', tier2, ['analyst_count','guidance_score','pe_digest_years','verified_conditions'])
    save_tier_csv('deep-tracked', tier3, ['score'])
    
    # ====== Generate MD report ======
    md = f'---\ntitle: 三层池子扫描 - {TODAY}\ndate: {TODAY}\nsource: agent\nstatus: auto_update\n---\n\n# 三层池子扫描\n\n## Tier 1: 候选关注池 ({len(tier1)}只)\n自动宽筛：GM>层中位 OR 营收>10亿 OR 机构覆盖>0\n\n| 层 | 数量 |\n|---|------|\n'
    from collections import Counter
    for l, c in sorted(Counter(s['layer'] for s in tier1).items(), key=lambda x:-x[1]):
        md += f'| {l} | {c} |\n'
    
    md += f'\n## Tier 2: 卡点观察池 ({len(tier2)}只，待人工确认)\n半自动筛选：分析师覆盖>=3 + 指引评分>=50\n\n| 代码 | 名称 | 层 | 分析师 | 评分 | PE消化 |\n|------|------|---|--------|------|--------|\n'
    for r in sorted(tier2, key=lambda x: -x['guidance_score'])[:30]:
        md += f'| {r["code"]} | {r["name"]} | {r["layer"]} | {r["analyst_count"]} | {r["guidance_score"]} | {r["pe_digest_years"]} |\n'
    
    md += f'\n## Tier 3: 重点跟踪池 ({len(tier3)}只)\n需人工完成6维度打分+case分析后方可进入\n'
    
    mdpath = os.path.join(KNOWLEDGE, f'zk-asi-tier-scan-{TODAY}.md')
    with open(mdpath, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'\nSaved: {os.path.basename(mdpath)}')
    print('Done!')

if __name__ == '__main__':
    main()
