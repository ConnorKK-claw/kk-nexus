# -*- coding: utf-8 -*-
"""Update comparison report with executive grant details"""
import os
import re

REPORT_FILE = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge\zk-ei-bb0-0-11-cases-comparison-report.md"

exec_table = """
## 表6：高管获授明细对比

| 公司/计划 | 高管人数 | 高管授予总量(万股) | 占总授予比例(%) | 获授最高(万股) | 最高者职务 | 高管人均获授(万股) |
|:---|:---:|:---:|:---:|:---:|:---|:---:|
| 上海建科 (2025) | — | — | — | — | — | — |
| 东方创业 (2021) | 8 | 38.9 | 2.47 | 20.4 | 党委书记、董事、总经理 | 5.44 |
| 国泰君安/国泰海通 (2020) | 7 | 451.2 | 5.07 | 72.2 | 副董事长、总裁 | 64.46 |
| 华建集团 (2018第一轮) | 10 | 135.58 | 10.46 | 21.50 | 董事、总经理 | 13.56 |
| 华建集团 (2022第二轮) | 6 | 371.53 | 17.10 | 70.18 | 董事、总经理 | 61.92 |
| 华谊集团 (2020) | 8 | 365.84 | 14.47 | 63.28 | 董事、总裁 | 45.73 |
| 锦江酒店 (2024) | 5 | 23.6 | 2.95 | 7.4 | 董事、首席执行官 | 4.72 |
| 上港集团 (2021) | 7 | 834.59 | 6.43 | 134.61 | 执行董事、总裁 | 119.23 |
| 上海机场 (2024) | 4 | 17.38 | 1.65 | 4.69 | 董事、副总经理 | 4.35 |
| 外服控股 (2022) | 7 | 187.75 | 8.30 | 32.84 | 董事、总裁 | 26.82 |
| 赢合科技 (2017第一轮) | 7 | 128.00 | 20.38 | 30.00 | 财务总监 | 18.29 |
| 赢合科技 (2022第二轮) | 待查 | — | — | — | — | — |
| 申能股份 (2021) | 2+ | 108.1+ | 2.46+ | 56.9 | 副董事长、总经理 | 54.05 |

> 注：
> - 上海建科2025年计划按岗位分类披露，未按姓名列示高管个人获授数，故不适用
> - 东方创业草案仅列示赵晓东(18.5万)和李捷(20.4万)二人的明确获授数，其他6名高管的获授数未单独列示，此处统计仅供参考
> - 赢合科技2022年第二轮高管明细待从草案中提取
> - 申能股份草案仅列示奚力强(56.9万)和余永林(51.2万)，其他高管的获授数需从登记结果公告确认

"""

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Check if table 6 already exists
if "## 表6：高管获授明细对比" in content:
    pattern = r"## 表6：高管获授明细对比.*?(?=\n## |\Z)"
    content = re.sub(pattern, exec_table.strip(), content, flags=re.DOTALL)
    print("Replaced existing Table 6")
else:
    # Add before the final section
    marker = "\n---\n\n**生成时间："
    if marker in content:
        content = content.replace(marker, exec_table + "\n" + marker)
        print("Added Table 6 before generation timestamp")
    else:
        content += "\n" + exec_table
        print("Appended Table 6 at end")

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("Comparison report updated!")
