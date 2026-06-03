import os, sys
sys.stdout.reconfigure(encoding="utf-8")

path = os.path.join("C:\\Users\\hexk\\OneDrive\\文档\\New project 6", "scripts", "gen_bb0_comparison.py")

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '"id": 6,' in line and 'unlock_schedule' in lines[i+3]:
        lines[i+3] = lines[i+3].replace("33% / 33% / 34%", "40% / 30% / 30%")
        print(f"Fixed line {i+3}: 华谊 -> 40/30/30")
        break
    # Also check next few lines
    if '"id": 6,' in line:
        for j in range(1, 10):
            if 'unlock_schedule' in lines[i+j]:
                if "33%" in lines[i+j]:
                    lines[i+j] = lines[i+j].replace("33% / 33% / 34%", "40% / 30% / 30%")
                    print(f"Fixed line {i+j}: 华谊 -> 40/30/30")
                break

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)

# Verify
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
print(f"40/30/30: {c.count('40% / 30% / 30%')}")
print(f"33/33/34: {c.count('33% / 33% / 34%')}")