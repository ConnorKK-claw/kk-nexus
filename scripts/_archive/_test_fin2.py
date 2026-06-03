import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
import sys
sys.stdout.reconfigure(encoding="utf-8")
import akshare as ak
import pandas as pd

# Get financial abstracts
codes = [
    ("上港集团", "600018"),
    ("华谊集团", "600623"),
    ("东方创业", "600278"),
    ("赢合科技", "300457"),
    ("申能股份", "600642"),
    ("华建集团", "600629"),
    ("上海电气", "601727"),
    ("国泰君安", "601211"),
    ("外服控股", "600662"),
    ("上海机场", "600009"),
    ("锦江酒店", "600754"),
    ("上海建科", "603153"),
]

def get_np(symbol, year):
    try:
        df = ak.stock_financial_abstract(symbol=symbol)
        if df is None or len(df) == 0:
            return None
        # Find row for the given year (年报)
        for _, row in df.iterrows():
            date_str = str(row.iloc[0])
            if str(year) in date_str and ("12-31" in date_str or "年报" in date_str or "年度" in date_str):
                # 净利润 is usually the third or fourth column
                for col in df.columns:
                    if "净" in str(col) and "利" in str(col):
                        val = row[col]
                        try:
                            return round(float(val) / 100000000, 2) if abs(float(val)) > 100000 else round(float(val), 2)
                        except:
                            return None
        return None
    except:
        return None

for name, code in codes:
    try:
        df = ak.stock_financial_abstract(symbol=code)
        print(f"\n{name} ({code}): columns={list(df.columns)[:5]}")
        print(df.head(3).to_string())
        break
    except Exception as e:
        print(f"{name}: {str(e)[:60]}")
