import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
import tushare as ts, sys
sys.stdout.reconfigure(encoding="utf-8")
pro = ts.pro_api()
for d in ['2019-05-07','2019-06-25','2021-12-17','2022-03-15','2026-05-15']:
    date = d.replace("-","")
    df = pro.daily(ts_code="601727.SH", start_date=date, end_date=date, fields="trade_date,close")
    if df is not None and len(df) > 0:
        print(f"{d}: {float(df.iloc[0]['close']):.2f}")
    else:
        print(f"{d}: N/A")
