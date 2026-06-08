# -*- coding: utf-8 -*-
"""Fast guidance scoring from L4 data, no per-stock API calls."""
import sys, os, csv, datetime
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(__file__))
RAW = os.path.join(BASE, "vault", "raw", "agent")
TODAY = datetime.date.today().strftime("%Y-%m-%d")

def sf(v, d=0):
    try: return float(v) if v else d
    except: return d

def main():
    # Check for today\'s or yesterday\'s data
    l4_path = os.path.join(RAW, f"{TODAY}-asi-layer-l4-full.csv")
    val_path = os.path.join(RAW, f"{TODAY}-asi-valuation.csv")
    l1_path = os.path.join(RAW, f"{TODAY}-asi-layer-l1-full.csv")
    
    if not os.path.exists(l4_path):
        yd = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        l4_path = os.path.join(RAW, f"{yd}-asi-layer-l4-full.csv")
        val_path = os.path.join(RAW, f"{yd}-asi-valuation.csv")
        l1_path = os.path.join(RAW, f"{yd}-asi-layer-l1-full.csv")
    
    l4, l1, val = {}, {}, {}
    for path, d in [(l4_path, l4), (l1_path, l1)]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    d[row["code"]] = row
    if os.path.exists(val_path):
        with open(val_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                val[row["code"]] = row

    results = []
    for code in l4:
        l4d = l4.get(code, {})
        r1 = l1.get(code, {})
        v = val.get(code, {})
        
        pe = sf(r1.get("pe_ttm"))
        price = sf(r1.get("price"))
        name = r1.get("name", "")
        layer = r1.get("layer", "")
        
        ac = int(l4d.get("analyst_count", 0) or 0)
        e1 = sf(l4d.get("eps_1"))
        e2 = sf(l4d.get("eps_2"))
        e3 = sf(l4d.get("eps_3"))
        pe_fwd = sf(l4d.get("consensus_pe_1"))
        
        # Guidance score (0-100)
        gs = 0
        if ac > 0: gs += 20
        if e1 > 0: gs += 20
        if e2 > 0: gs += 15
        if e3 > 0: gs += 15
        if pe_fwd > 0 and pe_fwd < pe: gs += 15
        if ac > 2: gs += 15
        gs = min(100, gs)
        
        # PE digest years
        pe_pct = sf(v.get("pe_pct"))
        layer_pe = sf(v.get("layer_pe_median"))
        target = min(pe_pct, layer_pe) if layer_pe > 0 else pe_pct
        digest = "N/A"
        if target > 0 and pe > 0:
            if pe <= target:
                digest = "0年(已合理)"
            elif e1 > 0 and price / ((price/pe) * (1+0.1)) <= target:
                digest = "1年"
            elif e2 > 0 and price / ((price/pe) * (1+0.25)) <= target:
                digest = "2年"
            elif e3 > 0 and price / ((price/pe) * (1+0.5)) <= target:
                digest = "3年"
            else:
                digest = ">3年(超期)"
        
        results.append({
            "code": code, "name": name, "layer": layer,
            "analyst_count": ac,
            "eps_1": e1, "eps_2": e2, "eps_3": e3,
            "guidance_score": gs,
            "pe_digest_years": digest,
            "source_layers_available": "L4",
            "pe_ttm": pe, "price": price,
        })

    outpath = os.path.join(RAW, f"{TODAY}-asi-guidance.csv")
    fields = ["code","name","layer","analyst_count","eps_1","eps_2","eps_3","guidance_score","pe_digest_years","source_layers_available","pe_ttm","price"]
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {len(results)} records -> {os.path.basename(outpath)}")
    print(f"  Analyst coverage: {sum(1 for r in results if r['analyst_count']>0)}/{len(results)}")

if __name__ == "__main__":
    main()
