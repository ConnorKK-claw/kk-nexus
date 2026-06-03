import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import tushare as ts
pro = ts.pro_api()

# Check financial data for each company around their baseline year
# We need: 归母净利润 for baseline year and surrounding years

companies = [
    ("上海建科", "603153.SH", 2024, 2022, 2025),
    ("东方创业", "600278.SH", 2020, 2018, 2022),
    ("国泰君安", "601211.SH", 2019, 2017, 2021),
    ("华建集团", "600629.SH", 2017, 2015, 2019),
    ("华建集团(2022)", "600629.SH", 2021, 2019, 2023),
    ("华谊集团", "600623.SH", 2019, 2017, 2021),
    ("锦江酒店", "600754.SH", 2023, 2021, 2024),
    ("上港集团", "600018.SH", 2020, 2018, 2022),
    ("上海机场", "600009.SH", 2023, 2021, 2024),
    ("外服控股", "600662.SH", 2020, 2018, 2022),
    ("赢合科技(2017)", "300457.SZ", 2016, 2014, 2018),
    ("赢合科技(2022)", "300457.SZ", 2021, 2019, 2023),
    ("申能股份", "600642.SH", 2019, 2017, 2021),
    ("上海电气", "601727.SH", 2017, 2015, 2019),
]

print(f"{'公司':<16} {'基年':<6} {'基年净利':>10} {'前1年':>10} {'前2年':>10} {'后1年':>10} {'后2年':>10}")
print("-"*72)

def get_net_profit(code, year):
    """Get net profit for a given year (Q4 report = annual)"""
    try:
        # Get annual report (Q4 of each year)
        start = f"{year}0101"
        end = f"{year}1231"
        df = pro.daily(ts_code=code, start_date=start, end_date=end, fields="trade_date")
        if df is None or len(df) == 0:
            return None
        # Use income statement to get net profit
        df_f = pro.income(ts_code=code, start_date=start, end_date=end, fields="end_date,net_profit")
        if df_f is not None and len(df_f) > 0:
            # Filter for annual report (December)
            for _, row in df_f.iterrows():
                if row["end_date"].endswith("1231"):
                    np_val = float(row["net_profit"]) / 100000000  # convert to 亿元
                    return round(np_val, 2)
        return None
    except Exception as e:
        return None

# For 上海建科 which IPO'd in 2023, historical data might be limited
# Let me use a different approach - just show what we can get

for name, code, base_yr, start_yr, end_yr in companies:
    vals = {}
    for y in range(start_yr, end_yr + 1):
        v = get_net_profit(code, y)
        if v:
            vals[y] = v
    
    if vals:
        base_val = vals.get(base_yr, "N/A")
        row = f"{name:<16} {base_yr:<6}"
        for y in [base_yr-2, base_yr-1, base_yr, base_yr+1, base_yr+2]:
            if y in vals:
                row += f"{vals[y]:>10.2f}"
            else:
                row += f"{'N/A':>10}"
        print(row)
    else:
        print(f"{name:<16} {base_yr:<6} {'NO DATA':>10}")
