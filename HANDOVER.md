# Super KAM — 项目交接文档

> 生成日期：2026-05-15
> 上一个对话已完成：方案设计 + 缺陷修复 + 环境配置
> 项目根：`C:\Users\hexk\OneDrive\文档\New project 6`

---

## 一、项目定位

Super KAM（Knowledge-Augmented Memory）—— 为每个 Codex skill 配备专属 Obsidian 知识库（vault），实现领域知识的摄取、蒸馏、检索和维护。目标是打造一批高效利用 vault 的超级 skills。

---

## 二、架构全景

### 三层 AGENTS.md

```
~/.codex/AGENTS.md              ← 全局级（所有会话生效）
  ├── vault 目录结构规范（8 目录）
  ├── 分层命名规则
  ├── YAML 元数据 schema
  ├── 跨 vault 检索协议
  └── Obsidian CLI 降级方案

New project 6/AGENTS.md          ← 项目级（元信息 + 外部 vault 引用）

~/.codex/skills/*/AGENTS.md     ← Skill 级（可选，各 skill 特有规则）
```

### Vault 目录结构

```
vault/
├── raw/user/          # 用户导入的原始资料（不可变）
├── raw/agent/         # Agent 导入的原始资料（不可变）
├── raw/original/      # 原始文件备份（PDF/DOCX 等）
├── knowledge/         # 精化知识节点（Zettelkasten ID 命名）
├── templates/         # 方案模板（主题命名）
├── cases/             # 案例/参考（日期前缀）
├── journal/           # 操作日志（YYYY-MM-DD.md）
└── auto-update/       # 定时任务写入（保持原文件名）
```

### 命名规范

| 目录 | 格式 | 示例 |
|------|------|------|
| vault/raw/ | `YYYY-MM-DD-{slug}-{source}.md` | `2026-05-15-上海国资股权激励指导意见-agent.md` |
| vault/knowledge/ | `zk-{domain}-{id}-{title}.md` | `zk-ei-aa1-0-equity-incentive-framework.md` |
| vault/templates/ | `{purpose}-template.md` | `equity-incentive-proposal-template.md` |
| vault/cases/ | `YYYY-MM-DD-{company}-{topic}-{source}.md` | `2026-05-15-张江高科-股权激励-user.md` |
| vault/journal/ | `YYYY-MM-DD.md` | `2026-05-15.md` |

### YAML 元数据 Schema

```yaml
---
title: 文件标题
date: YYYY-MM-DD
source: user | agent | distilled
original_source: user | agent      # 蒸馏时保留原始来源
source_path: original/源文件.pdf    # 原始备份路径
domain: equity-incentive           # 所属领域
tags: [标签1, 标签2]
status: raw | distilled | verified | expired
imported_by: vault_ingest.py | bootstrap | manual
imported_at: YYYY-MM-DDTHH:MM:SS
---
```

---

## 三、已完成的文件和改动

### New project 6/ 目录（项目根）

| 文件 | 说明 |
|------|------|
| `AGENTS.md` | 项目级规则 |
| `README.md` | 项目说明 |
| `KAM-IMPLEMENTATION.md` | ⚠️ 待更新（从 project 4 复制来，skill 列表需更新） |
| `scripts/bootstrap_vault.py` | 创建 vault 8 目录 + ontology 注册 |
| `scripts/enhance_skillmd.py` | 向 SKILL.md 注入 vault 上下文 |
| `templates/skill-header.md` | vault 注入块模板（官方 obsidian 命令+降级） |

### 全局

| 文件 | 说明 |
|------|------|
| `~/.codex/AGENTS.md` | 全局 vault 协议（命名/schema/检索/蒸馏） |
| `~/.codex/memories/ontology/graph.jsonl` | ontology 图谱文件（可写入） |
| `markitdown 0.1.5` | 文件转换工具（已安装） |

### 环境状态

