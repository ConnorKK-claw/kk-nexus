import os, json

# Load comparison report data from the report
REPORT_FILE = r'C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge\zk-ei-bb0-0-11-cases-comparison-report.md'

with open(REPORT_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract Table 1: grant price per company
import re
# Find table 1
m = re.search(r'## 表1.*?\n(\|.*?\n)+', content, re.DOTALL)
if m:
    table1 = m.group()
    lines = table1.split('\n')
    prices = {}  # company -> grant_price
    for line in lines:
        if line.startswith('| ') and '公司/计划' not in line and '---' not in line:
            cells = [c.strip() for c in line.split('|')]
            if len(cells) >= 8:
                company = cells[1]
                price_str = cells[7]
                try:
                    price = float(price_str)
                except:
                    price = 0
                prices[company] = price
    print('=== 授予价格 ===')
    for k,v in prices.items():
        print(f'{k}: {v}元/股')
