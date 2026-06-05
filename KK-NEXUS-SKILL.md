# KK Nexus — 架构搭建与审计 Skill

> **版本**: 1.0
> **用途**: 在新 PC 上从零搭建完整的 KK Nexus 知识系统，或审计现有安装的完整性
> **触发词**: "build KK nexus", "搭建 KK nexus", "审计 KK nexus"

---

## 1. 架构总览

KK Nexus 是一个基于 Codex 的**多员工知识系统**，采用四层架构：

```
第4层  集成层  — MCP / Obsidian / Ontology / txtai
第3层  员工层  — 6 个 skill 化员工（001~006）
第2层  知识库  — vault 体系（raw / knowledge / cases / templates）
第1层  工具链  — 36 个 Python 自动化脚本
```

### 核心设计原则

- **Don\'t tell it what to do. Give it success criteria and watch it go.**
- 每员工 = 一个 Codex skill，有独立 vault
- 知识统一语义索引（txtai），跨 vault 检索
- 自优化：memory/ + consolidate_learnings + WAL 协议
- 自审计：每周健康检查 + 编码/BOM 检查 + 索引验证

### 6 员工体系

| 编号 | 名称 | domain | vault 路径 |
|:---:|------|--------|-----------|
| 001 | equity-incentive | ei | ~/.codex/skills/equity-incentive/vault/ |
| 002 | tax-compliance-expert | tax | ~/.codex/skills/tax-compliance-expert/vault/ |
| 003 | weekly-report | wr | ~/.codex/skills/weekly-report/vault/ |
| 004 | hk-ipo | hk | ~/.codex/skills/hk-ipo/vault/ |
| 005 | financial-analysis | fa | ~/.codex/skills/financial-analysis/vault/ |
| 006 | serenity-a-share-investor | asi | ~/.codex/skills/serenity-a-share-investor/vault/ |

---

## 2. 前置环境检查清单

### 2.1 Python 环境

```powershell
python --version
# 要求: >= 3.10
```

pip 依赖（按需安装）：
```powershell
pip install txtai sentence-transformers
```

### 2.2 磁盘空间

```powershell
Get-PSDrive C | Select-Object Free
# 要求: >= 3GB 剩余空间
```

### 2.3 内存

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
# 要求: >= 8GB
```

### 2.4 Git

```powershell
git --version
# 要求: 有输出即可
```

### 2.5 网络

```powershell
ping -n 1 github.com
```

---

## 3. 项目初始化

### 3.1 克隆项目

```powershell
git clone https://github.com/你的用户名/kk-nexus.git C:\path\to\kk-nexus
cd C:\path\to\kk-nexus
```

### 3.2 安装 Python 依赖

```powershell
pip install txtai
pip install sentence-transformers
```

> Embedding 模型 `BAAI/bge-small-zh-v1.5`（512维，30MB）会在首次运行 `txtai_index.py --full` 时自动下载。

### 3.3 可选：安装 obsidian-cli

参考 [obsidian-cli](https://github.com/obsidian-community/obsidian-cli) 官方文档安装。

---

## 4. Vault 体系搭建

### 4.1 创建 vault 骨架

每个员工都需要一个 vault 目录。使用项目中的模板：

```powershell
# 为一个新员工创建 vault
$SKILL_NAME = "my-new-skill"
$VAULT_PATH = "$env:USERPROFILE\.codex\skills\$SKILL_NAME\vault"

# 复制骨架
Copy-Item -Recurse templates\vault-skeleton\ $VAULT_PATH
```

### 4.2 vault 标准结构

```
vault/
├── raw/user/          # 用户导入的原始资料（不可变）
├── raw/agent/         # Agent 导入的原始资料（不可变）
├── raw/original/      # 原始文件备份（PDF/DOCX 等）
├── knowledge/         # 精化知识节点（Zettelkasten ID）
├── knowledge/zk-categories.md  # 分类码映射表
├── templates/         # 方案模板
├── cases/             # 案例/参考
├── journal/           # 操作日志
├── auto-update/       # 定时任务写入
└── memory/            # 会话记忆
```

### 4.3 验证 vault 完整性

```powershell
python scripts/validate_vault.py <vault-path>
```

---

## 5. 员工创建 SOP

### 5.1 创建 skill 目录

```powershell
mkdir -Force "$env:USERPROFILE\.codex\skills\<skill-name>\vault"
```

### 5.2 创建 SKILL.md

每个员工 skill 的 `SKILL.md` 必须包含以下 vault 注入块：

```markdown
---
## Vault 知识库

