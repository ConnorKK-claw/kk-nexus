import requests, json, sys, os
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding="utf-8")

def get_price_from_eastmoney(ts_code, date):
    """Get close price from eastmoney API"""
    # Map stock code
    if ts_code.endswith(".SH"):
        secid = f"1.{ts_code.replace('.SH', '')}"
    elif ts_code.endswith(".SZ"):
        secid = f"0.{ts_code.replace('.SZ', '')}"
    else:
        return None
    
    dt = datetime.strptime(date, "%Y-%m-%d")
    start = (dt - timedelta(days=3)).strftime("%Y%m%d")
    end = (dt + timedelta(days=3)).strftime("%Y%m%d")
    
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=1&secid={secid}&beg={start}&end={end}"
    
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("data") and data["data"].get("klines"):
            for line in data["data"]["klines"]:
                parts = line.split(",")
                kdate = parts[0].replace("-", "")
                target = date.replace("-", "")
                if kdate == target:
                    return float(parts[2])
            # nearest date
            for line in data["data"]["klines"]:
                parts = line.split(",")
                kdate = parts[0].replace("-", "")
                target = date.replace("-", "")
                if kdate <= target:
                    return float(parts[2])
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

print("="*60)
print("Fetching stock prices from eastmoney")
print("="*60)

results = {}
for code, date in queries:
    price = get_price_from_eastmoney(code, date)
    if price:
        print(f"  {code} {date}: {price:.2f}")
        results[f"{code}|{date}"] = price
    else:
        print(f"  {code} {date}: N/A")

with open(os.path.join(os.path.dirname(__file__) or ".", "_stock_prices.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(results)} prices")
