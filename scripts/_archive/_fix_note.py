REPORT_FILE = r"C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge\zk-ei-bb0-0-11-cases-comparison-report.md"

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Update footnote
old_note = "- 赢合科技2022年第二轮高管明细待从草案中提取"
new_note = "- 赢合科技2022年第二轮仅2名高管有明确获授数（刘永青8.0万、李春辉6.0万），其余为中层及骨干"

if old_note in content:
    content = content.replace(old_note, new_note)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated footnote")
else:
    print("Footnote not found, checking...")
    for i, line in enumerate(content.split("\n")):
        if "待从草案" in line:
            print(f"Line {i}: {line}")
