import os

REPORT_FILE = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge\zk-ei-bb0-0-11-cases-comparison-report.md"

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Update 赢合科技 2022 row in Table 6
old_row = "| 赢合科技 (2022第二轮) | 待查 | — | — | — | — | — |"
new_row = "| 赢合科技 (2022第二轮) | 2 | 14.00 | 1.90 | 8.00 | 财务总监 | 7.00 |"

if old_row in content:
    content = content.replace(old_row, new_row)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated 赢合科技 2022 in Table 6")
else:
    print("Old row not found! Checking...")
    # Search for the line
    for i, line in enumerate(content.split("\n")):
        if "赢合科技 (2022第二轮)" in line:
            print(f"Line {i}: {line}")
