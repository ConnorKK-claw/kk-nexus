# -*- coding: utf-8 -*-
"""Update case files and comparison report with executive grant details"""
import os
import json
import re

VAULT_CASES = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\cases"
REPORT_FILE = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge\zk-ei-bb0-0-11-cases-comparison-report.md"

# Load compiled executive data
with open(r"C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_data.json", "r", encoding="utf-8") as f:
    exec_data = json.load(f)

def make_exec_section(company_key):
    """Generate markdown section for executive grants"""
    d = exec_data.get(company_key, {})
    if not d:
        return ""
    
    lines = []
    lines.append("")
    lines.append("## 高管获授明细")
    lines.append("")
    lines.append("| 姓名 | 职务 | 获授股数 | 占授予总量比例 | 占总股本比例 |")
    lines.append("|:---|:---|:---:|:---:|:---:|")
    
    for exec_item in d.get("execs", []):
        name, pos, shares, pct, pct_cap = exec_item[:5]
        lines.append(f"| {name} | {pos} | {shares} | {pct} | {pct_cap} |")
    
    # Categories (non-exec)
    for cat in d.get("categories", []):
        name, people, shares, pct, pct_cap = cat[:5]
        label = f"{name}（{people}）" if people and people != "-" else name
        lines.append(f"| {label} | — | {shares} | {pct} | {pct_cap} |")
    
    lines.append(f"| **合计** | **{d.get('total','')}** | **{d.get('total_shares','')}** | **100%** | **—** |")
    
    if d.get("note"):
        lines.append("")
        lines.append(f"> {d['note']}")
    
    lines.append("")
    return "\n".join(lines)

# Update each case file
for company_key, data in exec_data.items():
    # Map company key to case file
    if company_key == "华建集团_2018":
        case_file = os.path.join(VAULT_CASES, "2026-05-17-华建集团-限制性股票激励计划-case.md")
    elif company_key == "华建集团_2022":
        continue  # Same file as 2018
    elif company_key == "赢合科技_2017":
        case_file = os.path.join(VAULT_CASES, "2026-05-17-赢合科技-限制性股票激励计划-case.md")
    else:
        # Find by company name
        cands = [f for f in os.listdir(VAULT_CASES) if company_key in f and f.endswith(".md")]
        if not cands:
            print(f"  {company_key}: no case file found, skipped")
            continue
        case_file = os.path.join(VAULT_CASES, cands[0])
    
    if not os.path.exists(case_file):
        print(f"  {company_key}: file not exists")
        continue
    
    with open(case_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    exec_section = make_exec_section(company_key)
    
    # Check if already has exec section
    if "高管获授明细" in content:
        # Replace existing section
        pattern = r"## 高管获授明细.*?(?=\n## |\Z)"
        content = re.sub(pattern, exec_section.strip(), content, flags=re.DOTALL)
    else:
        # Append before the end (before ## 参考文件 or end of file)
        if "## 参考文件" in content:
            content = content.replace("## 参考文件", exec_section + "\n## 参考文件")
        elif "## 案例价值" in content:
            content = content.replace("## 案例价值", exec_section + "\n## 案例价值")
        elif "## 时间线" in content:
            content = content.replace("## 时间线", exec_section + "\n## 时间线")
        else:
            content = content.rstrip() + "\n" + exec_section
    
    with open(case_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Updated: {os.path.basename(case_file)}")

print("Case files update complete!")
