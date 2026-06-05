# KK Nexus - 多员工知识系统框架

> **KK Nexus** 是一个基于 Codex 的多员工(Multi-Agent)知识工作系统框架。
> 提供完整的工具链、协议体系和 vault 机制，
> 让你能为任何领域创建专属的 AI 员工。

## 当前员工体系（001~006）

| 编号 | 名称 | Domain | 职责 |
|:---:|------|:------:|------|
| 001 | equity-incentive | ei | 股权激励方案设计与法规合规 |
| 002 | tax-compliance-expert | tax | 财税合规、发票、记账、审计 |
| 003 | weekly-report | wr | 证券周报生成 |
| 004 | hk-ipo | hk | 港股 IPO 全流程 |
| 005 | financial-analysis | fa | 宏观经济、货币政策、资产配置 |
| 006 | serenity-a-share-investor | asi | A股AI半导体产业链投资研究 |

参考 `SUPER-KAM-EMPLOYEE-CREATION-SOP.md` 创建更多员工。
---

## 架构

```
第4层  集成层  — MCP / Obsidian / Ontology / txtai
第3层  员工层  — 独立的 skill 化员工（001~006），各配专属 vault
第2层  知识库  — vault 体系（raw / knowledge / cases / templates）
第1层  工具链  — 36 个 Python 自动化脚本
```

每个员工 = 一个独立的 Codex skill，位于 `~/.codex/skills/<name>/`：
- `SKILL.md` - 能力定义
- `SOUL.md` - 身份定义
- `TOOLS.md` - 工具清单
- `vault/` - 专属知识库

---

## 核心能力

### 知识处理全链路

```
导入 -> 验证 -> 语义索引 -> 蒸馏 -> 知识索引 -> 统一索引 -> 健康检查
```

| 步骤 | 命令 |
|------|------|
| 导入 | 手动放入 vault/raw/user/ 或运行 vault_ingest.py |
| 验证 | `python scripts/validate_vault.py <vault-path>` |
| 语义索引 | `python scripts/txtai_index.py --full` |
| 蒸馏 | 按 domain 独立设计（参考 distill_fa.py）|
| 知识索引 | `python scripts/build_index.py <vault-path>` |
| 统一索引 | `python scripts/unified_index.py --refresh` |
| 健康检查 | `python scripts/weekly_vault_health.py` |

### 语义搜索

```powershell
python scripts/txtai_query.py "<query>" --limit 5
python scripts/txtai_mcp.py   # 启动 MCP 服务
```

---

## 快速开始

### 前置要求

- Python >= 3.10
- Git
- 磁盘空间 >= 3GB
- 内存 >= 8GB

### 安装

```powershell
git clone https://github.com/ConnorKK-claw/kk-nexus.git
cd kk-nexus
pip install txtai sentence-transformers
```

---

## 项目结构

```
kk-nexus/
  AGENTS.md                     # 全局规则与协议
  KK-NEXUS-SKILL.md             # 完整搭建说明书（agent 直接读）
  docs/                         # 各员工部署 SOP
    super-kam-001-setup-summary.md
    super-kam-006-serenity-a-share-investor.md
  scripts/                      # 36 个自动化脚本
  templates/                    # vault 骨架 + skill 模板
```

---

## 许可证

MIT
