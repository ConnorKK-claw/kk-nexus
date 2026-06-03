import os, sys, json
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"

sys.stdout.reconfigure(encoding="utf-8")

import tushare as ts
pro = ts.pro_api()

def get_close(ts_code, date_str):
    date = date_str.replace("-", "")
    try:
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
    except Exception as e:
        print(f"  Error: {e}")
        return None

queries = [
    ("601211.SH", "2022-09-19"), ("601211.SH", "2023-09-18"),
    ("600629.SH", "2021-03-29"), ("600629.SH", "2022-03-29"), ("600629.SH", "2023-03-29"),
    ("600629.SH", "2024-03-04"), ("600629.SH", "2025-03-03"),
    ("600623.SH", "2024-09-11"), ("600623.SH", "2024-10-30"),
    ("600623.SH", "2025-03-11"), ("600623.SH", "2025-04-15"),
    ("600623.SH", "2026-03-11"), ("600623.SH", "2026-03-27"),
    ("300457.SZ", "2018-12-11"), ("300457.SZ", "2018-12-27"),
    ("300457.SZ", "2019-12-23"), ("300457.SZ", "2020-01-02"),
    ("300457.SZ", "2025-03-27"), ("300457.SZ", "2025-04-09"),
    ("300457.SZ", "2026-03-26"), ("300457.SZ", "2026-04-15"),
    ("600278.SH", "2024-04-27"), ("600278.SH", "2024-05-16"),
    ("600278.SH", "2025-03-01"), ("600278.SH", "2025-03-11"),
    ("600018.SH", "2024-08-27"), ("600018.SH", "2024-09-05"),
    ("600018.SH", "2025-10-31"), ("600018.SH", "2025-11-06"),
    ("600662.SH", "2024-12-06"), ("600662.SH", "2025-04-22"),
    ("600662.SH", "2025-11-04"), ("600662.SH", "2026-04-24"),
    ("600642.SH", "2024-08-29"), ("600642.SH", "2024-09-20"),
    ("600642.SH", "2025-08-28"), ("600642.SH", "2025-09-18"),
    ("603153.SH", "2026-05-15"), ("600009.SH", "2026-05-15"),
    ("600754.SH", "2026-05-15"), ("600662.SH", "2026-05-15"),
    ("600278.SH", "2026-05-15"), ("600629.SH", "2026-05-15"),
    ("600018.SH", "2026-05-15"), ("300457.SZ", "2026-05-15"),
    ("600623.SH", "2026-05-15"), ("601211.SH", "2026-05-15"),
    ("600642.SH", "2026-05-15"),
]

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6\scripts"
results = {}
for code, date in queries:
    price = get_close(code, date)
    if price:
        results[f"{code}|{date}"] = round(price, 2)
        print(f"  {code} {date}: {price:.2f}")
    else:
        print(f"  {code} {date}: N/A")

with open(os.path.join(wrk, "_stock_prices.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(results)} prices")
