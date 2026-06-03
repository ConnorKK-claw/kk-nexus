# KK Nexus — 多员工知识系统

> **KK Nexus** 是一个基于 Codex 的多员工（Multi-Agent）知识工作系统。
> 每个员工是一个独立的 AI skill，配备专属知识库（vault），
> 通过统一的工具链完成知识的导入、蒸馏、索引和检索。

---

## 快速开始

### 前置要求

- Python >= 3.10
- Git
- 磁盘空间 >= 3GB
- 内存 >= 8GB

### 安装

```powershell
git clone git@github.com:ConnorKK-claw/kk-nexus.git
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
第3层  员工层  — 5 个 skill 化员工（001~005）
第2层  知识库  — vault 体系（raw / knowledge / cases / templates）
第1层  工具链  — 36 个 Python 自动化脚本
```

### 5 员工体系

| 编号 | 名称 | Domain | 职责 |
|:---:|------|:------:|------|
| 001 | equity-incentive | ei | 股权激励方案设计与法规合规 |
| 002 | tax-compliance-expert | tax | 财税合规、发票、记账、审计 |
| 003 | weekly-report | wr | 周报生成（证券/公司） |
| 004 | hk-ipo | hk | 港股 IPO 全流程 |
| 005 | financial-analysis | fa | 宏观经济、货币政策、资产配置 |

每个员工 = 一个独立的 Codex skill，位于 `~/.codex/skills/<name>/`，包含：
- `SKILL.md` — 能力定义
- `SOUL.md` — 身份定义
- `TOOLS.md` — 工具清单
- `vault/` — 专属知识库

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
| 知识索引 | `python scripts/build_index.py <vault-path>` |
| 统一索引 | `python scripts/unified_index.py --refresh` |
| 健康检查 | `python scripts/weekly_vault_health.py` |

### 语义搜索

```powershell
# 搜索知识库
python scripts/txtai_query.py "关键词" --limit 5

# 启动 MCP 服务（供 Codex 直接调用）
python scripts/txtai_mcp.py
```

### 跨 vault 检索

检索优先级链（full-access 模式下）：
```
① txtai 语义搜索（向量 + RAG）
② UNIFIED_INDEX.md（O(1) 索引查询）
③ obsidian-cli --fuzzy（分词 + 拼音模糊）
④ vault/knowledge/index.md
⑤ Select-String 纯文本降级
```

---

## 在新 PC 上搭建

详细搭建说明书请阅读 **[KK-NEXUS-SKILL.md](./KK-NEXUS-SKILL.md)**，包含 10 个章节的完整指引。

快速流程：

```powershell
# 1. 克隆
git clone git@github.com:ConnorKK-claw/kk-nexus.git
cd kk-nexus

# 2. 安装依赖
pip install txtai sentence-transformers

# 3. 重建语义索引
python scripts/txtai_index.py --full

# 4. 刷新统一索引
python scripts/unified_index.py --refresh

# 5. 健康检查
python scripts/weekly_vault_health.py
python scripts/txtai_health.py
```

---

## 项目结构

```
kk-nexus/
├── AGENTS.md                     # 全局规则与协议
├── KK-NEXUS-SKILL.md             # 完整搭建说明书（kk-nexus skill）
├── KK_NEXUS_SETUP.md             # 安装指引（精简版）
├── ONBOARDING.md                 # 入职指南
├── HANDOVER.md                   # 交接文档
├── SOUL.md / TOOLS.md / USER.md  # 根配置
├── scripts/                      # 36 个自动化脚本
├── templates/                    # 模板（vault 骨架、SKILL 注入块等）
├── backup/                       # 备份（ontology.jsonl 等）
└── .gitignore
```

---

## 协议体系

KK Nexus 的核心运行协议定义在 `AGENTS.md` 中，包括：

- **WAL 协议** — 每次会话结束前必须执行的收尾流程
- **检索优先级协议** — 从语义搜索到纯文本降级的检索链
- **原始素材处理协议** — 导入到健康检查的 8 步全链路
- **标签规范** — 禁止 `未知` / `[object Object]` 等格式
- **文件命名规范** — vault/ 下各目录的命名规则

---

## 维护

### 定期任务

| 频率 | 任务 |
|:---:|------|
| 每周 | `python scripts/weekly_vault_health.py` |
| 每次变更 | `python scripts/unified_index.py --refresh` |
| 每次会话结束 | 执行 WAL 协议（SESSION-STATE + memory + working-buffer） |
| 按需 | `python scripts/txtai_index.py --full`（重建语义索引） |

### 回退

```powershell
git log --oneline          # 查看历史
git checkout <commit-hash> # 回退到某个快照
```

---

## 许可证

私有项目 © ConnorKK