### 目录结构

vault/ 遵循 Super KAM 标准结构（见 AGENTS.md）

### 检索优先级

1. txtai 语义检索（最优先）
2. UNIFIED_INDEX.md
3. obsidian-cli --fuzzy
4. vault/knowledge/index.md
5. Select-String

### 知识蒸馏流程

raw/ → knowledge/ 的标准流程：
1. 摄取：vault_ingest.py 转为 MD → vault/raw/
2. 蒸馏：提取关键概念 → knowledge/
3. 案例提取 → cases/
4. 运行 build_index.py 重建 knowledge/index.md
5. 标记 raw 文件 status: distilled
```

### 5.3 创建 SOUL.md

每个员工必须有 `SOUL.md`，定义其身份和边界：

```markdown
# SOUL — {员工名}

## 身份
{一句话定义}

## 专长
- {能力列表}

## 边界
- {不做的事}
```

### 5.4 创建 TOOLS.md

```markdown
# TOOLS — {员工名}

## 数据来源
- vault/raw/ — 原始资料
- vault/knowledge/ — 精化知识
- vault/cases/ — 案例

## 外部工具
- obsidian-cli — 模糊搜索
- txtai — 语义搜索
```

### 5.5 启动序列

每次会话开始按以下顺序加载：

```
1. SOUL.md — 身份认同
2. TOOLS.md — 可用工具
3. vault/knowledge/index.md — 知识索引
4. SESSION-STATE.md — 当前任务状态
```

---

## 6. 协议体系

### 6.1 WAL 协议

**每次会话结束前必须执行：**

1. 更新 `SESSION-STATE.md`（"本轮完成" + "剩余工作队列"）
2. 写入 `memory/YYYY-MM-DD.md`（关键决策 + 教训）
3. 如果上下文 > 60%，追加到 `working-buffer.md`
4. 运行 `python scripts/unified_index.py --refresh`（如果 vault 有变更）
5. 运行 `python scripts/consolidate_learnings.py`（汇聚 .learnings/ 到 MEMORY.md）

### 6.2 检索优先级协议

**full-access 模式（优先语义搜索）：**

```
① txtai 语义检索（向量搜索 + RAG 合成）
② UNIFIED_INDEX.md（O(1) 索引查询）
③ obsidian-cli "关键词" --fuzzy（分词 + TF-IDF + 拼音模糊）
④ vault/knowledge/index.md（精准知识索引）
⑤ Select-String -Path <vault> -Pattern "关键词" -Recurse（纯文本降级）
```

### 6.3 原始素材处理协议

任何新文件导入 vault 后必须完成以下全部环节：

```
导入 -> 验证 -> 语义索引(txtai) -> [领域蒸馏] -> 知识索引 -> 作者索引 -> 统一索引 -> 健康检查
```

| 环节 | 脚本 |
|------|------|
| 导入 | 手动或 vault_ingest.py |
| 验证 | python scripts/validate_vault.py <vault-path> |
| 语义索引 | python scripts/txtai_index.py --full |
| 蒸馏 | 每个 vault 独立设计（distill_fa.py / auto_distill_vault.py） |
| 知识索引 | python scripts/build_index.py <vault-path> |
| 作者索引 | python scripts/build_authors_index.py <vault-path> |
| 统一索引 | python scripts/unified_index.py --refresh |
| 健康检查 | python scripts/weekly_vault_health.py |

**失败回退：** 任何一步失败时中止后续步骤，修复问题后从头运行全流程，不允许跳过。

**全流程快捷命令：**
```powershell
python scripts/validate_vault.py .\vault
python scripts/txtai_index.py --full
python scripts/auto_distill_vault.py .\vault
python scripts/build_index.py .\vault
python scripts/build_authors_index.py .\vault
python scripts/unified_index.py --refresh
python scripts/weekly_vault_health.py
```

### 6.4 标签规范

- 禁止 `未知` 标签（作者未知则不标注）
- 禁止 `[object Object]` 格式的标签
- 知名国际机构来源需加上机构名称为标签
- 标签格式示例：`tags: [股权激励, 国资, 科创板]`
- 空标签 `tags: []` 可省略整个 tags 字段

### 6.5 文件命名规范

| 目录 | 命名格式 | 示例 |
|------|---------|------|
| vault/raw/ | `YYYY-MM-DD-{slug}-{source}.md` | `2026-05-15-上海国资股权激励-agent.md` |
| vault/knowledge/ | `zk-{domain}-{catseq}-{docseq}-{title}.md` | `zk-ei-aa0-0-equity-incentive-regulation.md` |
| vault/cases/ | `YYYY-MM-DD-{company}-{topic}-{source}.md` | `2026-05-15-张江高科-股权激励-user.md` |
| vault/journal/ | `YYYY-MM-DD.md` | `2026-05-15.md` |

---

## 7. 自优化机制

### 7.1 记忆系统

- 每次会话的决策和教训写入 `vault/memory/YYYY-MM-DD.md`
- 格式：`## 关键决策` + `## 教训` + `## 待办`

