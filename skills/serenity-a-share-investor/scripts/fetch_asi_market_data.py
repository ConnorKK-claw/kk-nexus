#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
006员工 - A股AI半导体全产业链数据灌注脚本
"""
import os, sys, csv, json, datetime, time
sys.stdout.reconfigure(encoding="utf-8")

VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
RAW = os.path.join(VAULT, "vault", "raw", "agent")

# 35 stocks definition
from asi_stocks import STOCKS

POWER_SET = {"300870","603290","002837"}


def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")

def cache_path(tag):
    p = os.path.join(RAW, f"{get_today()}-asi-{tag}.csv")
    return p

def has_cache():
    mp = cache_path("market-data")
    fp = cache_path("financial-data")
    if not (os.path.exists(mp) and os.path.exists(fp)):
        return False
    if os.path.getsize(mp) < 500 or os.path.getsize(fp) < 500:
        return False
    return True

def read_cache():
    md = {}
    with open(cache_path("market-data"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            md[row["code"]] = row
    fd = {}
    with open(cache_path("financial-data"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fd[row["code"]] = row
    return md, fd

def fetch_market_data():
    import requests
    px = {"http": "", "https": ""}
    hd = {"User-Agent": "Mozilla/5.0"}
    sh_codes = [s["code"] for s in STOCKS if s["secid"].startswith("1")]
    sz_codes = [s["code"] for s in STOCKS if s["secid"].startswith("0")]
    all_q = "sh" + ",sh".join(sh_codes) if sh_codes else ""
    if sz_codes:
        all_q += ",sz" + ",sz".join(sz_codes)
    url = f"http://qt.gtimg.cn/q={all_q}"
    try:
        r = requests.get(url, proxies=px, headers=hd, timeout=15)
        results = {}
        for line in r.text.strip().split(";"):
            if "=" not in line: continue
            data = line.split("=")[1].strip('"')
            if data.endswith(";"): data = data[:-1]
            f = data.split("~")
            if len(f) < 80: continue
            code = f[2]
            total_mv_raw = float(f[45]) * 1e8 if f[45] else 0
            float_mv_raw = float(f[44]) * 1e8 if f[44] else 0
            results[code] = {
                "code": code, "name": f[1],
                "price": float(f[3]) if f[3] else None,
                "pct_chg": float(f[32]) if f[32] else None,
                "change": float(f[31]) if f[31] else None,
                "high": float(f[33]) if f[33] else None,
                "low": float(f[34]) if f[34] else None,
                "open": float(f[5]) if f[5] else None,
                "total_mv": total_mv_raw,
                "float_mv": float_mv_raw,
                "pb": float(f[46]) if len(f)>46 and f[46] else None,
                "pe_ttm": float(f[62]) if len(f)>62 and f[62] else None,
                "turnover": float(f[38]) if f[38] else None,
                "amount": float(f[73]) if len(f)>73 and f[73] else None,
            }
        print(f"  Tencent API: {len(results)} records")
        return results
    except Exception as e:
        print(f"[ERROR] Tencent API: {e}")
        return {}


def fetch_financial_data():
    import requests
    hd = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "Referer": "https://emweb.securities.eastmoney.com/"}
    px = {"http": "", "https": ""}
    res = {}
    cols = "SECUCODE,SECURITY_NAME_ABBR,REPORTDATE,TOTAL_OPERATE_INCOME,PARENT_NETPROFIT,WEIGHTAVG_ROE,XSMLL,BPS,BASIC_EPS,YSTZ,SJLTZ"
    for i, s in enumerate(STOCKS):
        su = f"{s['code']}.{'SH' if s['secid'].startswith('1') else 'SZ'}"
        url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get?"
               f"reportName=RPT_LICO_FN_CPD&columns={cols}&"
               f"filter=(SECUCODE=%22{su}%22)&pageNumber=1&pageSize=1&"
               f"sortTypes=-1&sortColumns=NOTICE_DATE&source=HSF10&client=WEB")
        try:
            r = requests.get(url, proxies=px, headers=hd, timeout=15)
            d = r.json()
            if d.get("success") and d["result"] and d["result"].get("data"):
                dd = d["result"]["data"][0]
                rd = dd.get("REPORTDATE", "")
                if rd and len(rd) >= 10:
                    rd = rd[:10]
                res[s["code"]] = {"code": s["code"], "name": s["name"],
                    "report_date": rd,
                    "revenue": dd.get("TOTAL_OPERATE_INCOME"),
                    "net_profit": dd.get("PARENT_NETPROFIT"),
                    "roe": dd.get("WEIGHTAVG_ROE"),
                    "gross_margin": dd.get("XSMLL"),
                    "bps": dd.get("BPS"), "eps": dd.get("BASIC_EPS"),
                    "rev_yoy": dd.get("YSTZ"), "profit_yoy": dd.get("SJLTZ")}
            print(f"  [{i+1}/{len(STOCKS)}] {s['name']} OK")
            time.sleep(0.2)
        except Exception as e:
            print(f"  [{i+1}/{len(STOCKS)}] {s['name']} ERR: {e}")
            res[s["code"]] = {"code": s["code"], "name": s["name"],
                "report_date": "", "revenue": None, "net_profit": None,
                "roe": None, "gross_margin": None, "bps": None,
                "eps": None, "rev_yoy": None, "profit_yoy": None}
    return res

def save_csv(data, path, fnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fnames)
        w.writeheader()
        for item in data.values():
            w.writerow(item)
    print(f"  Saved: {os.path.basename(path)} ({len(data)} records)")

def merge_all(md, fd):
    merged = []
    for s in STOCKS:
        c = s["code"]
        m = md.get(c, {})
        f = fd.get(c, {})
        rev = f.get("revenue") or 0
        np = f.get("net_profit") or 0
        merged.append({
            "code": c, "name": s["name"], "layer": s["layer"],
            "price": m.get("price", ""), "pct_chg": m.get("pct_chg", ""),
            "pe_ttm": m.get("pe_ttm", ""), "pb": m.get("pb", ""),
            "total_mv": m.get("total_mv", ""), "float_mv": m.get("float_mv", ""),
            "turnover": m.get("turnover", ""),
            "roe": f.get("roe", ""), "gross_margin": f.get("gross_margin", ""),
            "revenue": rev, "net_profit": np,
            "rev_yoy": f.get("rev_yoy", ""), "profit_yoy": f.get("profit_yoy", ""),
            "eps": f.get("eps", ""), "bps": f.get("bps", ""),
            "report_date": f.get("report_date", ""),
            "power_upstream": "Y" if c in POWER_SET else "N"})
    return merged

def validate(md, fd):
    mm = [s["name"] for s in STOCKS if s["code"] not in md]
    mf = [s["name"] for s in STOCKS if s["code"] not in fd]
    if mm:
        print(f"[WARN] Missing quotes: {', '.join(mm)}")
    if mf:
        print(f"[WARN] Missing fin: {', '.join(mf)}")
    return len(mm) == 0 and len(mf) == 0

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="006 Data Fetcher")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-market", action="store_true")
    ap.add_argument("--skip-financial", action="store_true")
    args = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)
    print("="*50)
    print(f"006 Data Fetcher - {get_today()}")
    print(f"Stocks: {len(STOCKS)}")
    print("="*50)
    if not args.force and has_cache():
        print("\n[INFO] Cache exists, skipping fetch (use --force to refresh)")
        md, fd = read_cache()
        validate(md, fd)
        sys.exit(0)
    md = {}
    if not args.skip_market:
        print("\n[Phase 1/2] Fetching market data...")
        md = fetch_market_data()
        mf = ["code","name","price","pct_chg","change","high","low","open","pre_close",
              "total_mv","float_mv","pb","pe_ttm","turnover","amount"]
        save_csv(md, cache_path("market-data"), mf)
    fd = {}
    if not args.skip_financial:
        print("\n[Phase 2/2] Fetching financial data...")
        fd = fetch_financial_data()
        ff = ["code","name","report_date","revenue","net_profit","roe","gross_margin",
              "bps","eps","rev_yoy","profit_yoy"]
        save_csv(fd, cache_path("financial-data"), ff)
    if md and fd:
        merged = merge_all(md, fd)
        full_f = ["code","name","layer","price","pct_chg","pe_ttm","pb",
                  "total_mv","float_mv","turnover","roe","gross_margin",
                  "revenue","net_profit","rev_yoy","profit_yoy","eps","bps",
                  "report_date","power_upstream"]
        fp = cache_path("data-full")
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=full_f)
            w.writeheader()
            w.writerows(merged)
        print(f"\n  Saved full: {os.path.basename(fp)} ({len(merged)} records)")
        ok = validate(md, fd)
        print(f"\nDone! {'All OK' if ok else 'Partial'}")
    print("="*50)

