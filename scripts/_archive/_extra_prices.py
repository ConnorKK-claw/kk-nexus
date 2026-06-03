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

def get_close(ts_code, date_str):
    date = date_str.replace("-", "")
    df = pro.daily(ts_code=ts_code, start_date=date, end_date=date, fields="trade_date,close")
    if df is not None and len(df) > 0:
        return float(df.iloc[0]["close"])
    from datetime import datetime, timedelta
    d = datetime.strptime(date_str, "%Y-%m-%d")
    for offset in range(1, 8):
        for dr in [d + timedelta(days=offset), d - timedelta(days=offset)]:
            ds = dr.strftime("%Y%m%d")
            df2 = pro.daily(ts_code=ts_code, start_date=ds, end_date=ds, fields="trade_date,close")
            if df2 is not None and len(df2) > 0:
                return float(df2.iloc[0]["close"])
    return None

# Additional queries needed
queries = [
    ("300457.SZ", "2020-12-28"),  # 赢合2017第3批预计
    ("600629.SH", "2024-03-04"),  # 华建2022第1批上市日
    ("600018.SH", "2025-11-13"),  # 上港第2批上市日(看实际公告)
]

for code, date in queries:
    price = get_close(code, date)
    if price:
        print(f"{code} {date}: {price:.2f}")
    else:
        print(f"{code} {date}: N/A")
