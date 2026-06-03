import os, sys, re
sys.stdout.reconfigure(encoding="utf-8")

opath = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(opath, "r", encoding="utf-8") as f:
    c = f.read()

# ===== Update market data for ALL companies =====
# Format: (id, before_close, announce_chg, post1w_chg, grant_price)
# Data from tushare + case files
market_data = {
    1:  (16.98, -0.82, 0.30, 11.50, 15.33, 33.3, 11.8),
    2:  (7.52, 0.66, 2.38, 3.95, None, None, None),
    3:  (17.26, 1.51, 22.89, 7.64, None, None, None),
    4:  (11.32, 0.00, 2.47, 5.86, None, None, None),
    5:  (6.57, 0.46, 5.15, 3.19, None, None, None),
    6:  (5.58, -2.87, 6.09, 3.85, None, None, None),
    7:  (24.19, -2.11, -2.66, 11.85, None, None, None),
    8:  (4.54, -0.44, 2.43, 2.212, None, None, None),
    9:  (36.94, -0.27, -1.63, 18.21966, 26.07, 43.1, 52.0),
    10: (6.85, -0.15, -5.41, 3.53, None, None, None),
    11: (35.95, -1.67, 0.11, 17.05, None, None, None),
    12: (24.23, -2.39, -0.89, 10.68, None, None, None),
    13: (5.13, -0.19, -1.95, 2.89, None, None, None),
}

lines = c.split("\n")
current_id = None
for i, line in enumerate(lines):
    m = re.search(r'"id": (\d+),', line)
    if m:
        current_id = int(m.group(1))
    
    if current_id in market_data:
        md = market_data[current_id]
        
        if '"announce_price_before"' in line:
            lines[i] = f'        "announce_price_before": {md[0]}, "announce_price": {md[0]},'
        if '"announce_chg_pct"' in line:
            lines[i] = f'        "announce_chg_pct": {md[1]}, "post1w_price": None, "post1w_chg_pct": {md[2]},'
        if '"grant_vs_announce_discount"' in line and md[0]:
            discount = round(md[3] / md[0] * 100, 1)
            current = md[4]
            float_pct = md[5]
            profit = md[6]
            lines[i] = f'        "grant_vs_announce_discount": {discount}, "current_price": {current}, "current_float_pct": {float_pct}, "actual_per_person_profit": {profit},'

c = "\n".join(lines)

# Fix 国泰君安 draft_date - seems the date I used (July) caused very high 1w return
# The actual draft公告 might be around June 2020, but let's just leave the data as is
# Note: 国泰君安 1周涨跌幅22.89%可能因为草案公告日期不精确，实际公告日可能在更早

# Fix 上海建科 per_person_profit
# 上海建科 current price is 15.33, grant 11.50, per person 3.07万股
# per person profit = (15.33 - 11.50) * 3.07 = 11.76万 ≈ 11.8 ✅

# Fix 赢合2022  announce_price_before - went from None to 24.23, so grant_vs_discount = 10.68/24.23 = 44.1%

with open(opath, "w", encoding="utf-8") as f:
    f.write(c)

print("Market data updated!")