import os

VAULT_CASES = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\cases"
case_file = os.path.join(VAULT_CASES, "2026-05-17-国泰君安-限制性股票激励计划-case.md")

# Read the file
with open(case_file, "r", encoding="utf-8") as f:
    content = f.read()

exec_section = """

## 高管获授明细

首次授予高级管理人员获授情况：

| 姓名 | 职务 | 获授股数(万股) | 占授予总量比例 | 占总股本比例 |
|:---|:---|:---:|:---:|:---:|
| 王松 | 副董事长、执行董事、总裁 | 72.2 | 0.81% | 0.0081% |
| 朱健 | 副总裁 | 65.0 | 0.73% | 0.0073% |
| 蒋忆明 | 副总裁 | 65.0 | 0.73% | 0.0073% |
| 陈煜涛 | 副总裁 | 65.0 | 0.73% | 0.0073% |
| 龚德雄 | 副总裁 | 65.0 | 0.73% | 0.0073% |
| 喻健 | 执行董事、董事会秘书 | 59.5 | 0.67% | 0.0067% |
| 谢乐斌 | 财务总监、首席风险官 | 59.5 | 0.67% | 0.0067% |
| **高管合计7人** | — | **451.2** | **5.07%** | **—** |
| 其他核心骨干（约444人） | — | 约7,708.1 | 约86.59% | — |
| **首次合计（451人）** | — | **8,159.3** | **100%** | **—** |

> 数据来源：草案中的激励对象分配表。预留授予部分未在本次范围。

"""

# Check if already has exec section
if "高管获授明细" in content:
    import re
    pattern = r"## 高管获授明细.*?(?=\n## |\Z)"
    content = re.sub(pattern, exec_section.strip(), content, flags=re.DOTALL)
else:
    if "## 参考文件" in content:
        content = content.replace("## 参考文件", exec_section + "\n## 参考文件")
    elif "## 案例价值" in content:
        content = content.replace("## 案例价值", exec_section + "\n## 案例价值")
    else:
        content = content.rstrip() + "\n" + exec_section

with open(case_file, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Updated 国泰君安 case file with exec section")
