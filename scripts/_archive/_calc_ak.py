import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"

import sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
import tushare as ts
import akshare as ak
pro = ts.pro_api()
from datetime import datetime, timedelta
import pandas as pd

# Get 上证指数 via akshare
print("Fetching 上证指数 from akshare...")
try:
    idx = ak.stock_zh_index_daily(symbol="sh000001")
    if idx is not None and len(idx) > 0:
        idx_data = {}
        for _, row in idx.iterrows():
            d = pd.Timestamp(row["date"]).strftime("%Y%m%d")
            close = float(row["close"])
            idx_data[d] = close
        # Calculate pct changes
        sorted_dates = sorted(idx_data.keys())
        idx_pct = {}
        for i, d in enumerate(sorted_dates):
            if i == 0:
                idx_pct[d] = (idx_data[d], 0.0)
            else:
                prev = idx_data[sorted_dates[i-1]]
                pct = round((idx_data[d] - prev) / prev * 100, 2)
                idx_pct[d] = (idx_data[d], pct)
        idx_data = idx_pct
        print(f"Got {len(idx_data)} index days (from {sorted_dates[0]} to {sorted_dates[-1]})")
    else:
        print("No index data from akshare")
        exit(1)
except Exception as e:
    print(f"akshare error: {e}")
    exit(1)

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

def find_nth(data_dict, anchor, n):
    keys = sorted(data_dict.keys())
    found = False
    count = 0
    for k in keys:
        if not found and k >= anchor:
            found = True
        if found:
            if count == n:
                return data_dict[k]
            count += 1
    return None

def find_nearest(data_dict, target):
    for k in sorted(data_dict.keys()):
        if k >= target:
            return data_dict[k]
    return None

print(f"\n{'公司':<16} {'公告日':<12} {'公告日涨跌%':>8} {'上证当日%':>8} {'当日相对%':>8} {'10日相对%':>8} {'60日相对%':>9}")
print("-"*78)

results_list = []

for name, code, date in cases:
    time.sleep(0.04)
    d = datetime.strptime(date, "%Y-%m-%d")
    target = date.replace("-", "")
    start_s = (d - timedelta(days=5)).strftime("%Y%m%d")
    end_s = (d + timedelta(days=125)).strftime("%Y%m%d")
    
    try:
        df_s = pro.daily(ts_code=code, start_date=start_s, end_date=end_s, fields="trade_date,close,pct_chg")
        if df_s is None or len(df_s) == 0:
            print(f"{name:<16} {date:<12} {'NODATA':>8}")
            continue
        df_s = df_s.sort_values("trade_date")
        
        ann_close_s = None
        ann_chg_s = None
        for _, row in df_s.iterrows():
            if row["trade_date"] >= target:
                ann_close_s = float(row["close"])
                ann_chg_s = float(row["pct_chg"])
                break
        
        idx_info = find_nearest(idx_data, target)
        if idx_info:
            ann_close_i, ann_chg_i = idx_info
        else:
            print(f"{name:<16} {date:<12} {'NOIDX':>8}")
            continue
        
        d0_rel = round(ann_chg_s - ann_chg_i, 2)
        
        cnt = 0
        close10_s = None
        for _, row in df_s.iterrows():
            if row["trade_date"] >= target:
                if cnt == 10:
                    close10_s = float(row["close"])
                    break
                cnt += 1
        
        cnt = 0
        close60_s = None
        for _, row in df_s.iterrows():
            if row["trade_date"] >= target:
                if cnt == 60:
                    close60_s = float(row["close"])
                    break
                cnt += 1
        
        idx10 = find_nth(idx_data, target, 10)
        idx60 = find_nth(idx_data, target, 60)
        
        rel10 = None
        if close10_s and idx10:
            r_s = round((close10_s - ann_close_s) / ann_close_s * 100, 2)
            r_i = round((idx10[0] - ann_close_i) / ann_close_i * 100, 2)
            rel10 = round(r_s - r_i, 2)
        
        rel60 = None
        if close60_s and idx60:
            r_s = round((close60_s - ann_close_s) / ann_close_s * 100, 2)
            r_i = round((idx60[0] - ann_close_i) / ann_close_i * 100, 2)
            rel60 = round(r_s - r_i, 2)
        
        d0_str = f"{d0_rel:+.2f}"
        r10_str = f"{rel10:+.2f}" if rel10 is not None else "N/A"
        r60_str = f"{rel60:+.2f}" if rel60 is not None else "N/A"
        
        print(f"{name:<16} {date:<12} {ann_chg_s:>+8.2f} {ann_chg_i:>+8.2f} {d0_str:>8} {r10_str:>8} {r60_str:>9}")
        results_list.append({"name": name, "date": date, "stock_chg": f"{ann_chg_s:.2f}", "index_chg": f"{ann_chg_i:.2f}", "d0_rel": d0_str, "rel10": r10_str, "rel60": r60_str})
    except Exception as e:
        print(f"{name:<16} {date:<12} Error: {str(e)[:40]}")

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6\scripts"
with open(os.path.join(wrk, "_market_reaction.json"), "w", encoding="utf-8") as f:
    json.dump(results_list, f, ensure_ascii=False, indent=2)
print(f"\nDone! {len(results_list)} results")
