#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""006 Pool Classifier"""
import os,sys,csv,datetime,math
sys.stdout.reconfigure(encoding="utf-8")
V=os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
R=os.path.join(V,"vault","raw","agent")
K=os.path.join(V,"vault","knowledge")
T=datetime.date.today().strftime("%Y-%m-%d")
J=os.path.join

def sf(v,d=0.0):
    if v is None or str(v).strip() in ("","None"): return d
    try:
        fv=float(v)
        return d if (math.isnan(fv) or math.isinf(fv)) else fv
    except: return d

def load():
    fs=sorted([f for f in os.listdir(R) if f.endswith("-asi-data-full.csv")],reverse=True)
    if not fs: sys.exit("[ERROR] No data CSV!")
    with open(J(R,fs[0]),encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    print(f"Loaded {fs[0]} ({len(rows)} rows)")
    return rows

def med(v):
    v=sorted(v);n=len(v)
    return v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2 if n else 0

def classify(rows):
    pe_v=[sf(r.get("pe_ttm")) for r in rows if 0<sf(r.get("pe_ttm"))<500]
    pb_v=[sf(r.get("pb")) for r in rows if 0<sf(r.get("pb"))<50]
    pe_m=med(pe_v) or 50.0; pb_m=med(pb_v) or 3.0
    print(f"PE:{pe_m:.1f} PB:{pb_m:.2f}")
    pools={"c":[],"l":[],"h":[],"s":[],"p":[]}
    ly={}
    for r in rows:
        l=r.get("layer","O")
        ly.setdefault(l,[]).append(r)
    for l,ms in ly.items():
        for m in sorted(ms,key=lambda x:sf(x.get("total_mv")),reverse=True)[:2]:
            pools["s"].append(m)
    for r in rows:
        pe=sf(r.get("pe_ttm"));pb=sf(r.get("pb"));roe=sf(r.get("roe"))
        ry=sf(r.get("rev_yoy"));py_=sf(r.get("profit_yoy"))
        if 0<pe<pe_m*0.7 and 0<pb<pb_m*0.8 and roe>10: pools["c"].append(r)
        if 0<pe<30 and 0<pb<2: pools["l"].append(r)
        if ry>30 or py_>50: pools["h"].append(r)
        if r.get("power_upstream")=="Y": pools["p"].append(r)
    return pools,pe_m,pb_m,ly

def save_csvs(pools):
    for k,fn in [("c","core-moat"),("l","low-val"),("h","high-growth"),("s","sector-leader"),("p","power-upstream")]:
        po=pools[k]; p=J(R,f"{T}-asi-pool-{fn}.csv")
        if not po:
            with open(p,"w",newline="",encoding="utf-8") as f: f.write("code,name,layer\n")
        else:
            with open(p,"w",newline="",encoding="utf-8") as f:
                fn=list(po[0].keys())
                w=csv.DictWriter(f,fieldnames=fn);w.writeheader();w.writerows(po)
        print(f" CSV: {os.path.basename(p)} ({len(po)} recs)")

def gen_md(pools,pe_m,pb_m,rows):
    p=J(K,f"zk-asi-bb0-0-scan-{T}.md")
    c=[]; x=c.append
    x("---")
    x(f"title: A\u80a1AI\u534a\u5bfc\u4f53\u5168\u4ea7\u4e1a\u94fe\u626b\u63cf-\u4f4e\u4f30\u503c+\u9ad8\u58c1\u5792\u4e13\u9898")
    x(f"date: {T}"); x("source: agent"); x("domain: asi")
    x("tags: [AI\u534a\u5bfc\u4f53,\u5168\u4ea7\u4e1a\u94fe\u626b\u63cf,\u4f4e\u4f30\u503c,\u9ad8\u58c1\u5792,\u6c60\u5b50\u5206\u7c7b]")
    x("status: distilled"); x("---"); x("")
    x(f"# A\u80a1AI\u534a\u5bfc\u4f53\u5168\u4ea7\u4e1a\u94fe\u626b\u63cf-\u4f4e\u4f30\u503c+\u9ad8\u58c1\u5792\u4e13\u9898"); x("")
    x(f"> {T} | {len(rows)} | PE\u4e2d\u4f4d\u6570:{pe_m:.1f} | PB\u4e2d\u4f4d\u6570:{pb_m:.2f}"); x("")
    x("## \u6c60\u5b50\u6982\u89c8")
    x("|\u6c60\u5b50|\u6570\u91cf|"); x("|-|-")
    for pk,cn,n in [("c","\u6838\u5fc3\u58c1\u5792\u6c60",len(pools["c"])),("l","\u4f4e\u4f30\u503c\u6c60",len(pools["l"])),
                     ("h","\u9ad8\u589e\u957f\u6c60",len(pools["h"])),("s","\u4ea7\u4e1a\u94fe\u9f99\u5934\u6c60",len(pools["s"])),
                     ("p","\u7535\u529b\u4e0a\u6e38\u6c60",len(pools["p"]))]:
        x(f"|{cn}|{n}|")
    x("")
    for pk,cn in [("c","\u6838\u5fc3\u58c1\u5792\u6c60"),("l","\u4f4e\u4f30\u503c\u6c60"),("h","\u9ad8\u589e\u957f\u6c60"),("s","\u4ea7\u4e1a\u94fe\u9f99\u5934\u6c60"),("p","\u7535\u529b\u4e0a\u6e38\u6c60")]:
        po=pools[pk]
        x(f"## {cn}"); x("")
        if not po: x("*\u6682\u65e0*"); x(""); continue
        x("|#|\u4ee3\u7801|\u540d\u79f0|\u5c42|\u4ef7\u683c|PE|PB|ROE%|\u6bdb\u5229\u7387%|\u5e02\u503c|\u8425\u6536\u589e\u901f%|")
        x("|-|------|------|-|------|--------|----|------|---------|------|----------|")
        for i,r in enumerate(po,1):
            pe=sf(r.get("pe_ttm"));mv=sf(r.get("total_mv"));ry=sf(r.get("rev_yoy"))
            pr=sf(r.get("price"));pbv=sf(r.get("pb"));roe=sf(r.get("roe"));gm=sf(r.get("gross_margin"))
            pe_s=f"{pe:.1f}" if 0<pe<9999 else "-"
            mv_s=f"{mv/1e8:.1f}\u4ebf" if mv>0 else "-"
            ry_s=f"{ry:.1f}" if ry!=0 else "-"
            x(f"|{i}|{r['code']}|{r['name']}|{r.get('layer','')}|{pr:.2f}|{pe_s}|{pbv:.2f}|{roe:.1f}|{gm:.1f}|{mv_s}|{ry_s}|")
        x("")
    x("## \u6570\u636e\u65f6\u6548"); x("")
    x(f"-\u884c\u60c5:{T}\u5b9e\u65f6")
    x("-\u8d22\u62a5:\u6700\u65b0\u5b63\u62a5"); x("")
    x("> \u4ec5\u4f5c\u4fe1\u606f\u8ddf\u8e2a\uff0c\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\u3002")
    body="\n".join(c)
    with open(p,"w",encoding="utf-8") as f: f.write(body)
    print(f"MD: {os.path.basename(p)} ({len(body)}c)")

def gen_html(pools,pe_m,pb_m,rows):
    p=J(R,f"{T}-asi-scan-report.html")
    cs=[("c","#e3f2fd","#1565c0","\u6838\u5fc3\u58c1\u5792\u6c60"),("l","#e8f5e9","#2e7d32","\u4f4e\u4f30\u503c\u6c60"),
        ("h","#fce4ec","#c62828","\u9ad8\u589e\u957f\u6c60"),("s","#f3e5f5","#7b1fa2","\u4ea7\u4e1a\u94fe\u9f99\u5934\u6c60"),
        ("p","#fff3e0","#e65100","\u7535\u529b\u4e0a\u6e38\u6c60")]
    css="""*{margin:0;padding:0;box-sizing:border-box}\nbody{font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;background:#f0f2f5;color:#333;padding:20px}\n.c{max-width:1200px;margin:0 auto}\nh1{font-size:24px;color:#1a1a2e;margin-bottom:5px}\n.sub{color:#666;font-size:14px;margin-bottom:20px}\n.grid{display:flex;gap:12px;margin-bottom:25px;flex-wrap:wrap}\n.card{background:#fff;border-radius:10px;padding:15px 20px;flex:1;min-width:130px;box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center}\n.card .n{font-size:28px;font-weight:700;color:#1a1a2e}\n.card .l{font-size:12px;color:#888}\n.pc{background:#fff;border-radius:10px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden}\n.ph{padding:12px 20px;font-size:15px;font-weight:600}\n.pb{padding:12px 20px;overflow-x:auto}\ntable{width:100%;border-collapse:collapse;font-size:13px}\nth{background:#f8f9fa;padding:8px 6px;text-align:left;border-bottom:2px solid #dee2e6;white-space:nowrap}\ntd{padding:6px;border-bottom:1px solid #eee}\ntr:hover{background:#f0f4ff}\n.f{text-align:center;color:#999;font-size:12px;margin:30px 0}"""
    ht=[]; x=ht.append
    x("<!DOCTYPE html>")
    x('<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">')
    x(f"<title>A\u80a1AI\u534a\u5bfc\u4f53\u626b\u63cf {T}</title><style>{css}</style></head>")
    x('<body><div class="c">')
    x("<h1>A\u80a1AI\u534a\u5bfc\u4f53 \u4f4e\u4f30\u503c+\u9ad8\u58c1\u5792\u5168\u4ea7\u4e1a\u94fe\u626b\u63cf</h1>")
    x(f'<p class="sub">{T} | {len(rows)} | PE\u4e2d\u4f4d\u6570:{pe_m:.1f} | PB\u4e2d\u4f4d\u6570:{pb_m:.2f}</p>')
    x('<div class="grid">')
    for pk,_,_,cn in cs:
        x(f'<div class="card"><div class="n">{len(pools[pk])}</div><div class="l">{cn}</div></div>')
    x('</div>')
    for pk,bg,fc,cn in cs:
        po=pools[pk]
        x(f'<div class="pc"><div class="ph" style="background:{bg};color:{fc}">{cn} ({len(po)})</div><div class="pb">')
        if po:
            x("<table><tr><th>Code</th><th>Name</th><th>Layer</th><th>Price</th><th>PE</th><th>PB</th><th>ROE%</th><th>GM%</th><th>MktCap</th><th>RevYoY%</th></tr>")
            for r in po:
                mv=sf(r.get("total_mv"))
                mv_s="-" if mv<=0 else f"{mv/1e8:.1f}\u4ebf"
                x(f"<tr><td>{r['code']}</td><td>{r['name']}</td><td>{r.get('layer','')}</td>"
                  f"<td>{sf(r.get('price')):.2f}</td><td>{sf(r.get('pe_ttm')):.1f}</td>"
                  f"<td>{sf(r.get('pb')):.2f}</td><td>{sf(r.get('roe')):.1f}</td>"
                  f"<td>{sf(r.get('gross_margin')):.1f}</td><td>{mv_s}</td><td>{sf(r.get('rev_yoy')):.1f}</td></tr>")
            x("</table>")
        else:
            x("<p><em>\u6682\u65e0</em></p>")
        x('</div></div>')
    x('<div class="f">\u4ec5\u4f5c\u4fe1\u606f\u8ddf\u8e2a\uff0c\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\u3002</div></div></body></html>')
    body="\n".join(ht)
    with open(p,"w",encoding="utf-8") as f: f.write(body)
    print(f"HTML: {os.path.basename(p)} ({len(body)}c)")

if __name__=="__main__":
    print("="*50)
    print(f"006 Pool Classifier - {T}")
    print("="*50)
    rows=load()
    pools,pe_m,pb_m,ly=classify(rows)
    for k,fn in [("c","core-moat"),("l","low-val"),("h","high-growth"),("s","sector-leader"),("p","power-upstream")]:
        print(f"  {fn}: {len(pools[k])}")
    save_csvs(pools)
    gen_md(pools,pe_m,pb_m,rows)
    gen_html(pools,pe_m,pb_m,rows)
    print("="*50)