| 项目 | 状态 |
|------|------|
| Python 3.12 | ✅ |
| markitdown | ✅ pip 安装完成 |
| ontology 目录 | ✅ 可写入 |
| Obsidian CLI | ⏳ 需用户手动启用（设置→常规→启用命令行接口→注册PATH） |
| Obsidian 进程 | ⏳ 需打开 Obsidian |

---

## 四、设计决策摘要

| # | 决策 | 结论 |
|---|------|------|
| 1 | Skill vault 独立还是共享？ | 独立，每个 skill 有自己的 vault |
| 2 | Obsidian 还是纯 Markdown？ | 官方 Obsidian CLI + 文件系统降级 |
| 3 | 导入双通道如何分离？ | 目录 + 文件名 + YAML 三重标记 |
| 4 | 原文件如何处理？ | 备份到 raw/original/ |
| 5 | 命名规范？ | 按目录分层（raw 日期 / knowledge ZK ID / templates 主题） |
| 6 | 元数据？ | 统一 YAML schema（含 original_source 追踪） |
| 7 | 跨 vault 链接？ | ontology 注册 Vault 实体 + AGENTS.md 检索协议 |
| 8 | 公司 vault？ | 外挂（张江高科/database/），不拆入 skill vault |
| 9 | 蒸馏触发？ | 用户要求时执行 |

---

## 五、待办任务（按顺序）

### 第一优先级（下一个对话可以开始）

1. **实现 vault_ingest.py**（文件转化导入脚本）
   - 放在 `New project 6/scripts/vault_ingest.py`
   - 支持 PDF/DOCX/PPTX/XLSX/MD 输入
   - 输出到 vault/raw/user/ 或 vault/raw/agent/
   - 原文件归档到 vault/raw/original/
   - 添加 YAML frontmatter（新 schema）
   - 按 raw 层命名规范重命名
   - 命令行接口：`python vault_ingest.py <file> --vault <path> --source user|agent`

2. **创建 equity-incentive skill + vault**（第一个锚点）
   - 创建 `~/.codex/skills/equity-incentive/`
   - 编写 SKILL.md（含 vault 注入块）
   - `python bootstrap_vault.py` 建 vault 目录 + 注册 ontology
   - `python enhance_skillmd.py` 注入 vault 上下文

