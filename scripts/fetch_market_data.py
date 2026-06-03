#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补全对比报告表4的市场反应数据
用法：网络可用时运行 python scripts/fetch_market_data.py
"""
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6"
report_path = os.path.join(wrk, "zk-ei-bb0-0-11-cases-comparison-report.md")

# 各公司草案公告日（用于查询前后股价）
companies = [
    ("上海建科", "603153.SH", "2025-12-16"),
    ("东方创业", "600278.SH", "2021-11-30"),
    ("国泰君安", "601211.SH", "2020-07-01"),  # 约2020年7月
    ("华建集团", "600629.SH", "2018-12-01"),  # 约2018年
    ("华建集团", "600629.SH", "2022-01-01"),  # 约2022年初
    ("华谊集团", "600623.SH", "2020-11-01"),  # 草案2020年
    ("锦江酒店", "600754.SH", "2024-08-10"),
    ("上港集团", "600018.SH", "2021-04-24"),
    ("上海机场", "600009.SH", "2024-05-14"),  #已有数据
    ("外服控股", "600662.SH", "2022-03-01"),  # 约2022年初
    ("赢合科技", "300457.SZ", "2017-10-01"),  # 约2017年
    ("赢合科技", "300457.SZ", "2022-10-01"),  # 约2022年
    ("申能股份", "600642.SH", "2021-01-26"),
]

def fetch_stock_data(ts_code, announce_date):
    """获取公告日前后各5个交易日收盘价"""
    import tushare as ts
    pro = ts.pro_api()
    
    from datetime import datetime, timedelta
    d = datetime.strptime(announce_date, "%Y-%m-%d")
    start = (d - timedelta(days=10)).strftime("%Y%m%d")
    end = (d + timedelta(days=10)).strftime("%Y%m%d")
    
    try:
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end,
                       fields="trade_date,close,pct_chg")
        if df is not None and len(df) > 0:
            df = df.sort_values("trade_date")
            return df
    except Exception as e:
        print(f"  Error: {e}")
    return None

def calc_market_reaction(df, announce_date):
    """计算公告日和公告后1周涨跌幅"""
    if df is None or len(df) < 3:
        return None, None, None, None
    
    dates = list(df["trade_date"])
    closes = list(df["close"])
    
    # 找公告日当天或最近的交易日
    target = announce_date.replace("-", "")
    before_idx = None
    announce_idx = None
    after_idx = None
    
    for i, d in enumerate(dates):
        if d <= target:
            announce_idx = i
            before_idx = i - 1 if i > 0 else None
    
    # 找公告日后第5个交易日
    if announce_idx is not None:
        after_idx = min(announce_idx + 5, len(dates) - 1)
    
    if announce_idx is None or before_idx is None:
        return None, None, None, None
    
    announce_close = closes[announce_idx]
    before_close = closes[before_idx]
    after_close = closes[after_idx]
    
    announce_chg = round((announce_close - before_close) / before_close * 100, 2)
    one_week_chg = round((after_close - announce_close) / announce_close * 100, 2)
    
    return before_close, announce_chg, one_week_chg, after_close

if __name__ == "__main__":
    print("Fetching market data...")
    print()
    
    import tushare as ts
    
    results = []
    for name, code, date in companies:
        print(f"{name} ({code}): ", end="", flush=True)
        df = fetch_stock_data(code, date)
        before, chg, wk_chg, after = calc_market_reaction(df, date)
        
        if before:
            print(f"OK - 公告日前={before:.2f}, 公告日涨幅={chg:.2f}%, 1周涨幅={wk_chg:.2f}%")
            results.append((name, code, date, before, chg, wk_chg))
        else:
            print("SKIP - 数据不足")
    
    print()
    print("=== CSV格式（可复制到报告） ===")
    print("公司,公告前收盘价,公告日涨幅%,1周涨幅%")
    for r in results:
        print(f"{r[0]},{r[3]:.2f},{r[4]:.2f},{r[5]:.2f}")