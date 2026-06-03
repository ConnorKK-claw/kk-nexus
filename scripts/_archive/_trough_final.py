import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "*"
import sys
sys.stdout.reconfigure(encoding="utf-8")
import akshare as ak

companies = [
    ("上港集团", "600018", 2020, [2017, 2018, 2019, 2020, 2021, 2022]),
    ("国泰君安", "601211", 2019, [2017, 2018, 2019, 2020, 2021, 2022]),
    ("华谊集团", "600623", 2019, [2017, 2018, 2019, 2020, 2021]),
    ("申能股份", "600642", 2019, [2017, 2018, 2019, 2020, 2021]),
    ("东方创业", "600278", 2020, [2017, 2018, 2019, 2020, 2021, 2022]),
    ("华建集团", "600629", 2017, [2015, 2016, 2017, 2018, 2019]),
    ("华建集团", "600629", 2021, [2019, 2020, 2021, 2022, 2023]),
    ("上海电气", "601727", 2017, [2015, 2016, 2017, 2018, 2019]),
    ("上海机场", "600009", 2023, [2019, 2020, 2021, 2022, 2023, 2024]),
    ("锦江酒店", "600754", 2023, [2019, 2020, 2021, 2022, 2023, 2024]),
    ("上海建科", "603153", 2024, [2021, 2022, 2023, 2024]),
    ("赢合科技", "300457", 2016, [2014, 2015, 2016, 2017, 2018]),
    ("赢合科技", "300457", 2021, [2019, 2020, 2021, 2022, 2023]),
    ("外服控股", "600662", 2020, [2017, 2018, 2019, 2020, 2021, 2022]),
]

def get_np_series(symbol, years):
    try:
        df = ak.stock_financial_abstract(symbol=symbol)
        if df is None or len(df) == 0: return {}
        np_row = None
        for _, row in df.iterrows():
            if "归母净利润" in str(row.iloc[1]):
                np_row = row
                break
        if np_row is None: return {}
        results = {}
        for y in years:
            for col_key in [f"{y}1231", f"{y}0930"]:
                if col_key in df.columns:
                    try:
                        v = float(np_row[col_key])
                        # Determine unit: if huge numbers, convert
                        if v > 1e10: v = round(v / 1e8, 2)
                        elif v > 1e8: v = round(v / 1e8, 2)
                        results[y] = round(v, 2)
                        break
                    except: pass
        return results
    except: return {}

print(f"{'公司':<16} {'基年':<5} {'基年归母净利(亿)':>16} {'前序年份趋势':<30} {'结论'}")
print("-"*85)

for name, code, base_yr, years in companies:
    nps = get_np_series(code, years)
    if not nps:
        print(f"{name:<16} {base_yr:<5} {'NODATA':>16}")
        continue
    sv = sorted(nps.keys())
    base_val = nps.get(base_yr, "N/A")
    
    # Show trend
    trend_parts = []
    for y in years:
        if y in nps:
            trend_parts.append(f"{y}:{nps[y]}亿")
    trend = " → ".join(trend_parts)
    
    # Analyze
    before = [nps[y] for y in years if y < base_yr and y in nps]
    after = [nps[y] for y in years if y > base_yr and y in nps]
    all_chk = before + [nps.get(base_yr, 0)] + after
    
    is_trough = False
    note = ""
    if len(before) >= 1 and len(after) >= 1:
        b_avg = sum(before) / len(before)
        a_avg = sum(after) / len(after)
        bv = nps.get(base_yr, 0)
        if bv <= b_avg * 0.85 and bv <= a_avg * 0.85:
            is_trough = True
            note = "✅ 基年为明显洼地"
        elif bv <= b_avg * 0.9:
            is_trough = True
            note = "✅ 基年相对前序偏低"
        elif bv < b_avg and bv < a_avg:
            note = "⚠️ 基年略低于前后均值"
        else:
            note = "❌ 基年非洼地"
    else:
        note = "数据不足以判断"
    
    print(f"{name:<16} {base_yr:<5} {str(base_val)+'亿':>16} {trend:<50} {note}")
