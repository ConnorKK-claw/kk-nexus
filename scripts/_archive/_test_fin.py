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

# Try getting financial data for a few companies
codes = [
    ("上港集团", "600018"),
    ("东方创业", "600278"),
    ("华谊集团", "600623"),
    ("赢合科技", "300457"),
    ("申能股份", "600642"),
    ("华建集团", "600629"),
    ("国泰君安", "601211"),
    ("上海电气", "601727"),
]

for name, code in codes:
    try:
        # Try getting financial data
        df = ak.stock_financial_abstract(symbol=code, indicator="")
        if df is not None and len(df) > 0:
            print(f"\n{name} ({code}):")
            print(df.head(3).to_string())
            break  # Just test one
    except Exception as e:
        print(f"{name}: {str(e)[:60]}")
