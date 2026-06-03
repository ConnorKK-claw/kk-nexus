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

# Companies with their baseline year
companies = [
    ("上港集团", "600018", 2020, [2018, 2019, 2020, 2021, 2022]),
    ("东方创业", "600278", 2020, [2018, 2019, 2020, 2021, 2022]),
    ("华谊集团", "600623", 2019, [2017, 2018, 2019, 2020, 2021]),
    ("赢合科技", "300457", 2016, [2014, 2015, 2016, 2017, 2018]),
    ("赢合科技", "300457", 2021, [2019, 2020, 2021, 2022, 2023]),
    ("申能股份", "600642", 2019, [2017, 2018, 2019, 2020, 2021]),
    ("华建集团", "600629", 2017, [2015, 2016, 2017, 2018, 2019]),
    ("华建集团", "600629", 2021, [2019, 2020, 2021, 2022, 2023]),
    ("上海电气", "601727", 2017, [2015, 2016, 2017, 2018, 2019]),
    ("国泰君安", "601211", 2019, [2017, 2018, 2019, 2020, 2021]),
    ("外服控股", "600662", 2020, [2018, 2019, 2020, 2021, 2022]),
    ("上海机场", "600009", 2023, [2021, 2022, 2023, 2024]),
    ("锦江酒店", "600754", 2023, [2021, 2022, 2023, 2024]),
    ("上海建科", "603153", 2024, [2022, 2023, 2024]),
]

def get_net_profits(symbol, years):
    """Get net profit for each year from financial abstract"""
    try:
        df = ak.stock_financial_abstract(symbol=symbol)
        if df is None or len(df) == 0:
            return {}
        
        # Find the 归母净利润 row
        np_row = None
        for _, row in df.iterrows():
            if "归母净利润" in str(row.iloc[1]) or "净利润" in str(row.iloc[1]):
                np_row = row
                break
        
        if np_row is None:
            return {}
        
        results = {}
        for y in years:
            col = f"{y}1231"
            if col in df.columns:
                val = np_row[col]
                try:
                    # Convert to 亿元
                    fval = float(val)
                    if abs(fval) > 100000000:
                        fval = fval / 100000000
                    elif abs(fval) > 10000:
                        fval = fval / 10000
                    results[y] = round(fval, 2)
                except:
                    results[y] = None
        
        return results
    except Exception as e:
        return {}

print(f"{'公司':<16} {'基年':<5} {'基年净利':>8} {'-2年':>8} {'-1年':>8} {'+1年':>8} {'+2年':>8} {'基年是否为洼地?'}")
print("-"*85)

for name, code, base_yr, years in companies:
    nps = get_net_profits(code, years)
    if not nps:
        print(f"{name:<16} {base_yr:<5} {'NODATA':>8}")
        continue
    
    sorted_yrs = sorted(nps.keys())
    base_val = nps.get(base_yr, None)
    
    # Determine if baseline is a trough
    is_trough = False
    comment = ""
    if base_val is not None:
        vals_before = [nps.get(y) for y in range(base_yr-2, base_yr) if y in nps and nps[y] is not None]
        vals_after = [nps.get(y) for y in range(base_yr+1, base_yr+3) if y in nps and nps[y] is not None]
        all_vals = vals_before + [base_val] + vals_after
        if len(all_vals) >= 3:
            # Check if base_val is the lowest
            min_val = min(all_vals)
            max_val = max(all_vals)
            if base_val == min_val and max_val > min_val * 1.1:
                is_trough = True
                comment = "✅ 明显洼地"
            elif base_val <= min(vals_before + vals_after) * 1.05 if vals_before and vals_after else False:
                is_trough = True
                comment = "✅ 相对低位"
            elif base_val <= sum(all_vals)/len(all_vals) * 0.9:
                is_trough = True
                comment = "✅ 偏低"
            else:
                comment = "❌ 非洼地"
        else:
            comment = "数据不足"
    else:
        comment = "无基年数据"
    
    row = f"{name:<16} {base_yr:<5} {base_val if base_val else 'N/A':>8}"
    for y in [base_yr-2, base_yr-1, base_yr+1, base_yr+2]:
        v = nps.get(y, "N/A")
        if isinstance(v, float):
            row += f"{v:>8.1f}"
        else:
            row += f"{'N/A':>8}"
    row += f"  {comment}"
    print(row)
