# -*- coding: utf-8 -*-
"""L5: AKShare batch for research reports + jigou diaoyan.
Usage:
  python l5_akshare_batch.py --codes 688041,688008  # specific stocks
  python l5_akshare_batch.py --tier2                  # all Tier2 stocks
  python l5_akshare_batch.py --power                  # power-upstream pool
  python l5_akshare_batch.py --jgdy                   # jigou diaoyan only
"""
import sys, os, csv, datetime, json
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(__file__))
RAW = os.path.join(BASE, "vault", "raw", "agent")
TODAY = datetime.date.today().strftime("%Y-%m-%d")

def sf(v, d=0):
    try: return float(v) if v else d
    except: return d

def load_tier2_codes():
    """Load Tier2 stock codes from latest tier CSV."""
    files = sorted([f for f in os.listdir(RAW) if "tier-chokepoint" in f], reverse=True)
    if not files:
        print("[ERROR] No Tier2 CSV found")
        return []
    codes = []
    with open(os.path.join(RAW, files[0]), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            codes.append(row["code"])
    return codes

def load_power_codes():
    """Load power-upstream codes."""
    files = sorted([f for f in os.listdir(RAW) if "pool-power" in f], reverse=True)
    if not files:
        print("[ERROR] No power-upstream CSV found")
        return []
    codes = []
    with open(os.path.join(RAW, files[0]), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            codes.append(row["code"])
    return codes

def fetch_research(code, name):
    """Fetch research reports for one stock via AKShare."""
    try:
        import akshare as ak
        df = ak.stock_research_report_em(code)
        if df is None or df.empty:
            return None
        reports = df.to_dict("records")
        # Count: total reports, unique orgs, buy ratio
        total = len(reports)
        orgs = df["org_name"].nunique() if "org_name" in df.columns else 0
        # Get latest EPS forecasts from reports
        eps_2026 = sf(df.iloc[0].get("forecast_eps_2026", 0)) if total > 0 and "forecast_eps_2026" in df.columns else 0
        eps_2027 = sf(df.iloc[0].get("forecast_eps_2027", 0)) if total > 0 and "forecast_eps_2027" in df.columns else 0
        eps_2028 = sf(df.iloc[0].get("forecast_eps_2028", 0)) if total > 0 and "forecast_eps_2028" in df.columns else 0
        # Buy ratio
        buy_count = len(df[df["rating"] == "买入"]) if "rating" in df.columns else 0
        buy_pct = round(buy_count / total * 100, 1) if total > 0 else 0
        return {
            "research_report_count": total,
            "research_org_count": int(orgs),
            "research_buy_pct": buy_pct,
            "akshare_eps_2026": eps_2026,
            "akshare_eps_2027": eps_2027,
            "akshare_eps_2028": eps_2028,
        }
    except Exception as e:
        print(f"    [WARN] AKShare error for {code} {name}: {e}")
        return None

def fetch_jgdy():
    """Fetch institutional survey data for all stocks."""
    try:
        import akshare as ak
        df = ak.stock_jgdy_tj_em(date='20260101')
        if df is None or df.empty:
            return {}
        result = {}
        for _, row in df.iterrows():
            code = str(row.get("股票代码", ""))
            if code:
                result[code] = {
                    "jgdy_institution_count": int(row.get("累计接待机构数", 0)),
                    "jgdy_event_count": int(row.get("累计调研次数", 0)),
                }
        print(f"  [JGDY] {len(result)} stocks with survey data")
        return result
    except Exception as e:
        print(f"  [WARN] JGDY error: {e}")
        return {}

def update_guidance_csv(code, l5_data, jgdy_data):
    """Merge L5 data into existing guidance CSV."""
    # Find latest guidance CSV
    files = sorted([f for f in os.listdir(RAW) if f"{TODAY}-asi-guidance" in f], reverse=True)
    if not files:
        # Try yesterday
        yd = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        files = sorted([f for f in os.listdir(RAW) if f"{yd}-asi-guidance" in f], reverse=True)
    if not files:
        print("[ERROR] No guidance CSV to update")
        return
    
    gpath = os.path.join(RAW, files[0])
    with open(gpath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = rows[0].keys() if rows else []
    
    # Add extra fields if needed
    extra_fields = ["research_report_count","research_org_count","research_buy_pct",
                    "akshare_eps_2026","akshare_eps_2027","akshare_eps_2028",
                    "jgdy_institution_count","jgdy_event_count","source_layers_available"]
    for ef in extra_fields:
        if ef not in fields:
            fields = list(fields) + [ef]
    
    updated = 0
    for row in rows:
        c = row["code"]
        if c == code and l5_data:
            for k, v in l5_data.items():
                row[k] = v
            sl = row.get("source_layers_available", "")
            if "L5" not in sl:
                row["source_layers_available"] = (sl + ",L5").strip(",")
            updated += 1
        if c == code and jgdy_data:
            for k, v in jgdy_data.items():
                row[k] = v
            sl = row.get("source_layers_available", "")
            if "L5a" not in sl:
                row["source_layers_available"] = (sl + ",L5a").strip(",")
    
    # Write back
    tmp = gpath + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, gpath)
    return updated

def main():
    import argparse
    ap = argparse.ArgumentParser(description="L5 AKShare batch")
    ap.add_argument("--codes", help="Comma-separated stock codes")
    ap.add_argument("--tier2", action="store_true", help="All Tier2 stocks")
    ap.add_argument("--power", action="store_true", help="Power-upstream pool")
    ap.add_argument("--jgdy", action="store_true", help="Jigou diaoyan only")
    ap.add_argument("--skip-research", action="store_true")
    args = ap.parse_args()
    
    codes = []
    if args.codes:
        codes = [c.strip() for c in args.codes.split(",")]
    if args.tier2:
        codes.extend(load_tier2_codes())
    if args.power:
        codes.extend(load_power_codes())
    codes = list(set(codes))  # dedup
    
    print(f"[L5] Target codes: {len(codes)}")
    
    # JGDY batch (all at once)
    jgdy_data = {}
    if args.jgdy or (not args.skip_research and not args.jgdy):
        print("\n--- L5a: Institutional Survey ---")
        jgdy_data = fetch_jgdy()
    
    # Research reports (one by one)
    if not args.skip_research and not args.jgdy:
        print(f"\n--- L5b: Research Reports ({len(codes)} stocks) ---")
        for i, code in enumerate(codes):
            # Get name
            name = code
            for f in os.listdir(RAW):
                if f.endswith("-l1-full.csv"):
                    with open(os.path.join(RAW, f), "r", encoding="utf-8") as fh:
                        for row in csv.DictReader(fh):
                            if row["code"] == code:
                                name = row.get("name", code)
                                break
                    break
            
            print(f"  [{i+1}/{len(codes)}] {code} {name}...", end="", flush=True)
            l5 = fetch_research(code, name)
            if l5:
                upd = update_guidance_csv(code, l5, jgdy_data.get(code, {}))
                print(f" {l5['research_report_count']} reports, updated={upd}")
            else:
                update_guidance_csv(code, None, jgdy_data.get(code, {}))
                print(" no data")
            import time
            time.sleep(1)  # Rate limit
    elif args.jgdy:
        # JGDY-only mode: update all codes
        for code in codes:
            update_guidance_csv(code, None, jgdy_data.get(code, {}))
        print(f"  Updated {len(codes)} codes with JGDY data")

if __name__ == "__main__":
    main()
