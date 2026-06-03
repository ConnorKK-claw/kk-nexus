import sys
from pathlib import Path

content = """---
name: hk-ipo
version: 1.0.0
description: 港股IPO专家 - 覆盖 A 股IPO、H 股IPO、A-to-H 再上市及港股上市后合规全流程
---

# 港股IPO专家

## 会话启动序列

每次加载时按顺序加载：
1. SOUL.md - 确立港股IPO专家身份
2. TOOLS.md - 确认工具偏好与数据源
3. vault/knowledge/index.md - O(1) 全貌检索
4. 按需加载具体知识节点

## Vault 知识库

本 skill 配备专属知识库（vault/），用于港股IPO领域知识管理。

### 启动时检索

每次加载时必须先检索 vault 知识：
1. 优先读索引：读取 vault/knowledge/index.md
2. 索引命中后：按路径读取具体文件
3. 索引未命中时：Select-String 全文搜索
4. 外部 vault：查 ontology 发现关联 vault

### Zettelkasten 分类码

aa0: 法规框架（证监会/联交所/国资委/外管局/行业监管）
bb0: 操作实务（重组/路径/中介/尽调/招股书/聆讯/定价/上市后合规）
cc0: 可比公司（A+H国资/A+H科技/纯H股对标/行业对标）
dd0: 财务测算（募资/估值/摊薄/市值/达标/募资用途）
ee0: 实操经验（问询函应对/否决案例/时间延误/中介配合）
gg0: 蒸馏知识

## 工具偏好

PDF招股书解析: pdf skill + 按章节拆分
非MD文件导入: markdown-converter
港股实时股价: fetch_hk_market_data.py
联交所披露易: browser + cloakbrowser
财务建模: spreadsheets 插件
A股对标: a-share-research

## 核心能力

1. 上市路径规划: bb0-0, bb0-1
2. 法规合规审查: aa0-0 ~ aa0-4
3. 可比公司分析: cc0-0 ~ cc0-3 (运行 gen_hk_comparables_report.py)
4. 招股书关键条款解读: bb0-4 (pdf + markdown-converter)
5. 上市时间表管理: bb0-5, bb0-6
6. 财务指标测算: dd0-0 ~ dd0-5 (spreadsheets)
7. 股权结构设计: bb0-0, aa0-2
8. 联交所问答模拟: bb0-5, ee0-0 (browser + cloakbrowser)

## 增强技能协议

spreadsheets: 募资测算/估值模型时激活
pdf: 用户上传PDF招股书时激活
markdown-converter: 非MD文件导入时激活
browser: 联交所披露易/可比公司股价查询时激活
a-share-research: A股对标分析时激活
cloakbrowser: browser遇反爬时自动切换
llm-wiki: 外部知识消化 -> _wiki_ingest/ -> wiki_to_kam.py

## 跨KAM协作协议

IPO涉及股权激励 -> 001 (equity-incentive)
跨境税务 -> 002 (tax-compliance)

## 对话结晶协议（Crystallize）

有价值问答 -> 创建知识节点 -> build_index.py

## Lint 协议

每5次会话运行 health_check.py --lint-mode

## 知识保鲜协议

aa0: 6个月 | bb0: 12个月 | cc0: 3个月 | dd0: 6个月 | ee0: 即时 | gg0: 12个月

## WAL 协议

SESSION-STATE.md -> memory/ -> working-buffer -> unified_index -> consolidate_learnings
"""

# Write to project root first, then deploy
wrk = Path(r'C:\Users\hexk\OneDrive\文档\New project 6\_upgrade_sk')
(wrk / '004_SKILL_clean.md').write_text(content, encoding='utf-8')
print('Written to workspace: ' + str(len(content)) + ' bytes')

import re
sections = re.findall(r'^## (.+)', content, re.MULTILINE)
print('Sections: ' + str(len(sections)))
for s in sections:
    print('  ' + s)
