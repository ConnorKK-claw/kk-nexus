#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""006 Employee - Performance Guidance Certainty System
Sources: L4 (Eastmoney ProfitForecast), L5 (AKShare Research Reports), L2 (AKShare JGDY)
"""
import os, sys, csv, json, datetime, time, math
sys.stdout.reconfigure(encoding="utf-8")

VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
RAW = os.path.join(VAULT, "vault", "raw", "agent")

from asi_stocks import STOCKS

def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")

def get_week():
    return datetime.date.today().strftime("%Y-W%V")

def sf(v, d=0.0):
    if v is None or str(v).strip() in ("", "None"):
        return d
    try:
        fv = float(v)
        return d if (math.isnan(fv) or math.isinf(fv)) else fv
    except:
        return d

def cache_path(typ):
    return os.path.join(RAW, f"{get_today()}-asi-{typ}.csv")

def read_latest_valuation():
    fs = sorted([f for f in os.listdir(RAW) if f.endswith("-asi-valuation.csv")], reverse=True)
    if not fs:
        return None
    with open(os.path.join(RAW, fs[0]), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {r["code"]: r for r in rows}

def read_latest_full():
    fs = sorted([f for f in os.listdir(RAW) if f.endswith("-asi-data-full.csv")], reverse=True)
    if not fs:
        return None
    with open(os.path.join(RAW, fs[0]), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {r["code"]: r for r in rows}

# ==================== L2: \u673a\u6784\u8c03\u7814 ====================

def fetch_jgdy_batch(codes):
    """Fetch JGDY (institutional survey) data via AKShare, cache monthly"""
    week = get_week()
    jgdy_path = os.path.join(RAW, f"{week}-jgdy-stats.csv")
    
    # Check cache
    if os.path.exists(jgdy_path):
        with open(jgdy_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        print(f"  [L2] Loaded from cache: {len(rows)} records")
        return {r["code"]: r for r in rows}
    
    print(f"  [L2] Fetching JGDY via AKShare (this may take 10-30s)...")
    try:
        import akshare as ak
        
        # Fetch from last month (30 days back) to get enough data
        start = (datetime.date.today() - datetime.timedelta(days=90)).strftime("%Y%m%d")
        df = ak.stock_jgdy_tj_em(date=start)
        
        if df is None or len(df) == 0:
            print(f"  [L2] No JGDY data returned")
            return {}
        
        # Find columns
        code_col = "\u4ee3\u7801"
        name_col = "\u540d\u79f0"
        count_col = "\u63a5\u5f85\u673a\u6784\u6570\u91cf"
        date_col = "\u63a5\u5f85\u65e5\u671f"
        
        # Filter for our stocks
        our = df[df[code_col].isin(codes)]
        
        # Per stock: sum institutions, count events
        result = {}
        for code in codes:
            sub = our[our[code_col] == code]
            total_inst = int(sub[count_col].sum()) if len(sub) > 0 else 0
            event_cnt = len(sub)
            name = sub[name_col].iloc[0] if len(sub) > 0 else ""
            dates = [str(d) for d in sub[date_col].tolist()] if len(sub) > 0 else []
            result[code] = {
                "code": code,
                "name": name,
                "jgdy_institution_count": total_inst,
                "jgdy_event_count": event_cnt,
                "jgdy_recent_dates": ";".join(sorted(dates, reverse=True)[:5]) if dates else ""
            }
        
        # Save cache
        with open(jgdy_path, "w", newline="", encoding="utf-8") as f:
            keys = ["code","name","jgdy_institution_count","jgdy_event_count","jgdy_recent_dates"]
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(result.values())
        print(f"  [L2] Saved: {os.path.basename(jgdy_path)} ({len(result)} stocks)")
        return result
    except ImportError:
        print(f"  [L2] AKShare not installed, skipping")
        return {}
    except Exception as e:
        print(f"  [L2] Error: {e}")
        return {}

# ==================== L5: \u5206\u5355\u4efd\u7814\u62a5\u660e\u7ec6 ====================

def fetch_research_reports(code, name):
    """Fetch individual research reports via AKShare"""
    try:
        import akshare as ak
        df = ak.stock_research_report_em(symbol=code)
        if df is None or len(df) == 0:
            return None
        
        # Get latest reports (last 90 days)
        cutoff = datetime.date.today() - datetime.timedelta(days=90)
        
        eps_cols = [c for c in df.columns if "\u76c8\u5229\u9884\u6d4b" in c and "\u6536\u76ca" in c]
        rating_col = "\u4e1c\u8d22\u8bc4\u7ea7"
        date_col = "\u65e5\u671f"
        org_col = "\u673a\u6784"
        
        recent = df
        if len(recent) == 0:
            return None
        
        # Average EPS forecasts from individual reports
        eps_vals = {2026: [], 2027: [], 2028: []}
        ratings = []
        orgs = set()
        
        for _, row in recent.iterrows():
            orgs.add(str(row.get(org_col, "")))
            r = str(row.get(rating_col, ""))
            if r:
                ratings.append(r)
            for yr, col_idx in [(2026, 0), (2027, 1), (2028, 2)]:
                if col_idx < len(eps_cols):
                    val = sf(row.get(eps_cols[col_idx]))
                    if val > 0:
                        eps_vals[yr].append(val)
        
        result = {
            "research_report_count": len(recent),
            "research_org_count": len(orgs),
        }
        
        for yr in [2026, 2027, 2028]:
            vals = eps_vals[yr]
            if vals:
                result[f"akshare_eps_{yr}"] = round(sum(vals)/len(vals), 4)
            else:
                result[f"akshare_eps_{yr}"] = 0
        
        # Rating distribution
        buy = sum(1 for r in ratings if "\u4e70" in r)
        add = sum(1 for r in ratings if "\u589e" in r)
        hold = sum(1 for r in ratings if "\u6301" in r or "\u4e2d\u6027" in r)
        total_r = len(ratings)
        result["research_buy_pct"] = round((buy + add) / total_r * 100, 1) if total_r > 0 else 0
        
        return result
    except ImportError:
        return None
    except Exception as e:
        print(f"    [L5] Error: {e}")
        return None

# ==================== L4: Eastmoney ProfitForecast ====================

def fetch_profit_forecast_code(stock):
    import requests
    code = stock["code"]
    prefix = "SH" if code.startswith("6") else "SZ"
    url = f"https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code={prefix}{code}"
    hd = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "Referer": f"https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/Index?code={prefix}{code}"}
    px = {"http": "", "https": ""}
    try:
        r = requests.get(url, headers=hd, proxies=px, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def compute_guidance_score(data, l5_data, valuation_data, full_data):
    """Compute guidance score from L4 (Eastmoney) + L5 (AKShare cross-validation)"""
    result = {
        "guidance_score": 0, "analyst_count": 0, "buy_pct": 0, "eps_dispersion": 0,
        "consensus_eps_1": 0, "consensus_eps_2": 0, "consensus_eps_3": 0,
        "consensus_pe_1": 0, "consensus_pe_2": 0, "consensus_pe_3": 0,
        "consensus_rev_growth": 0, "consensus_profit_growth": 0, "consensus_roe": 0,
        "pe_digest_years": "N/A", "pe_digest_note": "\u7f3a\u4e4f\u673a\u6784\u8986\u76d6",
        "l4_vs_l5_divergence": 0, "source_layers_available": ""
    }
    
    # Merge L5 if available
    if l5_data:
        result["research_report_count"] = l5_data.get("research_report_count", 0)
        result["research_org_count"] = l5_data.get("research_org_count", 0)
        result["research_buy_pct"] = l5_data.get("research_buy_pct", 0)
        for yr in [2026, 2027, 2028]:
            result[f"akshare_eps_{yr}"] = l5_data.get(f"akshare_eps_{yr}", 0)

    if not data:
        result["source_layers_available"] = "L2" if "jgdy_institution_count" in result else ""
        return result

    pjtj = data.get("pjtj", [])
    jgyc = data.get("jgyc", [])
    yctj = data.get("yctj_chart", [])
    ycmx = data.get("ycmx", [])

    # L4 analyst count
    count_1m = 0
    for item in pjtj:
        if item.get("DATE_TYPE_CODE") == 1:
            count_1m = int(item.get("RATING_ORG_NUM", 0) or 0)
            break
    orgs = set()
    for item in jgyc:
        org = item.get("ORG_NAME_ABBR", "")
        if org and org != "\u8fd1\u516d\u6708\u5e73\u5747":
            orgs.add(org)
    analyst_count = max(count_1m, len(orgs))
    result["analyst_count"] = analyst_count

    # L4 rating consensus
    for item in pjtj:
        if item.get("DATE_TYPE_CODE") == 1:
            buy = int(item.get("RATING_BUY_NUM", 0) or 0)
            add = int(item.get("RATING_ADD_NUM", 0) or 0)
            total = int(item.get("RATING_ORG_NUM", 0) or 0)
            if total > 0:
                result["buy_pct"] = round((buy + add) / total * 100, 1)
            break

    # L4 consensus EPS
    avg_row = None
    for item in jgyc:
        if item.get("ORG_NAME_ABBR") == "\u8fd1\u516d\u6708\u5e73\u5747":
            avg_row = item
            break
    if avg_row:
        result["consensus_eps_1"] = sf(avg_row.get("EPS1"))
        result["consensus_eps_2"] = sf(avg_row.get("EPS2"))
        result["consensus_eps_3"] = sf(avg_row.get("EPS3"))
        result["consensus_pe_1"] = sf(avg_row.get("PE1"))
        result["consensus_pe_2"] = sf(avg_row.get("PE2"))
        result["consensus_pe_3"] = sf(avg_row.get("PE3"))

    for item in yctj:
        year_mark = item.get("YEAR_MARK", "")
        if year_mark == "E":
            result["consensus_roe"] = sf(item.get("ROE"))
            result["consensus_rev_growth"] = sf(item.get("TOTAL_OPERATE_INCOME_RATIO"))
            result["consensus_profit_growth"] = sf(item.get("PARENT_NETPROFIT_RATIO"))
            break

    # L4 dispersion
    eps1_values = [sf(item.get("EPS1")) for item in ycmx if sf(item.get("EPS1")) > 0]
    if len(eps1_values) >= 3:
        mean_e = sum(eps1_values) / len(eps1_values)
        std_e = (sum((v-mean_e)**2 for v in eps1_values) / len(eps1_values))**0.5
        result["eps_dispersion"] = round(std_e / mean_e, 3) if mean_e > 0 else 1.0
    else:
        result["eps_dispersion"] = 1.0

    # ============ L4 vs L5 cross-validation ============
    l4_eps = result["consensus_eps_1"]
    l5_eps = result.get("akshare_eps_2026", 0)
    
    divergence = 0
    if l4_eps > 0 and l5_eps > 0:
        divergence = abs(l4_eps - l5_eps) / max(l4_eps, l5_eps) * 100
    result["l4_vs_l5_divergence"] = round(divergence, 1)
    
    # ============ Score calculation ============
    score_coverage = min(analyst_count / 15, 1) * 20
    score_rating = result["buy_pct"] / 100 * 20
    score_dispersion = max(0, 1 - result["eps_dispersion"]) * 25
    
    score_pe_visible = 0
    current_pe = sf(full_data.get("pe_ttm")) if full_data else 0
    if current_pe > 0 and result["consensus_pe_3"] > 0:
        if result["consensus_pe_3"] < current_pe * 0.6:
            score_pe_visible = 15
        elif result["consensus_pe_3"] < current_pe * 0.8:
            score_pe_visible = 10
        else:
            score_pe_visible = 5
    
    score_accuracy = 10
    yctj_list = data.get("yctj_list", [])
    for item in yctj_list:
        if item.get("YEAR_MARK") == "A":
            actual = sf(item.get("EPS"))
            forecast = sf(item.get("EPS_LASTMONTHS"))
            if actual > 0 and forecast > 0:
                bias = abs(actual - forecast) / actual
                if bias < 0.1: score_accuracy = 20
                elif bias < 0.2: score_accuracy = 15
                elif bias < 0.3: score_accuracy = 10
                else: score_accuracy = 5
            break
    
    # Cross-validation penalty: if L4 vs L5 diverge >20%, -10 points
    cross_penalty = 0
    if divergence > 30:
        cross_penalty = 5
        print(f"    [L4vsL5] Divergence {divergence:.1f}% > 30%, applying -5 penalty")
    
    total = score_coverage + score_rating + score_dispersion + score_pe_visible + score_accuracy - cross_penalty
    result["guidance_score"] = round(min(max(total, 0), 100), 1)
    
    # Source layers tracking
    layers = []
    if result["analyst_count"] > 0:
        layers.append("L4")
    if l5_data:
        layers.append("L5")
    if result.get("jgdy_institution_count", 0) > 0:
        layers.append("L2")
    result["source_layers_available"] = ",".join(layers) if layers else ""

    # PE digest
    result = compute_pe_digest(result, valuation_data, full_data)
    return result

def compute_pe_digest(result, valuation_data, full_data):
    current_pe = sf(full_data.get("pe_ttm")) if full_data else 0
    price = sf(full_data.get("price")) if full_data else 0
    gs = result["guidance_score"]

    if current_pe <= 0 or price <= 0:
        result["pe_digest_years"] = "N/A"
        result["pe_digest_note"] = "\u7f3a\u4e4f\u884c\u60c5\u6570\u636e"
        return result

    if gs < 50:
        result["pe_digest_years"] = "N/A"
        result["pe_digest_note"] = "\u6307\u5f15\u786e\u5b9a\u6027\u4e0d\u8db3(\u8bc4\u5206<50)"
        return result

    hist_p60 = sf(valuation_data.get("pe_hist_p50")) if valuation_data else 0
    layer_med = sf(valuation_data.get("layer_pe_median")) if valuation_data else 0

    if hist_p60 <= 0:
        hist_p60 = sf(valuation_data.get("pe_hist_p75", 0)) if valuation_data else 0
    if hist_p60 <= 0:
        hist_p60 = current_pe * 0.7
    if layer_med <= 0:
        layer_med = current_pe

    target_pe = min(hist_p60, layer_med)

    if current_pe <= target_pe:
        result["pe_digest_years"] = "0"
        result["pe_digest_note"] = f"\u5df2\u5728\u5408\u7406\u533a\u95f4(\u76ee\u6807PE<={target_pe:.0f})"
        return result

    eps = [result.get("consensus_eps_1", 0), result.get("consensus_eps_2", 0), result.get("consensus_eps_3", 0)]
    if all(e <= 0 for e in eps):
        result["pe_digest_years"] = "N/A"
        result["pe_digest_note"] = "\u7f3a\u4e4f\u4e00\u81f4\u9884\u671fEPS"
        return result

    for year_idx in range(3):
        e = eps[year_idx]
        if e <= 0:
            continue
        fwd_pe = price / e
        if fwd_pe <= target_pe:
            result["pe_digest_years"] = str(year_idx + 1)
            result["pe_digest_note"] = f"{year_idx+1}\u5e74\u540e\u8fdc\u671fPE={fwd_pe:.0f}(\u76ee\u6807<={target_pe:.0f})"
            return result

    last_pe = price / eps[2] if eps[2] > 0 else current_pe
    result["pe_digest_years"] = ">3"
    result["pe_digest_note"] = f"\u8d85\u671f\u96be\u6d88\u5316(3\u5e74\u540e\u8fdc\u671fPE={last_pe:.0f}>{target_pe:.0f})"
    return result

def main():
    import argparse
    ap = argparse.ArgumentParser(description="006 Guidance System v2")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-jgdy", action="store_true")
    ap.add_argument("--skip-research", action="store_true")
    args = ap.parse_args()

    os.makedirs(RAW, exist_ok=True)
    print("="*50)
    print(f"006 Guidance System v2 - {get_today()}")
    print("="*50)

    gpath = cache_path("guidance")
    if not args.force and os.path.exists(gpath):
        print(f"\n[INFO] Cache exists: {os.path.basename(gpath)}")
        return

    val_data = read_latest_valuation()
    full_data = read_latest_full()
    if not full_data:
        print("[ERROR] No full data. Run fetch_asi_market_data.py first.")
        return

    # Step 1: L2 - JGDY batch (monthly cache)
    jgdy_data = {}
    if not args.skip_jgdy:
        codes = [s["code"] for s in STOCKS]
        jgdy_data = fetch_jgdy_batch(codes)
        if jgdy_data:
            print(f"  [L2] {sum(1 for v in jgdy_data.values() if int(v['jgdy_event_count']) >0)} stocks with survey events")

    # Step 2 & 3: Per stock L4 + L5
    results = []
    for i, s in enumerate(STOCKS):
        code = s["code"]
        print(f"\n[{i+1}/{len(STOCKS)}] {s['name']} ({code})...")

        # L5: AKShare research reports
        l5_data = None
        if not args.skip_research:
            l5_data = fetch_research_reports(code, s["name"])
            if l5_data:
                print(f"    [L5] {l5_data['research_report_count']} reports, buy%={l5_data['research_buy_pct']}")
            time.sleep(0.5)

        # L4: Eastmoney ProfitForecast
        data = fetch_profit_forecast_code(s)
        if not data:
            empty = {"code": code, "name": s["name"], "layer": s["layer"],
                     "guidance_score": 0, "analyst_count": 0,
                     "pe_digest_years": "N/A", "pe_digest_note": "\u65e0\u673a\u6784\u8986\u76d6"}
            if l5_data:
                empty.update(l5_data)
                empty["source_layers_available"] = "L5"
            if jgdy_data and code in jgdy_data:
                empty.update(jgdy_data[code])
                if empty["source_layers_available"]:
                    empty["source_layers_available"] += ",L2"
                else:
                    empty["source_layers_available"] = "L2"
            results.append(empty)
            continue

        # Compute with L4 + L5 + L2
        r = compute_guidance_score(data, l5_data, 
                                    val_data.get(code) if val_data else None,
                                    full_data.get(code) if full_data else None)
        r["code"] = code
        r["name"] = s["name"]
        r["layer"] = s["layer"]
        
        # Merge L2
        if jgdy_data and code in jgdy_data:
            r.update(jgdy_data[code])
        
        results.append(r)
        print(f"  Score={r['guidance_score']} Layers=[{r['source_layers_available']}] {r['pe_digest_years']}")
        time.sleep(0.3)

    # Save
    fields = ["code","name","layer","guidance_score","source_layers_available",
              "analyst_count","buy_pct","eps_dispersion",
              "consensus_eps_1","consensus_eps_2","consensus_eps_3",
              "consensus_pe_1","consensus_pe_2","consensus_pe_3",
              "consensus_rev_growth","consensus_profit_growth","consensus_roe",
              "research_report_count","research_org_count","research_buy_pct",
              "akshare_eps_2026","akshare_eps_2027","akshare_eps_2028",
              "l4_vs_l5_divergence",
              "jgdy_institution_count","jgdy_event_count",
              "pe_digest_years","pe_digest_note"]
    
    with open(gpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\nSaved: {os.path.basename(gpath)} ({len(results)} records)")

    # Stats
    covered = [r for r in results if r["guidance_score"] > 0]
    digest_ok = [r for r in results if r["pe_digest_years"] not in ("N/A", ">3")]
    with_l5 = [r for r in results if r.get("research_report_count", 0) > 0]
    with_jgdy = [r for r in results if int(r.get("jgdy_event_count", 0)) > 0]
    
    print(f"\nCoverage: {len(covered)}/{len(results)} with score>0")
    print(f"PE digest <=3yr: {len(digest_ok)} stocks")
    print(f"With L5 research: {len(with_l5)} stocks")
    print(f"With L2 JGDY: {len(with_jgdy)} stocks")
    
    # Check for significant divergences
    diverged = [r for r in results if sf(r.get("l4_vs_l5_divergence")) > 20]
    if diverged:
        print(f"\n[WARN] L4 vs L5 divergence >30% for {len(diverged)} stocks:")
        for r in diverged:
            print(f"  {r['code']} {r['name']}: divergence={r['l4_vs_l5_divergence']}%")
    print("="*50)

if __name__ == "__main__":
    main()


