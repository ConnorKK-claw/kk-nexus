import re, os, sys
sys.stdout.reconfigure(encoding="utf-8")

path = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(path, "r", encoding="utf-8") as f:
    c = f.read()

fixes_ids = [1, 7, 8, 9]  # 上海建科, 华谊, 上港, 上海机场

lines = c.split("\n")
current_id = None
for i, line in enumerate(lines):
    m = re.search(r'"id": (\d+),', line)
    if m:
        current_id = int(m.group(1))
    if current_id in fixes_ids and "unlock_schedule" in line:
        if "33% / 33% / 34%" in line:
            lines[i] = line.replace("33% / 33% / 34%", "40% / 30% / 30%")
            print(f"Fixed id={current_id} to 40/30/30")

c2 = "\n".join(lines)

# Also fix perf_targets for 华建2018 and 华谊 etc that got东方创业's data wrong
# Find 华建2018 entry (id:4) and fix its perf
lines = c2.split("\n")
current_id = None
current_company = None
for i, line in enumerate(lines):
    m = re.search(r'"id": (\d+),', line)
    if m:
        current_id = int(m.group(1))
    m2 = re.search(r'"company": "(.+?)"', line)
    if m2:
        current_company = m2.group(1)
    if "perf_targets" in line and current_id:
        if current_id == 4:  # 华建2018
            lines[i] = '        "perf_targets": "营收复合增长>=8%+75分位; ROE>=9.0%/9.5%/10.0%+50分位; 研发>=3%",'
        elif current_id == 5:  # 华建2022
            lines[i] = '        "perf_targets": "（待补充; 第一批条件曾被调整）",'
        elif current_id == 6:  # 华谊
            lines[i] = '        "perf_targets": "归母净利增长率+ROE+研发>=2.2%+老字号品牌增长>=3%(蜂花/回力)+安全环保(约束)",'
        elif current_id == 8:  # 上港
            lines[i] = '        "perf_targets": "扣非加权ROE>=8.55%/8.60%/8.65%+行业均值; 扣非净利复合增长>=4%/6%/8%(较2020); 吞吐量(门槛)",'
        elif current_id == 10:  # 外服
            lines[i] = '        "perf_targets": "（待补充）",'

c3 = "\n".join(lines)

with open(path, "w", encoding="utf-8") as f:
    f.write(c3)

print("Done!")
print(f"40/30/30 in file: {c3.count('40% / 30% / 30%')}")
print(f"33/33/34 in file: {c3.count('33% / 33% / 34%')}")