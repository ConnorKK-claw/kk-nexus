import sys, re
from pathlib import Path

def make_sections(skill_name, domain):
    top_lines = []
    top_lines.append("")
    top_lines.append("## 会话启动序列")
    top_lines.append("")
    top_lines.append("每次加载时按顺序加载以下上下文：")
    top_lines.append("1. **SOUL.md** — 确立" + skill_name + "身份")
    top_lines.append("2. **TOOLS.md** — 确认工具偏好与数据源")
    top_lines.append("3. **vault/knowledge/index.md** — O(1) 全貌检索")
    top_lines.append("4. 按需加载具体知识节点")
    top_lines.append("")
    top_lines.append("## 工具偏好")
    top_lines.append("")
    top_lines.append("遇到以下需求时，先查 TOOLS.md 选择最合适的工具：")
    top_lines.append("")
    top_lines.append("| 场景 | 首选工具 | 备选 |")
    top_lines.append("|------|---------|------|")

    if 'equity' in domain:
        top_lines.append("| PDF表格提取 | pdfplumber | markitdown |")
        top_lines.append("| 通用PDF转MD | markitdown | — |")
        top_lines.append("| A股历史股价 | tushare | fetch_market_data.py |")
        top_lines.append("| 公司公告查询 | cninfo API | browser |")
        top_lines.append("| 财务建模 | spreadsheet 插件 | — |")
    else:
        top_lines.append("| PDF报表提取 | pdfplumber | markitdown |")
        top_lines.append("| 凭证/发票转MD | markitdown | — |")
        top_lines.append("| 税务文件解析 | pdfplumber | — |")
        top_lines.append("| 财务建模 | spreadsheet 插件 | — |")

    top_lines.append("")
    top_lines.append("## 大文档分块策略（>100页）")
    top_lines.append("")
    top_lines.append("年报/审计报告：按\"财务报表/附注/管理层讨论\"分块")
    top_lines.append("法规文件：按\"章节/条款\"分块")
    if 'equity' in domain:
        top_lines.append("激励计划公告：按\"方案概要/授予明细/考核办法\"分块")

    top = "\n".join(top_lines)

    yaml_lines = []
    yaml_lines.append("")
    yaml_lines.append("### 知识节点 YAML Schema")
    yaml_lines.append("")
    yaml_lines.append("所有 vault 文件必须包含 YAML frontmatter：")
    yaml_lines.append("")
    yaml_lines.append("`yaml")
    yaml_lines.append("title: 文件标题")
    yaml_lines.append("date: YYYY-MM-DD")
    yaml_lines.append("source: user | agent | distilled")
    yaml_lines.append("original_source: user | agent")
    yaml_lines.append("domain: " + domain)
    yaml_lines.append("tags: [标签1, 标签2]")
    yaml_lines.append("status: raw | distilled | verified | expired")
    yaml_lines.append("related:")
    yaml_lines.append('  - id: "zk-' + domain + '-{catseq}-{docseq}-{slug}"')
    yaml_lines.append('    type: "引用 | 对比 | 上位法 | 补充 | 案例参考"')
    yaml_lines.append("freshness_months: 6")
    yaml_lines.append("last_reviewed: YYYY-MM-DD")
    yaml_lines.append("imported_by: vault_ingest.py | bootstrap | manual")
    yaml_lines.append("imported_at: YYYY-MM-DDTHH:MM:SS")
    yaml_lines.append("`")
    yaml_schema = "\n".join(yaml_lines)

    bottom_lines = []
    bottom_lines.append("")
    bottom_lines.append("## 增强技能协议")
    bottom_lines.append("")
    bottom_lines.append("| 技能 | 位置 | 激活条件 |")
    bottom_lines.append("|------|------|---------|")
    bottom_lines.append("| spreadsheet | 内置插件 | 涉及财务测算、模型构建时 |")
    bottom_lines.append("| pdf | skills/pdf/ | 用户上传或引用PDF文件时 |")
    bottom_lines.append("| markdown-converter | skills/markdown-converter/ | 需将非MD文件导入 vault raw/ 时 |")
    bottom_lines.append("| browser | 内置插件 | 查询公开数据/公司公告/市场数据时 |")
    if 'equity' in domain:
        bottom_lines.append("| a-share-research | skills/a-share-research/ | 需进行A股同行对标分析时 |")
    bottom_lines.append("")
    bottom_lines.append("## 对话结晶协议（Crystallize）")
    bottom_lines.append("")
    bottom_lines.append("当用户提出 vault 无法回答的问题，讨论后得到有价值答案时：")
    bottom_lines.append("1. 记录完整问答到 vault/journal/YYYY-MM-DD.md")
    bottom_lines.append("2. 有长期价值 -> 创建知识节点（按领域归入对应分类码）")
    bottom_lines.append("3. 使用日志前缀格式：## [YYYY-MM-DD] operation | Title")
    bottom_lines.append("4. 节点必须含 related 引用和 freshness_months")
    bottom_lines.append("5. 运行 python build_index.py <vault-path> 重建索引")
    bottom_lines.append("")
    bottom_lines.append("## Lint 协议（定期维基清洁）")
    bottom_lines.append("")
    bottom_lines.append("触发：每5次会话或用户要求\"检查 vault 健康\"时")
    bottom_lines.append("1. 孤立节点检查 -> 标记或补充链接")
    bottom_lines.append("2. 过期知识检查 -> 超期未审查提醒")
    bottom_lines.append("3. 矛盾声明检查 -> 节点间说法不一致时标记")
    bottom_lines.append("4. 破损引用检查 -> related 目标文件不存在时修复")
    bottom_lines.append("5. 未蒸馏提醒 -> raw/ 超5个文件14天未蒸馏")
    bottom_lines.append("执行：python health_check.py <vault-path> --lint-mode")
    bottom_lines.append("")
    bottom_lines.append("## 知识保鲜协议")
    bottom_lines.append("")
    bottom_lines.append("| 分类 | 保鲜周期 | 审查方式 |")
    bottom_lines.append("|------|---------|---------|")
    bottom_lines.append("| aa0 法规框架 | 每6个月 | 重新审查源文件确认有效性 |")
    bottom_lines.append("| bb0 操作实务 | 每12个月 | 流程变化时更新 |")
    bottom_lines.append("| cases 案例 | 每6个月 | 更新数据/状态 |")
    bottom_lines.append("| dd0/gg0 测算/蒸馏 | 每12个月 | 确认内容准确性 |")
    bottom_lines.append("")
    bottom_lines.append("## WAL 协议（会话结束前执行）")
    bottom_lines.append("")
    bottom_lines.append("1. 更新 SESSION-STATE.md")
    bottom_lines.append("2. 写入 memory/YYYY-MM-DD.md（前缀 ## [YYYY-MM-DD] operation | Title）")
    bottom_lines.append("3. 上下文 > 60% 追加 working-buffer.md")
    bottom_lines.append("4. 运行 python scripts/unified_index.py --refresh")
    bottom_lines.append("5. 运行 python scripts/consolidate_learnings.py")
    bottom_lines.append("")
    bottom = "\n".join(bottom_lines)
    return top, yaml_schema, bottom

