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

def get_eastmoney_klines(secid, start_str, end_str):
    """Fetch kline data from eastmoney"""
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=1&secid={secid}&beg={start_str}&end={end_str}"
    try:
        r = requests.get(url, timeout=10, proxies={"http": "", "https": ""})
        data = r.json()
        if data.get("data") and data["data"].get("klines"):
            return data["data"]["klines"]
    except:
        pass
    return None

def parse_kline(line):
    parts = line.split(",")
    return {"date": parts[0].replace("-", ""), "close": float(parts[2]), "pct_chg": float(parts[3])}

def get_stock_daily(code, start, end):
    s = start.replace("-", "")
    e = end.replace("-", "")
    df = pro.daily(ts_code=code, start_date=s, end_date=e, fields="trade_date,close,pct_chg")
    if df is not None and len(df) > 0:
        return df.sort_values("trade_date")
    return None

# All 14 cases
cases = [
    ("上海建科", "603153.SH", "1.603153", "2025-12-16"),
    ("东方创业", "600278.SH", "1.600278", "2021-11-30"),
    ("国泰君安", "601211.SH", "1.601211", "2020-06-08"),
    ("华建集团(2018)", "600629.SH", "1.600629", "2018-12-25"),
    ("华建集团(2022)", "600629.SH", "1.600629", "2022-01-29"),
    ("华谊集团", "600623.SH", "1.600623", "2020-11-25"),
    ("锦江酒店", "600754.SH", "1.600754", "2024-08-10"),
    ("上港集团", "600018.SH", "1.600018", "2021-04-24"),
    ("上海机场", "600009.SH", "1.600009", "2024-05-14"),
    ("外服控股", "600662.SH", "1.600662", "2022-03-17"),
    ("赢合科技(2017)", "300457.SZ", "0.300457", "2017-10-24"),
    ("赢合科技(2022)", "300457.SZ", "0.300457", "2022-11-12"),
    ("申能股份", "600642.SH", "1.600642", "2021-01-26"),
    ("上海电气", "601727.SH", "1.601727", "2019-01-23"),
]

# Pre-fetch ALL index data first (1 big call)
all_dates_list = []
for _, _, _, date in cases:
    d = datetime.strptime(date, "%Y-%m-%d")
    all_dates_list.extend([(d + timedelta(days=i)).strftime("%Y%m%d") for i in range(-5, 125)])

full_start = min(all_dates_list)
full_end = max(all_dates_list)
print(f"Fetching 上证指数 data from {full_start} to {full_end}...")
idx_klines = get_eastmoney_klines("1.000001", full_start, full_end)
idx_data = {}
if idx_klines:
    for line in idx_klines:
        p = parse_kline(line)
        idx_data[p["date"]] = (p["close"], p["pct_chg"])
    print(f"Got {len(idx_data)} index trading days")
else:
    print("Failed to get index data!")
    exit(1)

def find_nth_trading(data_dict, anchor_date, n):
    """Find the nth trading day's data after anchor_date"""
    keys = sorted(data_dict.keys())
    found = False
    count = 0
    for k in keys:
        if not found and k >= anchor_date:
            found = True
        if found:
            if count == n:
                return data_dict[k][0], data_dict[k][1], k
            count += 1
    return None, None, None

def find_nearest(data_dict, target_date):
    """Find nearest date >= target"""
    for k in sorted(data_dict.keys()):
        if k >= target_date:
            return data_dict[k][0], data_dict[k][1], k
    return None, None, None

print(f"\n{'公司':<16} {'公告日':<12} {'公告日涨跌%':>8} {'上证当日%':>8} {'当日相对%':>8} {'10日相对%':>8} {'60日相对%':>9}")
print("-"*78)

results_list = []

for name, ts_code, em_secid, date in cases:
    time.sleep(0.035)  # rate limit
    d = datetime.strptime(date, "%Y-%m-%d")
    start = (d - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (d + timedelta(days=125)).strftime("%Y-%m-%d")
    
    target = date.replace("-", "")
    
    # Get stock data from tushare
    df_s = get_stock_daily(ts_code, start, end)
    
    if df_s is None or len(df_s) == 0:
        print(f"{name:<16} {date:<12} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>9}")
        continue
    
    # Stock announce day
    ann_close_s = None
    ann_chg_s = None
    for _, row in df_s.iterrows():
        if row["trade_date"] >= target:
            ann_close_s = float(row["close"])
            ann_chg_s = float(row["pct_chg"])
            break
    
    # Index announce day
    ann_close_i, ann_chg_i, _ = find_nearest(idx_data, target)
    
    if ann_chg_s is None or ann_chg_i is None:
        print(f"{name:<16} {date:<12} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>9}")
        continue
    
    d0_rel = round(ann_chg_s - ann_chg_i, 2)
    
    # 10th trading day
    cnt = 0
    close10_s = None
    for _, row in df_s.iterrows():
        if row["trade_date"] >= target:
            if cnt == 10:
                close10_s = float(row["close"])
                break
            cnt += 1
    
    # 60th trading day
    cnt = 0
    close60_s = None
    for _, row in df_s.iterrows():
        if row["trade_date"] >= target:
            if cnt == 60:
                close60_s = float(row["close"])
                break
            cnt += 1
    
    close10_i, _, _ = find_nth_trading(idx_data, target, 10)
    close60_i, _, _ = find_nth_trading(idx_data, target, 60)
    
    if close10_s and close10_i:
        ret_s10 = round((close10_s - ann_close_s) / ann_close_s * 100, 2)
        ret_i10 = round((close10_i - ann_close_i) / ann_close_i * 100, 2)
        rel10 = round(ret_s10 - ret_i10, 2)
    else:
        rel10 = None
    
    if close60_s and close60_i:
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
print(f"\nDone!")
