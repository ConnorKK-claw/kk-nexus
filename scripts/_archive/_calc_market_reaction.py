import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
import sys
sys.stdout.reconfigure(encoding="utf-8")
import tushare as ts
pro = ts.pro_api()
from datetime import datetime, timedelta
import json

def get_daily(ts_code, start_date, end_date):
    """Get daily data for a date range"""
    s = start_date.replace("-", "")
    e = end_date.replace("-", "")
    df = pro.daily(ts_code=ts_code, start_date=s, end_date=e, fields="trade_date,close,pct_chg")
    if df is not None and len(df) > 0:
        df = df.sort_values("trade_date")
        return df
    return None

def calc_relative_return(stock_code, index_code, announce_date, days_after):
    """Calculate stock return minus index return over period"""
    d = datetime.strptime(announce_date, "%Y-%m-%d")
    start = (d - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (d + timedelta(days=days_after*2)).strftime("%Y-%m-%d")
    
    df_s = get_daily(stock_code, start, end)
    df_i = get_daily(index_code, start, end)
    
    if df_s is None or df_i is None or len(df_s) == 0 or len(df_i) == 0:
        return None, None, None
    
    # Find announce date in the data
    target = announce_date.replace("-", "")
    ann_idx_s = None
    ann_idx_i = None
    
    for i, row in df_s.iterrows():
        if row["trade_date"] >= target:
            ann_idx_s = i
            break
    for i, row in df_i.iterrows():
        if row["trade_date"] >= target:
            ann_idx_i = i
            break
    
    if ann_idx_s is None or ann_idx_i is None:
        return None, None, None
    
    # Get announce day close
    ann_close_s = float(df_s.loc[ann_idx_s, "close"])
    ann_close_i = float(df_i.loc[ann_idx_i, "close"])
    ann_chg_s = float(df_s.loc[ann_idx_s, "pct_chg"])
    ann_chg_i = float(df_i.loc[ann_idx_i, "pct_chg"])
    
    # Day 0 relative return (公告当日涨跌幅差)
    d0_rel = round(ann_chg_s - ann_chg_i, 2)
    
    # Find idx for days_after
    idx_s = ann_idx_s
    idx_i = ann_idx_i
    count_s = 0
    count_i = 0
    
    for j in range(len(df_s)):
        if j > df_s.index.get_loc(ann_idx_s):
            count_s += 1
            if count_s == days_after:
                idx_s = df_s.index[j]
                break
    
    for j in range(len(df_i)):
        if j > df_i.index.get_loc(ann_idx_i):
            count_i += 1
            if count_i == days_after:
                idx_i = df_i.index[j]
                break
    
    # Calculate returns
    close_after_s = float(df_s.loc[idx_s, "close"]) if idx_s != ann_idx_s else ann_close_s
    close_after_i = float(df_i.loc[idx_i, "close"]) if idx_i != ann_idx_i else ann_close_i
    
    ret_s = round((close_after_s - ann_close_s) / ann_close_s * 100, 2)
    ret_i = round((close_after_i - ann_close_i) / ann_close_i * 100, 2)
    rel_ret = round(ret_s - ret_i, 2)
    
    return d0_rel, rel_ret, (ret_s, ret_i)

# All cases with stock codes and announce dates
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

index_code = "000001.SH"  # 上证指数

print(f"{'公司':<16} {'公告日':<12} {'当日涨跌幅%':>10} {'上证当日%':>10} {'当日相对%':>10} {'10日相对%':>10} {'60日相对%':>10}")
print("-"*78)

results = []
for name, code, date in cases:
    d0_rel, rel10, detail10 = calc_relative_return(code, index_code, date, 10)
    _, rel60, detail60 = calc_relative_return(code, index_code, date, 60)
    
    # Also get the stock's own 当日涨跌幅
    d = datetime.strptime(date, "%Y-%m-%d")
    start = (d - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (d + timedelta(days=5)).strftime("%Y-%m-%d")
    df_s = get_daily(code, start, end)
    df_i = get_daily(index_code, start, end)
    
    ann_chg_s = "N/A"
    ann_chg_i = "N/A"
    
    if df_s is not None and len(df_s) > 0:
        target = date.replace("-", "")
        for _, row in df_s.iterrows():
            if row["trade_date"] >= target:
                ann_chg_s = f"{float(row['pct_chg']):.2f}"
                break
    if df_i is not None and len(df_i) > 0:
        target = date.replace("-", "")
        for _, row in df_i.iterrows():
            if row["trade_date"] >= target:
                ann_chg_i = f"{float(row['pct_chg']):.2f}"
                break
    
    d0_str = f"{d0_rel:+.2f}" if d0_rel is not None else "N/A"
    r10_str = f"{rel10:+.2f}" if rel10 is not None else "N/A"
    r60_str = f"{rel60:+.2f}" if rel60 is not None else "N/A"
    
    print(f"{name:<16} {date:<12} {ann_chg_s:>10} {ann_chg_i:>10} {d0_str:>10} {r10_str:>10} {r60_str:>10}")
    results.append({"name": name, "date": date, "d0_stock": ann_chg_s, "d0_index": ann_chg_i, "d0_rel": d0_str, "rel10": r10_str, "rel60": r60_str})

# Save
wrk = r"C:\Users\hexk\OneDrive\文档\New project 6\scripts"
with open(os.path.join(wrk, "_market_reaction.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved to _market_reaction.json")
