import os

VAULT_CASES = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\cases"
case_file = os.path.join(VAULT_CASES, "2026-05-17-华建集团-限制性股票激励计划-case.md")

exec_section_2022 = """
## 2022年（第二轮）高管获授明细

| 姓名 | 职务 | 获授股数(万股) | 占授予总量比例 | 占目前总股本比例 |
|:---|:---|:---:|:---:|:---:|
| 沈立东 | 董事、总经理 | 70.18 | 3.13% | 0.11% |
| 龙革 | 副总经理 | 63.16 | 2.82% | 0.10% |
| 徐志浩 | 副总经理、董事会秘书 | 63.16 | 2.82% | 0.10% |
| 周静瑜 | 副总经理 | 60.36 | 2.69% | 0.10% |
| 疏正宏 | 副总经理 | 55.72 | 2.49% | 0.09% |
| 王卫东 | 总工程师 | 58.95 | 2.63% | 0.09% |
| **高管合计6人** | — | **371.53** | **17.10%** | **—** |

"""

with open(case_file, "r", encoding="utf-8") as f:
    content = f.read()

# Insert after the 2018 exec section
if "## 2022年（第二轮）高管获授明细" not in content:
    # Find the 2018 exec section end and insert before ## 参考文件
    marker = "## 参考文件"
    if marker in content:
        content = content.replace(marker, exec_section_2022.strip() + "\n\n" + marker)
    
    with open(case_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added 2022 exec section to 华建集团 case")
else:
    print("2022 exec section already exists")
