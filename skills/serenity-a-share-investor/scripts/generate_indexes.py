import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')

VAULT_ROOT = os.path.join(os.path.dirname(__file__), '..', 'vault')
RAW = os.path.join(VAULT_ROOT, 'raw', 'agent')
KNOWLEDGE = os.path.join(VAULT_ROOT, 'knowledge')
TODAY = '2026-06-06'

def sf(v):
    try: return float(v) if v else 0
    except: return 0

def ldict(lst,key='code'):
    return {r[key]:r for r in lst}

# Load data
full = list(csv.DictReader(open(os.path.join(RAW,f'{TODAY}-asi-data-full.csv'),'r',encoding='utf-8')))
val = list(csv.DictReader(open(os.path.join(RAW,f'{TODAY}-asi-valuation.csv'),'r',encoding='utf-8')))
gui = list(csv.DictReader(open(os.path.join(RAW,f'{TODAY}-asi-guidance.csv'),'r',encoding='utf-8')))
val_d = ldict(val)
gui_d = ldict(gui)

pool_files = [f for f in os.listdir(RAW) if f'{TODAY}-asi-pool-' in f and f.endswith('.csv')]
pools = {}
for pf in pool_files:
    name = pf.replace(f'{TODAY}-asi-pool-','').replace('.csv','')
    pools[name] = list(csv.DictReader(open(os.path.join(RAW,pf),'r',encoding='utf-8')))

os.makedirs(KNOWLEDGE, exist_ok=True)

# ======================= 1. Company Registry =======================
md1 = f'---\\ntitle: ASI\u4e2a\u80a1\u767b\u8bb0\u603b\u8868\\ndate: {TODAY}\\nsource: agent\\nstatus: verified\\ndata_source: vault/raw/agent/{TODAY}-asi-data-full.csv\\n---\\n\\n# ASI\u4e2a\u80a1\u767b\u8bb0\u603b\u8868\\n\\n| \u4ee3\u7801 | \u540d\u79f0 | \u4ea7\u4e1a\u94fe\u5c42 | \u6838\u5fc3\u58c1\u5792 | \u4f4e\u4f30\u503c | \u9ad8\u589e\u957f | \u9f99\u5934 | \u7535\u529b\u4e0a\u6e38 | PE | \u58c1\u5792 | digest |\\n|------|------|--------|--------|--------|--------|--------|--------|----|--------|--------|\\n'

# Build pool membership sets
pool_sets = {}
for name, pool in pools.items():
    pool_sets[name] = set(r['code'] for r in pool)

for r in full:
    code = r['code']
    cm = 'Y' if code in pool_sets.get('core-moat',set()) else ''
    lv = 'Y' if code in pool_sets.get('low-val',set()) else ''
    hg = 'Y' if code in pool_sets.get('high-growth',set()) else ''
    sl = 'Y' if code in pool_sets.get('sector-leader',set()) else ''
    pu = 'Y' if code in pool_sets.get('power-upstream',set()) else ''
    pe = sf(r.get('pe_ttm'))
    gv = gui_d.get(code,{})
    vv = val_d.get(code,{})
    digest = gv.get('pe_digest_years','')
    moat = ''
    for pf_name, pf_codes in pool_sets.items():
        if code in pf_codes and 'moat' in pf_name:
            moat = '\u58c1\u5792'
    
    md1 += f'| {code} | {r["name"]} | {r["layer"]} | {cm} | {lv} | {hg} | {sl} | {pu} | {pe:.0f} | {moat} | {digest} |\\n'

with open(os.path.join(KNOWLEDGE,'zk-asi-company-registry.md'),'w',encoding='utf-8') as f:
    f.write(md1)
print(f'Created: company-registry ({len(full)} entries)')