def process_skill(filepath, skill_name, domain):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    top, yaml_schema, bottom = make_sections(skill_name, domain)

    # Step A: Insert top sections before first ## (after YAML frontmatter)
    yaml_end = 0
    if content.startswith('---'):
        end_idx = content.find('---', 3)
        if end_idx != -1:
            yaml_end = end_idx + 3

    after_yaml = content[yaml_end:]
    first_heading = after_yaml.find('\n## ')
    if first_heading == -1:
        first_heading = after_yaml.find('## ')
    if first_heading != -1:
        insert_pos = yaml_end + first_heading
        content = content[:insert_pos] + '\n' + top + '\n' + content[insert_pos:]

    # Step B: Insert YAML Schema after directory structure
    idx = content.find('auto-update/')
    if idx != -1:
        rest = content[idx:]
        next_heading = rest.find('\n## ')
        next_sep = rest.find('\n---')
        if next_heading != -1 and (next_sep == -1 or next_heading < next_sep):
            best_pos = idx + next_heading
        elif next_sep != -1:
            best_pos = idx + next_sep
        else:
            best_pos = len(content)
        content = content[:best_pos] + '\n' + yaml_schema + '\n' + content[best_pos:]

    # Step C: Append bottom sections
    content = content.rstrip() + '\n' + bottom + '\n'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    sections = [l.strip() for l in content.split('\n') if l.startswith('## ')]
    return sections

# Process 001
print("Processing 001 equity-incentive...")
s1 = process_skill(
    r'C:\Users\hexk\OneDrive\文档\New project 6\_upgrade_sk\001_SKILL.md',
    '股权激励专家',
    'equity-incentive'
)
print("  001 sections: " + str(len(s1)))
for s in s1:
    print("    " + s)

# Process 002
print()
print("Processing 002 tax-compliance...")
s2 = process_skill(
    r'C:\Users\hexk\OneDrive\文档\New project 6\_upgrade_sk\002_SKILL.md',
    '财税合规专家',
    'tax-compliance'
)
print("  002 sections: " + str(len(s2)))
for s in s2:
    print("    " + s)

print()
print("DONE")
