# -*- coding: utf-8 -*-
"""Fast valuation from layer data. PE percentile uses layer-rank (proxy), not historical 52w PE."""
import sys, os, csv, datetime
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(__file__))
RAW = os.path.join(BASE, "vault", "raw", "agent")
TODAY = datetime.date.today().strftime("%Y-%m-%d")

def sf(v, d=0.0):
    try: return float(v) if v else d
    except: return d

def layer_pe_percentile(pe, all_layer_pes):
    """Compute PE percentile by rank within layer (proxy, not historical)."""
    valid = sorted([v for v in all_layer_pes if 0 < v < 500])
    if not valid or pe <= 0:
        return None, False
    rank = sum(1 for v in valid if v <= pe)
    pct = round(rank / len(valid) * 100, 1)
    return pct, True  # value, is_proxy

def main():
    l1_path = os.path.join(RAW, f"{TODAY}-asi-layer-l1-full.csv")
    if not os.path.exists(l1_path):
        yd = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        l1_path = os.path.join(RAW, f"{yd}-asi-layer-l1-full.csv")
    l1 = {}
    with open(l1_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            l1[row["code"]] = row

    # Collect layer PE distributions
    layer_pes = defaultdict(list)
    for r in l1.values():
        pe = sf(r.get("pe_ttm"))
        if 0 < pe < 500:
            layer_pes[r.get("layer","")].append(pe)

    layer_med = {}
    for lay, vals in layer_pes.items():
        v = sorted(vals)
        layer_med[lay] = v[len(v)//2] if v else 0

    results = []
    for code, row in l1.items():
        pe = sf(row.get("pe_ttm"))
        layer = row.get("layer", "")
        
        # PE percentile: layer-rank proxy (not historical)
        pe_pct, is_proxy = layer_pe_percentile(pe, layer_pes.get(layer, []))
        pe_pct_val = pe_pct if pe_pct is not None else 50.0
        
        # Layer median
        lm = layer_med.get(layer, 0)
        
        # Layer z-score
        vals = sorted([v for v in layer_pes.get(layer, []) if 0 < v < 500])
        z = 0
        if len(vals) >= 3 and 0 < pe < 500:
            avg = sum(vals) / len(vals)
            std = (sum((p-avg)**2 for p in vals) / len(vals))**0.5
            z = round((pe - avg) / std, 2) if std > 0 else 0
        
        results.append({
            "code": code,
            "name": row.get("name", ""),
            "layer": layer,
            "pe_current": pe,
            "pe_pct": round(pe_pct_val, 1),
            "pe_pct_proxy": str(is_proxy).lower(),
            "layer_pe_median": lm,
            "layer_z_pe": z
        })

    outpath = os.path.join(RAW, f"{TODAY}-asi-valuation.csv")
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["code","name","layer","pe_current","pe_pct","pe_pct_proxy","layer_pe_median","layer_z_pe"], extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    
    proxy_count = sum(1 for r in results if r["pe_pct_proxy"] == "true")
    none_count = sum(1 for r in results if r["pe_pct"] == 50.0 and r["pe_pct_proxy"] == "false" and r["pe_current"] <= 0)
    print(f"[OK] {len(results)} records -> {os.path.basename(outpath)}")
    print(f"     PE百分位: 代理值={proxy_count}只, 亏损股标记50%={none_count}只")

if __name__ == "__main__":
    main()
