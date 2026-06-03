import os, sys
sys.stdout.reconfigure(encoding="utf-8")

wrk = r"C:\Users\hexk\OneDrive\文档\New project 6"

# Read current 外服 case from vault
vpath = os.path.join(os.environ["USERPROFILE"], ".codex", "skills", "equity-incentive", "vault", "cases", "2026-05-17-外服控股-限制性股票激励计划-case.md")
with open(vpath, "r", encoding="utf-8") as f:
    c = f.read()

# Add performance data before the unlock progress section
perf = """

## 业绩考核目标

### 授予条件（以2020年为基准）
- 每股收益不低于0.210元/股
- 营业收入（较2018年）增长率不低于30%，且不低于国际领先对标50分位或同行业平均值
- 新兴业务收入绝对值不低于70亿元

### 各解除限售期业绩条件

| 考核指标 | 第一批(2022年) | 第二批(2023年) | 第三批(2024年) |
|---------|:------------:|:------------:|:------------:|
| 每股收益 | >=0.230元 | >=0.253元 | >=0.290元 |
| 营业收入增长率(较2020) | >=33.0%(117.53亿) | >=52.9%(135.16亿) | >=75.9%(155.43亿) |
| 新兴业务收入绝对值 | >=100.60亿元 | >=116.70亿元 | >=135.37亿元 |

> 注意：所有营业收入指标同时要求不低于国际领先企业对标组75分位或同行业平均值。

### 员工规模
- 员工总数：2,998人（2021-12-31）
- 激励占比：7.17%（215人/2,998人）
- 总股本：226,327.95万股（约22.63亿股）
"""

if "## 业绩考核目标" not in c:
    c = c.replace("## 二、解锁完成进度", perf + "\n\n## 二、解锁完成进度")

# Write to updated_cases
outdir = os.path.join(wrk, "updated_cases")
os.makedirs(outdir, exist_ok=True)
outpath = os.path.join(outdir, "2026-05-17-外服控股-限制性股票激励计划-case.md")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(c)
print(f"Written: {outpath} ({len(c)} chars)")