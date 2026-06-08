# -*- coding: utf-8 -*-
"""
006 Employee - Run Layer Batch
Crawl L1-L5 data for a specific industry layer.
Usage: python run_layer_batch.py --layer "半导体设备" [--l1] [--l2] [--l3] [--l4] [--l5] [--skip-cache]
"""
import sys, os, csv, datetime, json, time, subprocess
sys.stdout.reconfigure(encoding="utf-8")

VAULT = "C:/Users/hexk/.codex/skills/serenity-a-share-investor"
SCRIPTS = os.path.join(VAULT, "scripts")
RAW = "C:/Users/hexk/.codex/skills/serenity-a-share-investor/vault/raw/agent"
TODAY = datetime.date.today().strftime("%Y-%m-%d")

sys.path.insert(0, SCRIPTS)
from asi_stocks import STOCKS

def get_stocks_by_layer(layer_name):
    result = []
    for s in STOCKS:
        if s["layer"].startswith(layer_name):
            result.append(s)
    return result

def write_layer_csv(layer_slug, data_tag, rows):
    os.makedirs(RAW, exist_ok=True)
    path = f"{RAW}/{TODAY}-asi-layer-{layer_slug}-{data_tag}.csv"
    if not rows:
        print(f"  [SKIP] {path} - no data")
        return None
    fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [SAVE] {path} ({len(rows)} records)")
    return path

def run_l1_l3_batch(stocks, layer_slug):
    import requests
    px = {"http": "", "https": ""}
    hd = {"User-Agent": "Mozilla/5.0"}
    sh_codes = [s["code"] for s in stocks if s["secid"].startswith("1")]
    sz_codes = [s["code"] for s in stocks if s["secid"].startswith("0")]
    all_q = "sh" + ",sh".join(sh_codes) if sh_codes else ""
    if sz_codes: all_q += ",sz" + ",sz".join(sz_codes)
    url = f"http://qt.gtimg.cn/q={all_q}"
    try:
        resp = requests.get(url, headers=hd, proxies=px, timeout=15)
        resp.encoding = "gbk"
        text = resp.text
    except Exception as e:
        print(f"  ERROR fetching L1: {e}")
        return [], []
    l1_rows = []
    l3_rows = []
    for line in text.strip().split("\n"):
        if not line.strip(): continue
        try:
            start = line.find('"')
            end = line.rfind('"')
            if start < 0 or end <= start: continue
            parts = line[start+1:end].split("~")
            if len(parts) < 48: continue
            code = parts[2]
            name = parts[1]
            price = float(parts[3]) if parts[3] else 0
            pe = float(parts[39]) if parts[39] else 0
            pb = float(parts[46]) if parts[46] else 0
            total_cap = float(parts[45]) if parts[45] and parts[45] != "0" else 0
            flow_cap = float(parts[44]) if parts[44] else 0
            cap = total_cap if total_cap > 0 else flow_cap
            amplitude = float(parts[43]) if parts[43] else 0
            turnover = float(parts[38]) if parts[38] else 0
            high = float(parts[33]) if parts[33] else 0
            low = float(parts[34]) if parts[34] else 0
            open_p = float(parts[5]) if parts[5] else 0
            pre_close = float(parts[4]) if parts[4] else 0
            change_pct = float(parts[32]) if parts[32] else 0
            amount = float(parts[37]) if parts[37] else 0
            high_52w = float(parts[47]) if parts[47] else 0
            low_52w = float(parts[48]) if parts[48] else 0
            l1_rows.append({
                "code": code, "name": name, "layer": layer_slug,
                "price": price, "pe_ttm": pe, "pb": pb,
                "mkt_cap": cap, "mkt_cap_flow": flow_cap,
                "change_pct": change_pct, "turnover": turnover,
                "amount": amount, "amplitude": amplitude,
                "high": high, "low": low, "open": open_p,
                "pre_close": pre_close, "high_52w": high_52w, "low_52w": low_52w,
            })
            if high_52w > 0 and low_52w > 0 and pe > 0:
                l3_rows.append({
                    "code": code, "name": name, "layer": layer_slug,
                    "pe": pe, "high_52w": high_52w, "low_52w": low_52w,
                })
        except:
            continue
    return l1_rows, l3_rows

def run_l2_batch(stocks, layer_slug):
    import requests
    px = {"http": "", "https": ""}
    hd = {"User-Agent": "Mozilla/5.0"}
    rows = []
    for i, s in enumerate(stocks):
        code = s["code"]
        suffix = "SH" if s["secid"].startswith("1") else "SZ"
        su = f"{code}.{suffix}"
        url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get?"
               f"reportName=RPT_LICO_FN_CPD&columns=SECUCODE,SECURITY_NAME_ABBR,"
               f"REPORTDATE,BASIC_EPS,WEIGHTAVG_ROE,TOTAL_OPERATE_INCOME,"
               f"PARENT_NETPROFIT,XSMLL,YSTZ,SJLTZ&"
               f"filter=(SECUCODE=%22{su}%22)&pageNumber=1&pageSize=1&"
               f"sortTypes=-1&sortColumns=NOTICE_DATE&source=HSF10&client=WEB")
        try:
            resp = requests.get(url, headers=hd, proxies=px, timeout=10)
            data = resp.json()
            if data.get("result") and data["result"]["data"]:
                d = data["result"]["data"][0]
                rows.append({
                    "code": code, "name": s["name"], "layer": layer_slug,
                    "roe": d.get("WEIGHTAVG_ROE", ""),
                    "gross_margin": d.get("XSMLL", ""),
                    "revenue": d.get("TOTAL_OPERATE_INCOME", ""),
                    "revenue_yoy": d.get("YSTZ", ""),
                    "net_profit": d.get("PARENT_NETPROFIT", ""),
                    "profit_yoy": d.get("SJLTZ", ""),
                    "eps": d.get("BASIC_EPS", ""),
                    "report_date": d.get("REPORTDATE", ""),
                })
        except:
            pass
        if (i + 1) % 10 == 0:
            print(f"  L2 progress: {i+1}/{len(stocks)}")
        time.sleep(0.3)
    return rows

