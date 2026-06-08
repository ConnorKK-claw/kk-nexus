import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')

RAW = os.path.join(os.path.dirname(__file__), '..', 'vault', 'raw', 'agent')
VAULT = os.path.join(os.path.dirname(__file__), '..', 'vault')
TODAY = '2026-06-06'

def sf(v):
    try: return float(v) if v else 0
    except: return 0
def med(vals):
    v=sorted([x for x in vals if x>0])
    return v[len(v)//2] if v else 0
def ldict(lst,key='code'):
    return {r[key]:r for r in lst}

full=list(csv.DictReader(open(os.path.join(RAW,f'{TODAY}-asi-data-full.csv'),'r',encoding='utf-8')))
val=list(csv.DictReader(open(os.path.join(RAW,f'{TODAY}-asi-valuation.csv'),'r',encoding='utf-8')))
gui=list(csv.DictReader(open(os.path.join(RAW,f'{TODAY}-asi-guidance.csv'),'r',encoding='utf-8')))
val_d=ldict(val)
gui_d=ldict(gui)
print(f'Loaded {len(full)} stocks')
pe_med=med([sf(r.get('pe_ttm')) for r in full if 0<sf(r.get('pe_ttm'))<500]) or 50
roe_med=med([sf(r.get('roe')) for r in full if -50<sf(r.get('roe'))<100]) or 8
gm_med=med([sf(r.get('gross_margin')) for r in full if 0<sf(r.get('gross_margin'))<100]) or 35
print(f'Industry: PE={pe_med:.1f} ROE={roe_med:.1f}% GM={gm_med:.1f}%')
layer_groups={}
for r in full:
    l=r.get('layer','')
    layer_groups.setdefault(l,[]).append(r)
pools={'core-moat':[],'low-val':[],'high-growth':[],'sector-leader':[],'power-upstream':[]}
for r in full:
    code=r['code']; layer=r.get('layer','')
    v=val_d.get(code,{}); g=gui_d.get(code,{})
    pe=sf(r.get('pe_ttm')); pb=sf(r.get('pb')); cap=sf(r.get('mkt_cap'))
    roe=sf(r.get('roe')); gm=sf(r.get('gross_margin'))
    rev_yoy=sf(r.get('revenue_yoy')); profit_yoy=sf(r.get('profit_yoy'))
    pe_pct=sf(v.get('pe_pct')); z_pe=sf(v.get('layer_z_pe'))
    gs=sf(g.get('guidance_score')); ac=int(g.get('analyst_count',0) or 0)
    digest=g.get('pe_digest_years','N/A')
    is_strong = gm>gm_med and roe>roe_med*0.8 and gs>50 and cap>50
    is_medium = gm>gm_med*0.7 and roe>0 and gs>30 and cap>30
    moat='\u5f37' if is_strong else ('\u4e2d' if is_medium else '\u5f31')
    is_core_moat = is_strong or is_medium
    is_low_val = 0<pe_pct<30 and z_pe<-0.5
    is_high_growth = rev_yoy>30 or profit_yoy>50
    layer_stocks=layer_groups.get(layer,[])
    layer_sorted=sorted(layer_stocks, key=lambda x: sf(x.get('mkt_cap')), reverse=True)
    rank=next((i+1 for i,ls in enumerate(layer_sorted) if ls['code']==code),99)
    is_leader = rank<=2 and cap>50
    is_power = '\u7535\u6e90' in layer or '\u6563\u70ed' in layer
    entry={'code':code,'name':r['name'],'layer':layer,'pe_ttm':pe,'pb':pb,
           'mkt_cap':cap,'roe':roe,'gross_margin':gm,'pe_pct':pe_pct,
           'layer_z_pe':z_pe,'guidance_score':gs,'analyst_count':ac,
           'pe_digest_years':digest,'revenue_yoy':rev_yoy,'profit_yoy':profit_yoy,
           'moat':moat,'layer_rank':rank}
    if is_core_moat: pools['core-moat'].append(entry)
    if is_low_val: pools['low-val'].append(entry)
    if is_high_growth: pools['high-growth'].append(entry)
    if is_leader: pools['sector-leader'].append(entry)
    if is_power: pools['power-upstream'].append(entry)
for name, pool in pools.items():
    outpath=os.path.join(RAW,f'{TODAY}-asi-pool-{name}.csv')
    if pool:
        fns=list(pool[0].keys())
        with open(outpath,'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fns)
            w.writeheader(); w.writerows(pool)
        print(f'  {name}: {len(pool)} stocks')
    else:
        print(f'  {name}: 0 stocks')
md='---\\ntitle: \u6c60\u5b50\u7efc\u5408\u626b\u63cf - '+TODAY+'\\ndate: '+TODAY+'\\nsource: agent\\nstatus: auto_update\\n---\\n\\n# \u6c60\u5b50\u7efc\u5408\u626b\u63cf\\n\\n## \u6838\u5fc3\u58c1\u5792\u6c60 ('+str(len(pools['core-moat']))+'\u53ea)\n'
for p in pools['core-moat'][:50]:
    md+=f'- {p["code"]} {p["name"]} | {p["layer"]} | PE={p["pe_ttm"]:.0f} ROE={p["roe"]}% GM={p["gross_margin"]:.1f}% | moat={p["moat"]} | digest={p["pe_digest_years"]}\\n'
md+='\\n## \u4f4e\u4f30\u503c\u6c60 ('+str(len(pools['low-val']))+'\u53ea)\n'
for p in pools['low-val']:
    md+=f'- {p["code"]} {p["name"]} | {p["layer"]} | PE={p["pe_ttm"]:.0f} pct={p["pe_pct"]:.0f}% z={p["layer_z_pe"]:.1f}\\n'
md+='\\n## \u9ad8\u589e\u957f\u6c60 ('+str(len(pools['high-growth']))+'\u53ea)\n'
for p in pools['high-growth'][:30]:
    md+=f'- {p["code"]} {p["name"]} | {p["layer"]} | rev+{p["revenue_yoy"]:.0f}% profit+{p["profit_yoy"]:.0f}% PE={p["pe_ttm"]:.0f}\\n'
md+='\\n## \u9f99\u5934\u6c60 ('+str(len(pools['sector-leader']))+'\u53ea)\n'
for p in pools['sector-leader']:
    md+=f'- {p["code"]} {p["name"]} | {p["layer"]} #{p["layer_rank"]} | \u5e02\u503c={p["mkt_cap"]:.0f}\u4ebf PE={p["pe_ttm"]:.0f}\\n'
mdpath=os.path.join(VAULT,'knowledge',f'zk-asi-kk0-0-pools-scan-{TODAY}.md')
os.makedirs(os.path.dirname(mdpath),exist_ok=True)
with open(mdpath,'w',encoding='utf-8') as f:
    f.write(md)
print(f'\\nMD: {os.path.basename(mdpath)}')
print('Done!')