# ======================= 2. Pool Index =======================
md2 = f'---\\ntitle: \u6c60\u5b50\u603b\u7d22\u5f15\\ndate: {TODAY}\\nsource: agent\\nstatus: auto_update\\n---\\n\\n# \u6c60\u5b50\u603b\u7d22\u5f15\\n\\n'
for name, pool in pools.items():
    avg_pe = sf(sum(sf(r.get('pe_ttm')) for r in pool) / max(len(pool),1))
    avg_cap = sf(sum(sf(r.get('mkt_cap')) for r in pool) / max(len(pool),1))
    md2 += f'## {name} ({len(pool)}\u53ea)\\n'
    md2 += f'- \u5e73\u5747PE: {avg_pe:.0f} | \u5e73\u5747\u5e02\u503c: {avg_cap:.0f}\u4ebf\\n'
    for r in pool[:15]:
        md2 += f'  - {r["code"]} {r["name"]} | {r["layer"]} | PE={sf(r["pe_ttm"]):.0f}\\n'
    if len(pool)>15:
        md2 += f'  - ... +{len(pool)-15}\u53ea (\u8be6\u89c1CSV)\\n'
    md2 += '\\n'

with open(os.path.join(KNOWLEDGE,'zk-asi-pool-index.md'),'w',encoding='utf-8') as f:
    f.write(md2)
print('Created: pool-index')

# ======================= 3. Layer Index =======================
layer_groups = {}
for r in full:
    l = r.get('layer','')
    layer_groups.setdefault(l,[]).append(r)

md3 = f'---\\ntitle: \u4ea7\u4e1a\u94fe\u5c42\u603b\u7d22\u5f15\\ndate: {TODAY}\\nsource: agent\\nstatus: auto_update\\n---\\n\\n# \u4ea7\u4e1a\u94fe\u5c42\u603b\u7d22\u5f15\\n\\n| \u5c42 | \u6570\u91cf | \u5e73\u5747PE | \u5e73\u5747ROE | \u5e73\u5747GM | \u5e73\u5747\u5e02\u503c(\u4ebf) |\\n|----|------|--------|---------|---------|-----------|\\n'
for l, ss in sorted(layer_groups.items(), key=lambda x: len(x[1]), reverse=True):
    n = len(ss)
    pe_avg = sf(sum(sf(s.get('pe_ttm')) for s in ss) / n)
    roe_avg = sf(sum(sf(s.get('roe')) for s in ss) / n)
    gm_avg = sf(sum(sf(s.get('gross_margin')) for s in ss) / n)
    cap_avg = sf(sum(sf(s.get('mkt_cap')) for s in ss if sf(s.get('mkt_cap'))>0) / max(len([s for s in ss if sf(s.get('mkt_cap'))>0]),1))
    md3 += f'| {l} | {n} | {pe_avg:.0f} | {roe_avg:.1f}% | {gm_avg:.1f}% | {cap_avg:.0f} |\\n'

with open(os.path.join(KNOWLEDGE,'zk-asi-layer-index.md'),'w',encoding='utf-8') as f:
    f.write(md3)
print('Created: layer-index')

# ======================= 4. Data Inventory =======================
md4 = f'---\\ntitle: \u6570\u636e\u6e90\u6e05\u5355\\ndate: {TODAY}\\nsource: agent\\n---\\n\\n# \u6570\u636e\u6e90\u6e05\u5355\\n\\n'
for fname in sorted(os.listdir(RAW)):
    if TODAY in fname or 'W23' in fname:
        fullp = os.path.join(RAW, fname)
        sz = os.path.getsize(fullp)
        md4 += f'- {fname} ({sz//1000}KB)\\n'
md4 += f'\\n## \u8986\u76d6\u72b6\u6001\\n\\n'
counts = {
    'L1(\u884c\u60c5)': len([r for r in full if sf(r.get('pe_ttm'))>0]),
    'L2(\u8d22\u52a1)': len([r for r in full if sf(r.get('roe'))!=0]),
    'L3(52w\u5206\u4f4d)': len([r for r in val if sf(r.get('pe_pct'))!=50]),
    'L4(\u4e00\u81f4\u9884\u671f)': len([r for r in gui if int(r.get('analyst_count',0) or 0)>0]),
}
for k,v in counts.items():
    md4 += f'- {k}: {v}/228\\n'

with open(os.path.join(KNOWLEDGE,'zk-asi-data-inventory.md'),'w',encoding='utf-8') as f:
    f.write(md4)
print('Created: data-inventory')
print('\\nAll index nodes created!')