def run_l4_batch(stocks, layer_slug):
    """L4: Consensus EPS forecast from Eastmoney."""
    import requests
    px = {"http": "", "https": ""}
    hd = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "Referer": "https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/Index"}
    rows = []

    def sf(v):
        try: return float(v) if v else 0.0
        except: return 0.0

    for i, s in enumerate(stocks):
        code = s["code"]
        prefix = "SH" if code.startswith("6") else "SZ"
        code_secid = f"{prefix}{code}"
        url = (f"https://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/PageAjax?code={code_secid}")
        try:
            resp = requests.get(url, headers=hd, proxies=px, timeout=15)
            data = resp.json()
            # API returns {pjtj:[], jgyc:[], yctj_list:[], yctj_chart:[], ycmx:[]}
            pjtj = data.get("pjtj", [])
            jgyc = data.get("jgyc", [])

            # Analyst count from pjtj (monthly)
            analyst_count = 0
            for item in pjtj:
                if item.get("DATE_TYPE_CODE") == 1:
                    analyst_count = int(item.get("RATING_ORG_NUM", 0) or 0)
                    break

            # Average consensus EPS from jgyc (近六月平均)
            avg_row = None
            for item in jgyc:
                if item.get("ORG_NAME_ABBR") == "近六月平均":
                    avg_row = item
                    break

            if avg_row:
                rows.append({
                    "code": code, "name": s["name"], "layer": layer_slug,
                    "analyst_count": analyst_count,
                    "eps_1": sf(avg_row.get("EPS1")),
                    "eps_2": sf(avg_row.get("EPS2")),
                    "eps_3": sf(avg_row.get("EPS3")),
                    "consensus_pe_1": sf(avg_row.get("PE1")),
                    "consensus_pe_2": sf(avg_row.get("PE2")),
                    "consensus_pe_3": sf(avg_row.get("PE3")),
                })
            else:
                # Fallback: use first jgyc item
                if jgyc:
                    item = jgyc[0]
                    rows.append({
                        "code": code, "name": s["name"], "layer": layer_slug,
                        "analyst_count": analyst_count,
                        "eps_1": sf(item.get("EPS1")),
                        "eps_2": sf(item.get("EPS2")),
                        "eps_3": sf(item.get("EPS3")),
                        "consensus_pe_1": sf(item.get("PE1")),
                        "consensus_pe_2": sf(item.get("PE2")),
                        "consensus_pe_3": sf(item.get("PE3")),
                    })

        except Exception as e:
            print(f"  [L4] {s['name']} error: {e}")
        if (i + 1) % 10 == 0:
            print(f"  L4 progress: {i+1}/{len(stocks)}")
        time.sleep(0.5)
    return rows

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run layer batch crawl")
    parser.add_argument("--layer", required=True, help="Layer name prefix")
    parser.add_argument("--l1", action="store_true")
    parser.add_argument("--l2", action="store_true")
    parser.add_argument("--l3", action="store_true")
    parser.add_argument("--l4", action="store_true")
    parser.add_argument("--l5", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--skip-cache", action="store_true")
    args = parser.parse_args()

    layer_name = args.layer
    stocks = get_stocks_by_layer(layer_name)
    if not stocks:
        stocks = get_stocks_by_layer(f"WIND.{layer_name}")
    if not stocks:
        print(f"ERROR: No stocks for '{layer_name}'")
        layers = {}
        for s in STOCKS:
            layers[s["layer"]] = layers.get(s["layer"], 0) + 1
        for l, c in sorted(layers.items()):
            print(f"  {l}: {c}")
        return

    layer_slug = layer_name.replace(" ", "-").replace("(", "-").replace(")", "").replace("/", "-")
    print(f"=== Layer: {layer_name} ({len(stocks)} stocks) ===")

    if args.l1 or args.all:
        print(f"\n[L1+L3] Real-time...")
        l1_rows, l3_rows = run_l1_l3_batch(stocks, layer_slug)
        write_layer_csv(layer_slug, "l1", l1_rows)
        write_layer_csv(layer_slug, "l3", l3_rows)
    if args.l2 or args.all:
        print(f"\n[L2] Financial...")
        l2_rows = run_l2_batch(stocks, layer_slug)
        write_layer_csv(layer_slug, "l2", l2_rows)
    if args.l4 or args.all:
        print(f"\n[L4] Consensus EPS...")
        l4_rows = run_l4_batch(stocks, layer_slug)
        write_layer_csv(layer_slug, "l4", l4_rows)
    if args.l5 or args.all:
        print(f"\n[L5] Not implemented in batch mode.")
    print(f"Done! {len(stocks)} stocks.")

if __name__ == "__main__":
    main()