### 7.2 学习汇聚

运行以下命令将 `.learnings/` 下的分散记录汇聚到 `MEMORY.md`：

```powershell
python scripts/consolidate_learnings.py
```

### 7.3 工作缓冲区

当上下文使用超过 60% 时，将当前状态追加到 `working-buffer.md`：

```
## 当前任务
## 已完成
## 上下文
## 待办
```

### 7.4 心跳监控

配置定时任务运行 `auto_heartbeat.py`：

```powershell
python scripts/auto_heartbeat.py
```

---

## 8. 自审计机制

### 8.1 每周健康检查

```powershell
python scripts/weekly_vault_health.py
```

检查项：
- ✅ 所有文件 UTF-8 编码（无 BOM）
- ✅ 无双重 BOM 文件
- ✅ 无重复 URL（raw/ 中）
- ✅ YAML frontmatter 完整性
- ✅ 文件命名合规

### 8.2 索引完整性验证

```powershell
# 验证 txtai 索引
python scripts/txtai_health.py

# 验证统一索引
python scripts/unified_index.py --refresh
```

### 8.3 过期知识标记

定期检查 knowledge/ 中节点是否过期：

- 超过 2 年未更新的法规节点 → 标记 `status: expired`
- 已失效的案例 → 标记 `status: archived` 或移入 `cases/`

---

## 9. 集成配置

### 9.1 Obsidian CLI

如果在目标机器上安装了 obsidian-cli：

```powershell
obsidian-cli search --vault <vault-path> --query "关键词"
```

### 9.2 txtai MCP

kk-nexus 项目中的 `scripts/txtai_mcp.py` 提供 MCP 服务：

```powershell
python scripts/txtai_mcp.py
```

该服务允许 Codex agent 通过 MCP 协议直接调用语义搜索。

### 9.3 Ontology 知识图谱恢复

```powershell
# 从备份恢复
Copy-Item backup\ontology.jsonl "$env:USERPROFILE\.codex\memories\ontology\graph.jsonl"
```

### 9.4 统一索引刷新

任何时候 vault 有变更，都需要刷新：

```powershell
python scripts/unified_index.py --refresh
```

---

## 10. 故障排除

### 10.1 txtai 索引问题

症状：语义搜索无返回结果
解决：
```powershell
python scripts/txtai_index.py --full
# 首次需要下载模型（约 30MB）
```

### 10.2 LLM DLL 错误（torch_python.dll）

症状：`OSError: [WinError 126] The specified module could not be found`
原因：Windows 沙箱环境限制了 C 扩展 DLL 加载
解决：在 full-access 模式下运行，或跳过 embeddings_load 检查项

### 10.3 编码问题

症状：文件开头有 `\uFEFF`（BOM）
解决：
```powershell
python -c "
import os
for root, dirs, files in os.walk(r'vault'):
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8-sig') as fh:
                c = fh.read()
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(c)
"
```

### 10.4 回退到上一次快照

```powershell
git log --oneline          # 查看提交历史
git checkout <commit-hash>  # 回退到指定版本
```

---

## 附录：项目路径速查

| 项目 | 路径 |
|------|------|
| 项目根目录 | C:\path\to\kk-nexus |
| 脚本目录 | C:\path\to\kk-nexus\scripts\ |
| 模板目录 | C:\path\to\kk-nexus\templates\ |
| 本体备份 | C:\path\to\kk-nexus\backup\ontology.jsonl |
| txtai 索引 | C:\Users\<user>\.txtai_index\ |
| Codex skills | C:\Users\<user>\.codex\skills\ |
| Codex 本体 | C:\Users\<user>\.codex\memories\ontology\graph.jsonl |

---

*KK Nexus v1.0 — 架构固化于 2026-06-03*
