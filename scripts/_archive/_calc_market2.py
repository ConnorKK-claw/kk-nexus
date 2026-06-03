import os, sys, json, time, requests
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
sys.stdout.reconfigure(encoding="utf-8")

import tushare as ts
pro = ts.pro_api()
from datetime import datetime, timedelta

def get_stock_daily(code, start, end):
    s = start.replace("-", "")
    e = end.replace("-", "")
    df = pro.daily(ts_code=code, start_date=s, end_date=e, fields="trade_date,close,pct_chg")
    if df is not None and len(df) > 0:
        return df.sort_values("trade_date")
    return None

def get_index_by_sina(date_str):
    """Fetch 上证指数 data from sina finance API"""
    import urllib.request
    d = datetime.strptime(date_str, "%Y-%m-%d")
    # sina provides historical data
    url = f"http://quotes.money.163.com/service/chddata.html?code=0000001&start={d.strftime("%Y%m%d")}&end={d.strftime("%Y%m%d")}&fields=TCLOSE;PCHG"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode("gbk")
        lines = data.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split(",")
            close = float(parts[2])
            pct_chg = float(parts[3])
            return close, pct_chg
    except Exception as e:
        pass
    return None, None

# Alternative: fetch from public API
def get_index_daily_range(start_date, end_date):
    """Batch fetch 上证指数 data"""
    import urllib.request
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    url = f"http://quotes.money.163.com/service/chddata.html?code=0000001&start={s.strftime("%Y%m%d")}&end={e.strftime("%Y%m%d")}&fields=TCLOSE;PCHG"
    results = {}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read().decode("gbk")
        lines = data.strip().split("\n")
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 4:
                date_str = parts[0].replace("-", "")
                close = float(parts[2])
                pct_chg = float(parts[3])
                results[date_str] = (close, pct_chg)
    except:
        pass
    return results

# All cases
cases = [
    ("上海建科", "603153.SH", "2025-12-16"),
    ("东方创业", "600278.SH", "2021-11-30"),
    ("国泰君安", "601211.SH", "2020-06-08"),
    ("华建集团(2018)", "600629.SH", "2018-12-25"),
    ("华建集团(2022)", "600629.SH", "2022-01-29"),
    ("华谊集团", "600623.SH", "2020-11-25"),
    ("锦江酒店", "600754.SH", "2024-08-10"),
    ("上港集团", "600018.SH", "2021-04-24"),
    ("上海机场", "600009.SH", "2024-05-14"),
    ("外服控股", "600662.SH", "2022-03-17"),
    ("赢合科技(2017)", "300457.SZ", "2017-10-24"),
    ("赢合科技(2022)", "300457.SZ", "2022-11-12"),
    ("申能股份", "600642.SH", "2021-01-26"),
    ("上海电气", "601727.SH", "2019-01-23"),
]

# Pre-fetch all index data in one batch
all_dates_dt = set()
for _, _, date in cases:
    d = datetime.strptime(date, "%Y-%m-%d")
    for i in range(-5, 125):
        all_dates_dt.add((d + timedelta(days=i)).strftime("%Y-%m-%d"))

full_start = min(all_dates_dt)
full_end = max(all_dates_dt)
print(f"Fetching 上证指数 data from {full_start} to {full_end}...")
idx_data = get_index_daily_range(full_start, full_end)
print(f"Got {len(idx_data)} trading days of index data")

def find_nth_day_idx(target_date_str, n, data_dict):
    """Find nth trading day's data in index dict"""
    target = target_date_str.replace("-", "")
    keys = sorted(data_dict.keys())
    found = False
    count = 0
    for k in keys:
        if not found:
            if k >= target:
                found = True
        if found:
            if count == n:
                return data_dict[k][0], data_dict[k][1]
            count += 1
    return None, None

def find_nearest_idx(target_date_str, data_dict):
    target = target_date_str.replace("-", "")
    keys = sorted(data_dict.keys())
    for k in keys:
        if k >= target:
            return data_dict[k][0], data_dict[k][1]
    return None, None

print(f"\n{'公司':<16} {'公告日':<12} {'公告日涨跌%':>8} {'上证当日%':>8} {'当日相对%':>8} {'10日相对%':>8} {'60日相对%':>9}")
print("-"*78)

results_list = []

for name, code, date in cases:
    time.sleep(0.04)
    d = datetime.strptime(date, "%Y-%m-%d")
    start = (d - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (d + timedelta(days=125)).strftime("%Y-%m-%d")
    
    df_s = get_stock_daily(code, start, end)
    
    if df_s is None or len(df_s) == 0:
        print(f"{name:<16} {date:<12} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>9}")
        continue
    
    target = date.replace("-", "")
    
    # Stock announce day
    ann_close_s = None
    ann_chg_s = None
    for _, row in df_s.iterrows():
        if row["trade_date"] >= target:
            ann_close_s = float(row["close"])
            ann_chg_s = float(row["pct_chg"])
            break
    
    # Index announce day
    ann_close_i, ann_chg_i = find_nearest_idx(date, idx_data)
    
    if ann_chg_s is None or ann_chg_i is None:
        print(f"{name:<16} {date:<12} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>9}")
        continue
    
    d0_rel = round(ann_chg_s - ann_chg_i, 2)
    
    # 10th and 60th trading day
    close10_s, _, date10_s = None, None, None
    cnt = 0
    for _, row in df_s.iterrows():
        if row["trade_date"] >= target:
            if cnt == 10:
                close10_s = float(row["close"])
                date10_s = row["trade_date"]
                break
            cnt += 1
    
    cnt = 0
    close60_s, date60_s = None, None
    for _, row in df_s.iterrows():
        if row["trade_date"] >= target:
            if cnt == 60:
                close60_s = float(row["close"])
                date60_s = row["trade_date"]
                break
            cnt += 1
    
    close10_i, _ = find_nth_day_idx(date, 10, idx_data)
    close60_i, _ = find_nth_day_idx(date, 60, idx_data)
    
    if close10_s and close10_i and ann_close_s and ann_close_i:
        ret_s10 = round((close10_s - ann_close_s) / ann_close_s * 100, 2)
        ret_i10 = round((close10_i - ann_close_i) / ann_close_i * 100, 2)
        rel10 = round(ret_s10 - ret_i10, 2)
    else:
        rel10 = None
    
    if close60_s and close60_i and ann_close_s and ann_close_i:
        ret_s60 = round((close60_s - ann_close_s) / ann_close_s * 100, 2)
        ret_i60 = round((close60_i - ann_close_i) / ann_close_i * 100, 2)
        rel60 = round(ret_s60 - ret_i60, 2)
    else:
        rel60 = None
    
    d0_str = f"{d0_rel:+.2f}"
    r10_str = f"{rel10:+.2f}" if rel10 is not None else "N/A"
    r60_str = f"{rel60:+.2f}" if rel60 is not None else "N/A"
    
    print(f"{name:<16} {date:<12} {ann_chg_s:>+8.2f} {ann_chg_i:>+8.2f} {d0_str:>8} {r10_str:>8} {r60_str:>9}")
    results_list.append({"name": name, "date": date, "stock_chg": f"{ann_chg_s:.2f}", "index_chg": f"{ann_chg_i:.2f}", "d0_rel": d0_str, "rel10": r10_str, "rel60": r60_str})

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6\scripts"
with open(os.path.join(wrk, "_market_reaction.json"), "w", encoding="utf-8") as f:
    json.dump(results_list, f, ensure_ascii=False, indent=2)
print(f"\nDone. Results in _market_reaction.json")
