# -*- coding: utf-8 -*-
"""Fix errors in the comparison report"""

REPORT_FILE = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge\zk-ei-bb0-0-11-cases-comparison-report.md"

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    content = f.read()

changes = []

# Fix 1: 华建集团2018 激励人数 379→339 (草案计划379人, 实际授予339人)
old = "| 华建集团 (2018第一轮) | 6292 | 379 | 6.02 | 1296.62 | 约3% | 3.82 | 定向增发 |"
new = "| 华建集团 (2018第一轮) | 6292 | 339 | 5.39 | 1296.62 | 3.00 | 3.82 | 定向增发 |"
if old in content:
    content = content.replace(old, new)
    changes.append("Fix 1: 华建2018 激励人数379→339, 占比6.02%→5.39%, 约3%→3.00%")
    
# Fix 2: 华建2018 占比重算: 339/6292=5.39%

# Fix 3: 表6 华建2018 高管合计正确为10人(从PDF提取的)
# Table 6 entries look correct based on our extraction

# Fix 4: 表1 国泰君安/国泰海通 中 国泰海通(2020) 是国泰君安+海通合并后名称,但计划是2020年国泰君安实施的
# The plan was implemented by 国泰君安 in 2020, before the merger
# This is fine as is since the report already notes the name change

# Fix 5: 表1 - "授予价/公告日市价比(%)" 添加明确的标注
old_h = "| 公司/计划 | 激励方式 | 股票来源 | 草案公告日 | 草案日PB | 授予日 | 授予价格(元/股) | 授予价/公告日市价比(%) | 锁定期 | 解锁安排 | 当前状态 |"
new_h = "| 公司/计划 | 激励方式 | 股票来源 | 草案公告日 | 草案日PB | 授予日 | 授予价格(元/股) | 授予价/草案公告日市价比(%) | 锁定期 | 解锁安排 | 当前状态 |"
if old_h in content:
    content = content.replace(old_h, new_h)
    changes.append("Fix 5: 列标题 '公告日市价比' → '草案公告日市价比'")

print("\n".join(changes))

# Write back
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n{len(changes)} fixes applied")
