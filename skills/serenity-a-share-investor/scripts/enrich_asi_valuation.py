#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
006\u5458\u5de5 - \u4f30\u503c\u6df1\u5ea6\u5206\u6790\u811a\u672c
\u529f\u80fd\uff1a\u83b7\u53d6\u591a\u5b63\u5ea6EPS + \u5386\u53f2\u4ef7\u683c\uff0c\u8ba1\u7b97\u4f30\u503c\u6307\u6807\n"""
import os, sys, csv, json, datetime, time, math
sys.stdout.reconfigure(encoding="utf-8")

VAULT = os.path.expanduser("~/.codex/skills/serenity-a-share-investor")
RAW = os.path.join(VAULT, "vault", "raw", "agent")

from asi_stocks import STOCKS

def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")

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

def read_latest_full():
    """\u8bfb\u53d6\u6700\u65b0\u7684 data-full CSV"""
    fs = sorted([f for f in os.listdir(RAW) if f.endswith("-asi-data-full.csv")], reverse=True)
    if not fs:
        print("[ERROR] No data-full CSV found. Run fetch_asi_market_data.py first.")
        return None
    with open(os.path.join(RAW, fs[0]), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {fs[0]} ({len(rows)} rows)")
    return rows

def fetch_quarterly_eps(stock):
    """\u83b7\u53d612\u5b63\u5ea6EPS\u5e8f\u5217"""
    import requests
    hd = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}
    px = {"http": "", "https": ""}
    su = f"{stock['code']}.SH" if stock["secid"].startswith("1") else f"{stock['code']}.SZ"
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get?"
           f"reportName=RPT_LICO_FN_CPD&columns=SECUCODE,SECURITY_NAME_ABBR,"
           f"REPORTDATE,TOTAL_OPERATE_INCOME,PARENT_NETPROFIT,WEIGHTAVG_ROE,XSMLL,BPS,BASIC_EPS,YSTZ,SJLTZ&"
           f"filter=(SECUCODE=%22{su}%22)&pageNumber=1&pageSize=12&"
           f"sortTypes=-1&sortColumns=NOTICE_DATE&source=HSF10&client=WEB")
    try:
        r = requests.get(url, headers=hd, proxies=px, timeout=15)
        if r.status_code == 200:
            d = r.json()
            if d.get("result") and d["result"].get("data"):
                return d["result"]["data"]
    except:
        pass
    return []

def fetch_kline(code):
    """\u83b7\u53d6720\u5929\u65e5\u7ebf\u6570\u636e"""
    import requests
    prefix = "sh" if code.startswith("6") else "sz"
    url = f"http://ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix}{code},day,,,720,qfq"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200:
            d = r.json()
            key = f"{prefix}{code}"
            if "data" in d and key in d["data"]:
                k = d["data"][key]
                if "qfqday" in k:
                    return k["qfqday"]
    except:
        pass
    return []

def compute_eps_ttm(quarterly_data):
    """\u4ece12\u5b63\u5ea6\u6570\u636e\u8ba1\u7b97EPS_TTM\u5e8f\u5217"""
    # \u6309REPORTDATE\u6392\u5e8f(\u4ece\u65e9\u5230\u665a)
    sorted_q = sorted(quarterly_data, key=lambda x: x.get("REPORTDATE", ""))
    eps_seq = []
    for i, q in enumerate(sorted_q):
        eps = sf(q.get("BASIC_EPS"))
        date = q.get("REPORTDATE", "")[:10]
        eps_seq.append((date, eps))
    return eps_seq

def compute_historical_pe(kline_data, eps_sequence):
    """\u8ba1\u7b97720\u5929\u6bcf\u65e5\u5386\u53f2PE"""
    import datetime as dt
    # \u6784\u5efaEPS_TTM\u65f6\u95f4\u7ebf\uff08\u6bcf\u4e2a\u5b63\u5ea6\u62a5\u544a\u65e5\u4e4b\u540e\u4f7f\u7528\u5f53\u524d\u7684EPS_TTM\uff09
    eps_map = {}
    for date_str, eps in eps_sequence:
        try:
            d = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            eps_map[d] = eps
        except:
            pass

    # \u8ba1\u7b97\u6bcf\u4e2a\u62a5\u544a\u65e5\u7684EPS_TTM\uff08\u6700\u8fd14\u4e2a\u5b63\u5ea6\u52a0\u548c\uff09
    sorted_dates = sorted(eps_map.keys())
    ttm_map = {}
    for i, d in enumerate(sorted_dates):
        if i >= 3:
            ttm = sum(eps_map[sorted_dates[j]] for j in range(i-3, i+1))
        else:
            # \u4e0d\u8db34\u4e2a\u5b63\u5ea6\uff0c\u7528\u5df2\u6709\u6570\u636e\u52a0\u6743\u4f30\u7b97
            count = min(i + 1, 4)
            ttm = sum(eps_map[sorted_dates[j]] for j in range(max(0, i-3), i+1)) * (4.0 / count)
        ttm_map[d] = ttm

    # \u5bf9\u6bcf\u4e2a\u4ea4\u6613\u65e5\uff0c\u67e5\u627e\u6700\u65b0\u7684EPS_TTM
    daily_pe = []
    for bar in kline_data:
        try:
            date_str = bar[0]
            close = float(bar[2])
            d = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            # \u627e\u5230\u5c0f\u4e8e\u7b49\u4e8e\u5f53\u524d\u65e5\u671f\u7684\u6700\u65b0EPS_TTM
            latest_ttm = None
            for rd in sorted(ttm_map.keys()):
                if rd <= d:
                    latest_ttm = ttm_map[rd]
                else:
                    break
            if latest_ttm and latest_ttm > 0:
                pe = close / latest_ttm
                daily_pe.append((date_str, close, latest_ttm, round(pe, 2)))
        except:
            pass
    return daily_pe

def compute_percentiles(values):
    """\u8ba1\u7b97\u767e\u5206\u4f4d"""
    vs = sorted(values)
    n = len(vs)
    if n == 0:
        return (0, 0, 0, 0, 0)
    def pct(p):
        k = (n - 1) * p / 100
        f = int(k)
        c = f + 1
        if c >= n:
            return vs[-1]
        return vs[f] * (c - k) + vs[c] * (k - f)
    return (pct(5), pct(25), pct(50), pct(75), pct(95))

def analyze_stock(stock):
    """\u5355\u53ea\u5206\u6790\uff1a\u5386\u53f2PE\u5206\u4f4d"""
    code = stock["code"]
    result = {"code": code, "name": stock["name"], "layer": stock["layer"]}

    # \u83b7\u53d6\u5b63\u5ea6EPS
    qdata = fetch_quarterly_eps(stock)
    if len(qdata) < 2:
        print(f"  [{code}] Only {len(qdata)} quarters of EPS data")
        return result

    eps_seq = compute_eps_ttm(qdata)
    if not eps_seq:
        return result

    # \u83b7\u53d6\u5386\u53f2\u65e5\u7ebf
    kline = fetch_kline(code)
    if len(kline) < 20:
        print(f"  [{code}] Only {len(kline)} trading days")
        return result

    # \u8ba1\u7b97\u5386\u53f2PE
    daily_pe = compute_historical_pe(kline, eps_seq)
    if len(daily_pe) < 20:
        print(f"  [{code}] Only {len(daily_pe)} PE data points")
        return result

    pe_values = [p[3] for p in daily_pe if p[3] > 0 and p[3] < 500]
    if len(pe_values) < 20:
        return result

    p5, p25, p50, p75, p95 = compute_percentiles(pe_values)
    current_pe = pe_values[-1] if pe_values else 0

    # \u5f53\u524dPE\u5728\u5386\u53f2\u4e2d\u7684\u767e\u5206\u4f4d
    pct_rank = sum(1 for v in pe_values if v < current_pe) / len(pe_values) * 100 if pe_values else 0

    result.update({
        "pe_hist_count": len(pe_values),
        "pe_hist_p5": round(p5, 2),
        "pe_hist_p25": round(p25, 2),
        "pe_hist_p50": round(p50, 2),
        "pe_hist_p75": round(p75, 2),
        "pe_hist_p95": round(p95, 2),
        "pe_current": round(current_pe, 2),
        "pe_percentile": round(pct_rank, 1),
        "eps_ttm_latest": round(daily_pe[-1][2], 4),
        "price_latest": daily_pe[-1][1],
    })
    print(f"  [{code}] {stock['name']}: PE_percentile={pct_rank:.1f}% p50={p50:.1f}")
    return result

def main():
    import argparse
    ap = argparse.ArgumentParser(description="006 Valuation Analysis")
    ap.add_argument("--force", action="store_true", help="Force re-fetch even if cache exists")
    ap.add_argument("--skip-kline", action="store_true")
    ap.add_argument("--skip-financial", action="store_true")
    args = ap.parse_args()

    os.makedirs(RAW, exist_ok=True)
    print("="*50)
    print(f"006 Valuation Analysis - {get_today()}")
    print(f"Stocks: {len(STOCKS)}")
    print("="*50)

    vpath = cache_path("valuation")
    if not args.force and os.path.exists(vpath):
        print(f"\n[INFO] Cache exists: {os.path.basename(vpath)}")
        # \u68c0\u67e5\u662f\u5426\u5df2\u6709\u5168\u91cf\u5b57\u6bb5
        with open(vpath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
        if "pe_percentile" in fields and "pe_hist_p50" in fields:
            print("  All valuation fields present. Use --force to refresh.")
            return
        print("  Partial cache, re-fetching...")

    results = []
    for i, s in enumerate(STOCKS):
        print(f"\n[{i+1}/{len(STOCKS)}] {s['name']} ({s['code']})...")
        r = analyze_stock(s)
        results.append(r)
        time.sleep(0.3)  # rate limit

    # \u6dfb\u52a0\u5c42\u5185\u5bf9\u6bd4
    layers = {}
    for r in results:
        l = r.get("layer", "O")
        pe = sf(r.get("pe_current"))
        if 0 < pe < 500:
            layers.setdefault(l, []).append(pe)

    for r in results:
        l = r.get("layer", "O")
        layer_pe = layers.get(l, [])
        if len(layer_pe) >= 2:
            r["layer_pe_median"] = round(sorted(layer_pe)[len(layer_pe)//2], 2)
            avg = sum(layer_pe) / len(layer_pe)
            std = (sum((p-avg)**2 for p in layer_pe) / len(layer_pe))**0.5
            pe = sf(r.get("pe_current"))
            r["layer_pe_zscore"] = round((pe - avg) / std, 2) if std > 0 else 0
        else:
            r["layer_pe_median"] = 0
            r["layer_pe_zscore"] = 0

    # \u4fdd\u5b58
    fields = ["code","name","layer","pe_hist_count","pe_hist_p5","pe_hist_p25",
              "pe_hist_p50","pe_hist_p75","pe_hist_p95","pe_current","pe_percentile",
              "layer_pe_median","layer_pe_zscore","eps_ttm_latest","price_latest"]
    with open(vpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\nSaved: {os.path.basename(vpath)} ({len(results)} records)")

    # \u4e5f\u4fdd\u5b58EPS\u65f6\u95f4\u5e8f\u5217\u548c\u5386\u53f2PE
    # eps sequence is already saved per-stock in the valuation output
    print(f"\nDone!")
    print("="*50)

if __name__ == "__main__":
    main()