3. **从微信文件导入首批股权激励材料到 vault/raw/**
   - 微信文件位置：`C:\Users\hexk\OneDrive\文档\xwechat_files\...\msg\file\2026-05\`
   - 涉及：法规 PDF、方案 PPTX、测算 XLSX、案例 DOCX

### 第二优先级

4. 更新 `KAM-IMPLEMENTATION.md` 跟踪表
5. 启用 Obsidian CLI（你手动操作）
6. 注册张江高科 company vault 到 ontology

### 第三优先级

7. 跨 vault 检索的实际运行验证
8. 蒸馏 SOP 首次执行
9. 内容保鲜机制（scheduled-tasks）

---

## 六、已有数据源

### 张江高科 company vault（外部引用）

- 路径：`C:\Users\hexk\OneDrive\Desktop\张江高科\database\`
- 内容：165 个 .md + 254 个 .pdf
- 结构：`张江高科历年年报/` + `张江高科重大事项公告/`
- 注意：YAML 用旧 schema（convert_pdfs.py 格式），agent 读取时需兼容

### 股权激励待处理素材

微信文件中已收集的股权激励相关材料（主要在 `xwechat_files/.../msg/file/2026-05/`）：

- `上市公司股权激励100问-68页.pdf`
- `上市公司股权激励100问-排版 20250624更新.pdf`
- `《国有控股上市公司（境内）实施股权激励试行办法.pdf`
- `上海国资上市公司员工股权激励案例.docx`
- `上海国资上市公司股权激励市场反应统计.docx`
- `关于本市国有控股上市公司推进股权激励工作促进高质量发展的指导意见.pdf`
- `张江高科股权激励方案0427(1).pdf`
- `张江高科股权激励方案0428(1).pptx`
- `张江高科股权激励方案（简版）0408.docx`
- `股权激励核心问题(1).docx`
- `股权激励考核数据测算(1).xlsx`
- `中央企业控股上市公司实施股权激励工作指引.pdf`
- Obsidian Vault 已有：`股权激励研究/国企股权激励税务问题研究报告.md`（29KB）

---

## 七、常用命令速查

```bash
# 建 vault
python scripts/bootstrap_vault.py ~/.codex/skills/equity-incentive

# 增强 SKILL.md
python scripts/enhance_skillmd.py ~/.codex/skills/equity-incentive

# 文件转化（vault_ingest.py 实现后）
python scripts/vault_ingest.py 文件.pdf --vault ~/.codex/skills/equity-incentive/vault --source user

# 查看全局 AGENTS.md
Get-Content ~/.codex/AGENTS.md
```

---

> 新对话暗号：**"Super KAM 继续"**

## 2026-05-16 — SKILL.md 重复注入修复

### 问题
- equity-incentive/SKILL.md 被 enhance_skillmd.py 重复注入 4 次，文件膨胀到 4976 字节
- 重复内容导致模型在加载 SKILL.md 时产生空的 assistant message
- OpenAI API 返回 `Invalid assistant message: content or tool_calls must be set`，另一个对话卡死

### 修复
1. **SKILL.md 重建**: 从备份提取原始内容 + 按模板正确注入 vault 块，文件从 4976 → 2130 字节
2. **enhance_skillmd.py 去重增强**:
   - `is_enhanced()` 从单标记检查改为检查 4 个关键标记全部存在
   - 新增重复标记计数检测，>1 时发出警告
   - `find_vault_block()` 结束边界改为按 `## 配置需求` + 下一个 `##` 标题定位
   - `update()` 改为循环移除所有注入块（防止重复时只移除一个）
   - 新增 `_clean_blank_lines()` 卸载后清理多余空行

### 文件变更
- `~/.codex/skills/equity-incentive/SKILL.md` — 清理重建
- `scripts/enhance_skillmd.py` — 去重逻辑 v1.1

## 2026-05-16 — 交换 #4~#6: 002号KAM搭建 + 双KAM协作 + bb1扩充 + 案例导入

### 完成事项

#### 交换 #4: 002号KAM搭建 + 双KAM协作
- 评价002财税合规知识框架，设计双KAM协作架构（领域分工+JSON数据接口）
- bootstrap_vault.py 创建002 vault目录，enhance_skillmd.py 注入vault上下文
- 导入法规文件，升级001法规节点（227号令2025修正/治理准则18号/单独计税延至2027）
- 发现178号文40%规则（之前误用30%），修正公式
- 从张江高科2025年报获取董事长年薪127.23万元，重算股权激励收益
- 修复SKILL.md跨KAM协作协议，清理references，创建cases/templates

#### 交换 #5: 002号KAM bb1行业特殊税政扩充
- 差距分析后重新规划bb1（聚焦张江高科实际业务：园区运营+产业投资）
- 创建5个知识节点：不动产开发与租赁税务/产业投资税务/浦东新区政策/政府补助处理/国企重组税务
- 更新zk-categories.md，重建索引，validate 17/17通过

#### 交换 #6: 上海建科股权激励案例导入（新工作流）
- **建立公告获取工作流**：cninfo API搜索公告 + eastmoney API获取历史股价
- **案例导入工作流**：用户下载PDF→markitdown提取→创建案例→写入cases/→build_index+validate
- 处理20份上海建科PDF，创建完整案例（含6个关键节点实际股价+解锁期分析+合规检查）
- 创建Obsidian canvas时间线可视化（13节点+11连线）
- 案例从002搬至001 vault（因为本质是股权激励计划而非税务案例）

### 关键教训与纠正

| 发现 | 说明 |
|------|------|
| 178号文40%上限 | 之前误用171号文30%，实际为178号文第三十四条40% |
| 薪酬总水平=年薪x间隔期 | 第三十五条(十三)，非单年，一般2年 |
| bb1应聚焦实际业务 | 排除高新/研发加计等，改为园区+产业投资方向 |
| 案例放对vault | 股权激励案例放001，税务精算放002 |

### 环境新增

| 工具 | 用途 | 验证 |
|------|------|:----:|
| cninfo API | 按公司名搜索公告全文 | ✅ |
| eastmoney API | 获取A股历史日K线行情 | ✅ |
| markitdown | PDF转Markdown文本提取 | ✅ |

### vault最终状态

**001 equity-incentive:** knowledge 10 / cases 4 / templates 3 / raw/user 13 / validate 32/32
**002 tax-compliance:** knowledge 13 / cases 1 / templates 1 / validate 17/17


## 2026-05-17 — 批量案例蒸馏 + 对比报告生成

### 完成事项

#### 11家公司案例批量导入+蒸馏
- **赢合科技（300457.SZ）**: 81份PDF → 两轮完整生命周期案例（2017+2022）
- **上港集团（600018.SH）**: 42份PDF → 首批+第二批已完成案例
- **东方创业（600278.SH）**: 47份PDF → 首批已解锁案例
- **华谊集团（600623.SH）**: 42份PDF → 全生命周期案例（三期全部解锁）
- **国泰君安/国泰海通（601211.SH）**: 30份PDF → 证券公司+预留全部解锁案例
- **华建集团（600629.SH）**: 两轮计划案例（2018+2022）
- **锦江酒店（600754.SH）**: 2024计划案例
- **上海机场（600009.SH）**: 2024计划案例
- **申能股份（600642.SH）**: 首批被取消特色案例
- **外服控股（600662.SH）**: 首批第二批均解锁案例

#### 对比报告
- **11家公司横向对比报告**: `zk-ei-bb0-0-11-cases-comparison-report.md`
- 对比维度：激励方式、范围、解禁安排、业绩考核、市场反应、实际收益
- 已部署到 vault knowledge 目录

#### 数据修复流程
- 发现并修复多个 case 数据不一致问题（股价源、授予价、股票来源等）
- 创建 `_deploy_all.py` 一键部署脚本
- 多个 `_fix*.py` 数据修复辅助工具

### Vault 最终状态

**001 equity-incentive:** knowledge 15 / cases 14 / templates 3 / raw 313 / validate 337/337 ✅
**002 tax-compliance:** knowledge 14 / cases 1 / templates 1 / raw 3 / validate 17/17 ✅

### 新增脚本

| 脚本 | 用途 |
|------|------|
| `gen_bb0_comparison.py` | 案例对比报告生成器 |
| `update_cases.py` | 批量更新 case 数据 |
| `update_cases_missing_data.py` | 填充缺失数据 |
| `fetch_market_data.py` | eastmoney API 获取历史股价 |
| `fix_stock_source.py` | 股票来源一致性修复 |
| `_deploy_all.py` | 一键部署更新到 vault |

### 更新待办

| # | 任务 | 状态 |
|---|------|:----:|
| 1 | vault_ingest.py 实现 | ✅ 已完成 |
| 2 | Obsidian CLI 启用 | ⏳ 需用户手动 |
| 3 | 知识蒸馏（首次批量） | ✅ 14家案例全部蒸馏 |
| 4 | validate_vault.py | ✅ 337/337 |
| 5 | KAM-IMPLEMENTATION.md | ✅ 已更新 |
| 6 | health_check 误报优化 | ⏳ 低优先级 |


## 定时健康检查任务
| 项目 | 值 |
|------|-----|
| 任务名称 | KAM\VaultHealthCheck |
| 触发时间 | 每天 09:00 和 21:00 |
| 执行脚本 | auto_health.py |
| 日志输出 | logs/health_YYYY-MM-DD.md |
| 创建日期 | 2026-05-17 |
| 状态 | enabled |