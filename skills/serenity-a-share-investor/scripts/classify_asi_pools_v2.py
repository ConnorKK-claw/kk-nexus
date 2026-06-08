# -*- coding: utf-8 -*-
"""
006 Employee - Pool + Tier Classifier v3
Three-tier system + 4 fixed pools (low-val, high-growth, sector-leader, power-upstream)
"""
import sys, os, csv, datetime
sys.stdout.reconfigure(encoding='utf-8')

VAULT = os.path.join(os.path.dirname(__file__), '..')
RAW = os.path.join(VAULT, 'vault', 'raw', 'agent')
KNOWLEDGE = os.path.join(VAULT, 'vault', 'knowledge')
SCRIPTS = os.path.dirname(__file__)

sys.path.insert(0, SCRIPTS)
from asi_stocks import STOCKS

TODAY = datetime.date.today().strftime('%Y-%m-%d')

def sf(v):
    try: return float(v) if v else 0
    except: return 0

def med(vals):
    v = sorted([x for x in vals if x > 0])
    return v[len(v)//2] if v else 0

def load_csv(name):
    p = os.path.join(RAW, name)
    if os.path.exists(p):
        return list(csv.DictReader(open(p, 'r', encoding='utf-8')))
    return []

print('='*50)
print(f'006 Pool + Tier Classifier v3 - {TODAY}')
print('='*50)

# ====== Load all data ======
full = load_csv(f'{TODAY}-asi-data-full.csv')
val = load_csv(f'{TODAY}-asi-valuation.csv')
gui = load_csv(f'{TODAY}-asi-guidance.csv')
l2 = load_csv(f'{TODAY}-asi-layer-l2-full.csv')

# Build dicts
def idx(lst, key='code'):
    return {r[key]: r for r in lst if r.get(key)}

fd = idx(full); vd = idx(val); gd = idx(gui); l2d = idx(l2)

# Map old layer names to new ones for the data
def map_layer(code):
    for s in STOCKS:
        if s['code'] == code:
            return s['layer']
    return ''

# ====== Build layer groups from new STOCKS ======
layer_groups = {}
for s in STOCKS:
    l = s['layer']
    if l not in layer_groups:
        layer_groups[l] = []
    layer_groups[l].append(s)

# Per-layer GM median
layer_gm_med = {}
for l, ss in layer_groups.items():
    vals = [sf(l2d.get(s['code'], {}).get('gross_margin')) for s in ss if s['code'] in l2d]
    layer_gm_med[l] = med([v for v in vals if 0 < v < 100])

print(f'\nNew ASI universe: {len(STOCKS)} stocks, {len(layer_groups)} layers')
for l, ss in sorted(layer_groups.items(), key=lambda x: -len(x[1])):
    pe_vals = [sf(fd.get(s['code'], {}).get('pe_ttm')) for s in ss if s['code'] in fd]
    avg_pe = med(pe_vals) if pe_vals else 0
    print(f'  {l}: {len(ss)} stocks (PE中位={avg_pe:.0f} GM中位={layer_gm_med.get(l,0):.1f}%)')

# ====== Tier 1: 候选关注池 (auto) ======
tier1 = []
for s in STOCKS:
    code = s['code']
    if code not in l2d:
        continue
    gm = sf(l2d[code].get('gross_margin'))
    rev = sf(l2d[code].get('revenue'))
    ac = int(gd.get(code, {}).get('analyst_count', 0) or 0) if code in gd else 0
    gm_ok = gm > layer_gm_med.get(s['layer'], 0) and gm > 0
    rev_ok = rev > 1e9
    cov_ok = ac > 0
    if gm_ok or rev_ok or cov_ok:
        tier1.append(s)

# ====== Tier 2: 卡点观察池 (semi-auto) ======
tier2 = []
for s in tier1:
    code = s['code']
    g = gd.get(code, {})
    ac = int(g.get('analyst_count', 0) or 0) if g else 0
    gs = sf(g.get('guidance_score')) if g else 0
    if ac >= 3 and gs >= 50:
        tier2.append({'code':code,'name':s['name'],'layer':s['layer'],
                      'analyst_count':ac,'guidance_score':gs,
                      'status':'chokepoint_pending',
                      'verified_conditions':'proxy(L4+analyst)'})

# ====== Tier 3: 重点跟踪池 (manual, empty) ======
tier3 = []

# ====== Fixed pools (unchanged) ======
pools = {'low-val':[],'high-growth':[],'sector-leader':[],'power-upstream':[]}

for s in STOCKS:
    code = s['code']; layer = s['layer']
    f = fd.get(code, {}); v = vd.get(code, {}); g = gd.get(code, {}); l = l2d.get(code, {})
    pe = sf(f.get('pe_ttm')); pb = sf(f.get('pb')); cap = sf(f.get('mkt_cap'))
    roe = sf(l.get('roe')); gm = sf(l.get('gross_margin'))
    rev_yoy = sf(l.get('revenue_yoy')); profit_yoy = sf(l.get('profit_yoy'))
    pe_pct = sf(v.get('pe_pct')); z_pe = sf(v.get('layer_z_pe'))
    gs = sf(g.get('guidance_score')); ac = int(g.get('analyst_count',0) or 0)
    digest = g.get('pe_digest_years','N/A')
    
    entry = {'code':code,'name':s['name'],'layer':layer,'pe_ttm':pe,'pb':pb,
             'mkt_cap':cap,'roe':roe,'gross_margin':gm,'pe_pct':pe_pct,
             'layer_z_pe':z_pe,'guidance_score':gs,'analyst_count':ac,
             'pe_digest_years':digest,'revenue_yoy':rev_yoy,'profit_yoy':profit_yoy}
    
    # Low-val: pe_pct<30, layer_z_pe<-0.5
    # Low-val: z_pe < -0.3
    if z_pe < -0.3:
    # High-growth: rev_yoy>30 or profit_yoy>50
        pools['low-val'].append(entry)
    if rev_yoy > 30 or profit_yoy > 50:
        pools['high-growth'].append(entry)
    # Sector leader: top 2 per layer by mkt_cap
    layer_stocks = sorted(layer_groups.get(layer,[]), key=lambda x: sf(fd.get(x['code'],{}).get('mkt_cap')), reverse=True)
    rank = next((i+1 for i,ls in enumerate(layer_stocks) if ls['code']==code), 99)
    if rank <= 2 and cap > 50:
        pools['sector-leader'].append({**entry, 'layer_rank': rank})
    # Power upstream: AI基础设施 layer + keyword match
    if layer == 'AI基础设施' or any(kw in s['name'] for kw in ['液冷','温控','UPS','电源','散热','精密空调']):
        pools['power-upstream'].append(entry)

# ====== Save all ======
# Tier files (csv.writer)
import csv as csvmod
for tag, rows in [('proxy-screened', tier1), ('chokepoint-pending', tier2), ('deep-tracked', tier3)]:
    outpath = os.path.join(RAW, f'{TODAY}-asi-tier-{tag}.csv')
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csvmod.writer(f)
        w.writerow(['code','name','layer','status'])
        for r in rows:
            if isinstance(r, dict):
                w.writerow([r.get("code",""), r.get("name",""), r.get("layer",""), tag])
            else:
                w.writerow([r.code, r.name, r.layer, tag])
    print(f'  Tier {tag}: {len(rows)} stocks')
# Pool files
for name, pool in pools.items():
    outpath = os.path.join(RAW, f'{TODAY}-asi-pool-{name}.csv')
    if pool:
        fns = list(pool[0].keys())
        with open(outpath, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fns)
            w.writeheader(); w.writerows(pool)
        print(f'  Pool {name}: {len(pool)} stocks')
    else:
        print(f'  Pool {name}: 0 stocks')

# ====== Generate MD report ======
md = f'---\\ntitle: \u6c60\u5b50+\u4e09\u5c42\u626b\u63cf - {TODAY}\\ndate: {TODAY}\\nsource: agent\\nstatus: auto_update\\n---\\n\\n# \u6c60\u5b50+\u4e09\u5c42\u626b\u63cf\\n\\n'

md += f'## Tier 1: \u5019\u9009\u5173\u6ce8\u6c60 ({len(tier1)}\u53ea)\\n'
from collections import Counter
for l,c in sorted(Counter(s['layer'] for s in tier1).items(), key=lambda x:-x[1]):
    md += f'- {l}: {c}\\n'

md += f'\\n## Tier 2: \u5361\u70b9\u89c2\u5bdf\u6c60 ({len(tier2)}\u53ea\uff0c\u5f85\u786e\u8ba4)\\n'
for r in sorted(tier2, key=lambda x: -x.get('guidance_score',0))[:20]:
    md += f'- {r["code"]} {r["name"]} | {r["layer"]} | score={r["guidance_score"]} analyst={r["analyst_count"]}\\n'

md += f'\\n## Tier 3: \u91cd\u70b9\u8ddf\u8e2a\u6c60 ({len(tier3)}\u53ea)\\n'

md += f'\\n## \u4f4e\u4f30\u503c\u6c60 ({len(pools["low-val"])}\u53ea)\\n'
for r in pools['low-val'][:10]:
    md += f'- {r["code"]} {r["name"]} | PE={r["pe_ttm"]:.0f} \u5206\u4f4d={r["pe_pct"]:.0f}% z={r["layer_z_pe"]:.1f}\\n'

md += f'\\n## \u9ad8\u589e\u957f\u6c60 ({len(pools["high-growth"])}\u53ea)\\n'
for r in pools['high-growth'][:15]:
    md += f'- {r["code"]} {r["name"]} | \u8425\u6536+{r["revenue_yoy"]:.0f}% \u5229\u6da6+{r["profit_yoy"]:.0f}% PE={r["pe_ttm"]:.0f}\\n'

md += f'\\n## \u9f99\u5934\u6c60 ({len(pools["sector-leader"])}\u53ea)\\n'
for r in sorted(pools['sector-leader'], key=lambda x: -sf(x.get('mkt_cap',0))):
    md += f'- {r["code"]} {r["name"]} | {r["layer"]} | \u5e02\u503c={sf(r.get("mkt_cap",0)):.0f}\u4ebf PE={r["pe_ttm"]:.0f}\\n'

md += f'\\n## \u7535\u529b\u4e0a\u6e38\u6c60 ({len(pools["power-upstream"])}\u53ea)\\n'
for r in pools['power-upstream']:
    md += f'- {r["code"]} {r["name"]} | PE={r["pe_ttm"]:.0f}\\n'

mdpath = os.path.join(KNOWLEDGE, f'zk-asi-pools-tiers-scan-{TODAY}.md')
with open(mdpath, 'w', encoding='utf-8') as f:
    f.write(md)
print(f'\\nMD: {os.path.basename(mdpath)}')
print('Done!')


