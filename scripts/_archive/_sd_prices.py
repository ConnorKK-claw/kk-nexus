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

queries = [
    ("601727.SH", "2019-01-23"),   # 草案公告日
    ("601727.SH", "2019-05-07"),   # 授予日
    ("601727.SH", "2019-06-25"),   # 登记日
    ("601727.SH", "2021-06-25"),   # 第1批预计解锁日
    ("601727.SH", "2021-12-17"),   # 终止公告前日
    ("601727.SH", "2021-12-18"),   # 终止公告日
    ("601727.SH", "2022-03-15"),   # 最终回购注销日
    ("601727.SH", "2026-05-15"),   # 最新收盘
]

for code, date in queries:
    price = get_close(code, date)
    if price:
        print(f"{code} {date}: {price:.2f}")
    else:
        print(f"{code} {date}: N/A")
