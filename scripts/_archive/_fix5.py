import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

path = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# Fix unlock_structure for 4 companies that should be 40%/30%/30%
# Pattern: find company id, then fix its unlock_structure
lines = c.split("\n")
current_id = None
for i, line in enumerate(lines):
    m = re.search(r'"id": (\d+),', line)
    if m:
        current_id = int(m.group(1))
    # fix unlock_structure for 上海建科(1), 华谊(6), 上港(8), 上海机场(9)
    if current_id in [1, 6, 8, 9] and '"unlock_structure"' in line:
        if '"33%/33%/34%"' in line:
            lines[i] = line.replace('"33%/33%/34%"', '"40%/30%/30%"')
            print(f"Fixed unlock_structure for id={current_id}")

c2 = "\n".join(lines)

with open(path, "w", encoding="utf-8") as f:
    f.write(c2)

print("Done!")