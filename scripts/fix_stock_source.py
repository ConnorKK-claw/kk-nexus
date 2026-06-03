import sys, os, re
sys.stdout.reconfigure(encoding="utf-8")
path = os.path.join("C:", os.sep.join(["Users","hexk","OneDrive","文档","New project 6","scripts","gen_bb0_comparison.py"]))
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix stock_source for each company
lines = content.split("\n")
current_company = None
result = []
for line in lines:
    m = re.search(r'"company": "(.+?)"', line)
    if m:
        current_company = m.group(1)
    if '"stock_source":' in line and current_company:
        if current_company in ["上海建科", "东方创业", "锦江酒店", "上海机场", "申能股份", "国慕君安"]:
            line = '        "stock_source": "二级市场回购",'
        elif current_company in ["上港集团", "华谊集团", "外服控股"]:
            line = '        "stock_source": "定向增发",'
        elif current_company == "华建集团":
            line = '        "stock_source": "定向增发",'
    result.append(line)

content = "\n".join(result)

# Fix 赢合科技 specifically for the two rounds
content = content.replace(
    '"company": "赢合科技",\n        "code": "300457.SZ",\n        "plan_year": "2017"',
    '"company": "赢合科技",\n        "code": "300457.SZ",\n        "plan_year": "2017"')
content = content.replace(
    content[content.find('"company": "赢合科技"'):content.find('"company": "赢合科技"')+200].split('"stock_source"')[0] + '"stock_source": "定向增发"',
    'XXX')

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

cnt_dxzf = content.count('"stock_source": "定向增发"')
cnt_erjig = content.count('"stock_source": "二级市场回购"')
print(f"dxzf={cnt_dxzf}, erjig={cnt_erjig}")