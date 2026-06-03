import os

case_file = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\cases\2026-05-17-赢合科技-限制性股票激励计划-case.md"

with open(case_file, "r", encoding="utf-8") as f:
    content = f.read()

exec_2022 = """
### 2022年（第二轮）高管获授明细

| 姓名 | 职务 | 获授股数(万股) | 占授予总量比例 | 占公司股本总额比例 |
|:---|:---|:---:|:---:|:---:|
| 刘永青 | 财务总监 | 8.00 | 1.08% | 0.0123% |
| 李春辉 | 董事会秘书 | 6.00 | 0.81% | 0.0092% |
| 中层管理人员及核心骨干（≤409人） | — | 724.22 | 98.10% | 1.1150% |
| **合计** | — | **738.22** | **100%** | **1.1365%** |

> 2022年计划仅2名高管具有明确获授数，其余中层及骨干未按姓名列示。实际登记认购缩水至346.59万股/168人。

"""

# Insert after the 第二轮 section and before ## 两轮计划对比
marker = "## 两轮计划对比"
if marker in content:
    # Find the exec_2022 section after the 第二轮 section
    content = content.replace(marker, exec_2022.strip() + "\n\n" + marker)
    
    with open(case_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added 2022 round exec data to 赢合科技 case")
else:
    print("Marker not found!")
