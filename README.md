# KK Nexus — 多员工知识系统框架

> **KK Nexus** 是一个基于 Codex 的多员工（Multi-Agent）知识工作系统框架。  
> 提供完整的工具链、协议体系和 vault 机制，  
> 让你能为任何领域创建专属的 AI 员工。

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

> Embedding 模型 `BAAI/bge-small-zh-v1.5`（512维，30MB）会在首次语义索引时自动下载。

### 验证安装

```powershell
python scripts/txtai_health.py
```

---

## 架构

```
第4层  集成层  — MCP / Obsidian / Ontology / txtai
第3层  员工层  — 独立的 skill 化员工，各配专属 vault
第2层  知识库  — vault 体系（raw / knowledge / cases / templates）
第1层  工具链  — 28 个 Python 自动化脚本
```

### 员工体系（参考示例）

本框架不提供具体员工的知识内容，但提供创建 5 类员工的 SOP：

| 角色 | Domain | 典型职责 |
|:----|:------:|---------|
| 股权激励专家 | ei | 方案设计、法规合规、案例对标 |
| 财税合规专家 | tax | 财税合规、发票、记账、审计 |
| 周报助手 | wr | 定期报告生成 |
| 港股 IPO 专家 | hk | IPO 全流程 |
| 宏观分析师 | fa | 宏观经济、货币政策、资产配置 |

每个员工 = 一个独立的 Codex skill，位于 `~/.codex/skills/<name>/`：
- `SKILL.md` — 能力定义
- `SOUL.md` — 身份定义
- `TOOLS.md` — 工具清单
- `vault/` — 专属知识库

参考 `SUPER-KAM-EMPLOYEE-CREATION-SOP.md` 创建你自己的员工。

---

## 核心能力

### 知识处理全链路

```
导入 -> 验证 -> 语义索引 -> 蒸馏 -> 知识索引 -> 作者索引 -> 统一索引 -> 健康检查
```

| 步骤 | 命令 |
|------|------|
| 导入 | 手动放入 vault/raw/user/ 或运行 vault_ingest.py |
| 验证 | `python scripts/validate_vault.py <vault-path>` |
| 语义索引 | `python scripts/txtai_index.py --full` |
| 蒸馏 | 按 domain 独立设计（参考 distill_fa.py） |
| 知识索引 | `python scripts/build_index.py <vault-path>` |
| 统一索引 | `python scripts/unified_index.py --refresh` |
| 健康检查 | `python scripts/weekly_vault_health.py` |

### 语义搜索

```powershell
python scripts/txtai_query.py "关键词" --limit 5
python scripts/txtai_mcp.py   # 启动 MCP 服务
```

### 跨 vault 检索优先级

```
① txtai 语义搜索（向量 + RAG）
② UNIFIED_INDEX.md（O(1) 索引查询）
③ obsidian-cli --fuzzy
④ vault/knowledge/index.md
⑤ Select-String 纯文本降级
```

---

## 在新 PC 上搭建

详细搭建说明书请阅读 **[KK-NEXUS-SKILL.md](./KK-NEXUS-SKILL.md)**（10 章完整版）。

快速流程：

```powershell
git clone https://github.com/ConnorKK-claw/kk-nexus.git
cd kk-nexus
pip install txtai sentence-transformers
python scripts/txtai_index.py --full
python scripts/unified_index.py --refresh
python scripts/weekly_vault_health.py
```

然后将 `KK-NEXUS-SKILL.md` 复制到 `~/.codex/skills/kk-nexus/SKILL.md`，
以后 agent 会自动读取这份搭建说明书。

---

## 项目结构

```
kk-nexus/
├── AGENTS.md                     # 全局规则与协议（WAL/检索/素材处理）
├── KK-NEXUS-SKILL.md             # 完整搭建说明书（agent 直接读）
├── SOUL.md / TOOLS.md            # 核心配置模板
├── ONBOARDING.md                 # 入职指南
├── SUPER-KAM-EMPLOYEE-CREATION-SOP.md  # 创建员工的 SOP
├── scripts/                      # 28 个自动化脚本
│   ├── txtai_*.py                # 语义索引引擎
│   ├── build_index.py            # 知识索引
│   ├── unified_index.py          # 统一索引
│   ├── validate_vault.py         # vault 校验
│   ├── vault_ingest.py           # 导入管道
│   ├── distill_fa.py             # 蒸馏示例（公众号文章）
│   └── ...
├── templates/                    # vault 骨架 + skill 模板
└── .gitignore
```

---

## 协议体系

定义在 `AGENTS.md` 中：

- **WAL 协议** — 每次会话结束前必须执行的收尾流程
- **检索优先级协议** — 从语义搜索到纯文本降级的检索链
- **原始素材处理协议** — 导入到健康检查的 8 步全链路
- **标签规范** — 禁止 `未知` / `[object Object]` 等格式
- **文件命名规范** — vault/ 下各目录的命名规则

---

## 维护

| 频率 | 任务 |
|:---:|------|
| 每周 | `python scripts/weekly_vault_health.py` |
| 每次变更 | `python scripts/unified_index.py --refresh` |
| 每次会话结束 | 执行 WAL 协议 |
| 按需 | `python scripts/txtai_index.py --full`（重建语义索引） |

---

## 许可证

MIT
