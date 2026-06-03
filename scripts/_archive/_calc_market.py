import os, sys, json, time
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
sys.stdout.reconfigure(encoding="utf-8")
import tushare as ts
pro = ts.pro_api()
from datetime import datetime, timedelta

def get_index_daily(code, start, end):
    """Get index daily data"""
    s = start.replace("-", "")
    e = end.replace("-", "")
    df = pro.index_daily(ts_code=code, start_date=s, end_date=e, fields="trade_date,close,pct_chg")
    if df is not None and len(df) > 0:
        return df.sort_values("trade_date")
    return None

def get_stock_daily(code, start, end):
    """Get stock daily data"""
    s = start.replace("-", "")
    e = end.replace("-", "")
    df = pro.daily(ts_code=code, start_date=s, end_date=e, fields="trade_date,close,pct_chg")
    if df is not None and len(df) > 0:
        return df.sort_values("trade_date")
    return None

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

INDEX = "000001.SH"

# First, collect ALL date ranges needed and batch query
all_dates = []
for name, code, date in cases:
    d = datetime.strptime(date, "%Y-%m-%d")
    start = (d - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (d + timedelta(days=125)).strftime("%Y-%m-%d")  # 60 trading days ≈ 120 calendar days
    all_dates.append((name, code, date, start, end))

# Get index data in one big batch (for all companies)
index_start = min(d[3] for d in all_dates)
index_end = max(d[4] for d in all_dates)
idx_df = get_index_daily(INDEX, index_start, index_end)

def find_price(df, target_date_str, direction="nearest"):
    """Find close and pct_chg for a specific date (or nearest)"""
    target = target_date_str.replace("-", "")
    for _, row in df.iterrows():
        if row["trade_date"] == target:
            return float(row["close"]), float(row["pct_chg"])
    if direction == "after":
        for _, row in df.iterrows():
            if row["trade_date"] >= target:
                return float(row["close"]), float(row["pct_chg"])
    return None, None

def find_nth_trading_day(df, anchor_date_str, n):
    """Find the nth trading day after anchor_date"""
    anchor = anchor_date_str.replace("-", "")
    found_anchor = False
    count = 0
    for _, row in df.iterrows():
        if not found_anchor:
            if row["trade_date"] >= anchor:
                found_anchor = True
        if found_anchor:
            if count == n:
                return float(row["close"]), float(row["pct_chg"]), row["trade_date"]
            count += 1
    return None, None, None

print(f"{'公司':<16} {'公告日':<12} {'公告日涨跌%':>8} {'上证当日%':>8} {'当日相对%':>8} {'10日相对%':>8} {'60日相对%':>9}")
print("-"*78)

results_list = []

for name, code, date, start, end in all_dates:
    time.sleep(0.03)  # Rate limit ~2 calls/second
    df_s = get_stock_daily(code, start, end)
    
    if df_s is None or idx_df is None:
        print(f"{name:<16} {date:<12} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>9}")
        continue
    
    # Find announce day stock price & chg
    ann_close_s, ann_chg_s = find_price(df_s, date)
    ann_close_i, ann_chg_i = find_price(idx_df, date)
    
    if ann_chg_s is None:
        ann_close_s, _ = find_price(df_s, date, "after")
        _, ann_chg_s = find_price(df_s, date, "after")
    if ann_chg_i is None:
        _, ann_chg_i = find_price(idx_df, date, "after")
    
    if ann_chg_s is None or ann_chg_i is None:
        print(f"{name:<16} {date:<12} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>9}")
        continue
    
    d0_rel = round(ann_chg_s - ann_chg_i, 2)
    
    # Get stock price at 10th and 60th trading day
    close10_s, _, date10_s = find_nth_trading_day(df_s, date, 10)
    close60_s, _, date60_s = find_nth_trading_day(df_s, date, 60)
    close10_i, _, _ = find_nth_trading_day(idx_df, date, 10)
    close60_i, _, _ = find_nth_trading_day(idx_df, date, 60)
    
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
