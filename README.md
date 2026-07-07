# KK Nexus — 多员工知识系统框架

> **构建你自己的多员工-多知识库 AI 知识操作系统**

KK Nexus 是一个基于 [Codex](https://github.com/openai/codex-cli) 的框架，让你能**构建自己的"AI 员工团队"**——每个员工是一个专业化的 Codex skill，配备独立的知识库（vault），通过语义搜索统一索引，实现持续学习与自我进化。

---

## 设计哲学

`
Don't tell it what to do. Give it success criteria and watch it go.
                                                    —Andrej Karpathy
`

- **员工 = Skill**：每个员工是一个独立的 Codex skill，拥有专属领域和 vault
- **知识 = Vault**：结构化的知识库体系（raw → knowledge → cases → templates）
- **索引 = txtai**：跨 vault 统一语义搜索，离线、轻量
- **进化 = WAL**：Write-Ahead Logging 协议，每次会话的决策和教训被持久化
- **自治 = Health Check**：每周健康检查 + 自修复机制

---

## 核心架构

`
┌─────────────────────────────────────────────────────┐
│              第4层  集成层                          │
│    MCP / Obsidian / Ontology / txtai 语义搜索        │
├─────────────────────────────────────────────────────┤
│              第3层  员工层                          │
│    独立的 Skill 化员工，各配专属 Vault              │
│    ┌──────┐ ┌──────┐ ┌──────┐     ┌──────┐        │
│    │员工01│ │员工02│ │员工03│ ... │员工N │        │
│    └──────┘ └──────┘ └──────┘     └──────┘        │
├─────────────────────────────────────────────────────┤
│              第2层  知识库                          │
│    vault/raw → vault/knowledge → vault/cases        │
│    Zettelkasten 节点 + YAML 元数据 + 来源引用       │
├─────────────────────────────────────────────────────┤
│              第1层  工具链                          │
│    Python 自动化脚本：摄取/蒸馏/索引/健康检查/WAL   │
└─────────────────────────────────────────────────────┘
`

---

## 快速开始

### 前置要求

- Python >= 3.10
- Git
- 磁盘 >= 3GB
- 内存 >= 8GB

### 安装

`powershell
git clone https://github.com/<your-org>/kk-nexus.git
cd kk-nexus
pip install txtai sentence-transformers
`

### 创建你的第一个员工

`powershell
# 1. 创建 vault 骨架
python scripts/bootstrap_vault.py --vault ~/my-skill/vault --domain my-domain

# 2. 编写 SKILL.md（定义员工能力）
# 3. 导入知识素材
python scripts/vault_ingest.py --input my-knowledge.md --vault ~/my-skill/vault --source user

# 4. 建立语义索引
python scripts/txtai_index.py --full

# 5. 建立知识索引
python scripts/build_index.py ~/my-skill/vault

# 6. 注册员工路由
# 创建 KKNEXUS-REGISTRY.json（详见 KK-NEXUS-SKILL.md）
`

---

## 项目结构

`
kk-nexus/
├── AGENTS.md                    # 全局规则与协议（本文件即系统宪法）
├── KK-NEXUS-SKILL.md            # 完整搭建说明书（agent 可直接读取执行）
├── README.md                    # 本文件
├── LICENSE                      # MIT
├── requirements.txt             # Python 依赖
├── .gitignore
├── templates/                   # 通用模板
│   ├── skill-header.md          # SKILL.md 头部模板
│   ├── skill-header-shared.md   # 共享 header 模板
│   └── vault-skeleton/          # Vault 骨架（可直接复制使用）
│       ├── raw/user/
│       ├── raw/agent/
│       ├── raw/original/
│       ├── knowledge/
│       ├── cases/
│       ├── journals/
│       ├── templates/
│       ├── auto-update/
│       └── memory/
└── scripts/                     # 通用 Python 脚本
    ├── txtai_index.py           # 语义索引构建
    ├── txtai_query.py           # 语义查询
    ├── txtai_mcp.py             # MCP 服务
    ├── txtai_health.py          # 索引健康检查
    ├── txtai_utils.py           # 索引工具
    ├── unified_index.py         # 统一索引管理
    ├── build_index.py           # knowledge/index.md 构建
    ├── build_authors_index.py   # 作者索引构建
    ├── validate_vault.py        # Vault 结构验证
    ├── vault_ingest.py          # 文件导入
    ├── vault_search.py          # Vault 搜索
    ├── health_check.py          # 每周健康检查
    ├── consolidate_learnings.py # 学习汇聚
    ├── auto_distill_vault.py    # 自动知识蒸馏
    ├── bootstrap_vault.py       # Vault 初始化
    ├── domain_classifier.py     # 领域分类
    ├── enhance_skillmd.py       # SKILL.md 增强
    ├── v2-session_harvester.py  # 会话自动收割
    ├── kam.py                   # KAM 核心
    └── ...                      # 更多通用脚本
`

---

## 核心能力

### 知识处理全链路

`
导入 → 验证 → 语义索引 → 蒸馏 → 知识索引 → 作者索引 → 统一索引 → 健康检查
`

每一个环节都有对应脚本，失败会中止并提示修复，不允许跳过。

### 多级检索策略

1. **txtai 语义搜索**（向量搜索 + RAG 合成，离线运行）
2. **UNIFIED_INDEX**（O(1) 索引查找）
3. **Obsidian CLI**（分词 + 拼音模糊匹配）
4. **knowledge/index.md**（精准知识索引）
5. **ripgrep 纯文本降级**

### 自我进化机制

- **WAL 协议**：每次会话结束前持久化决策和教训
- **学习汇聚**：.learnings/ → MEMORY.md 持续累积
- **工作缓冲**：上下文 > 60% 时自动暂存状态
- **健康检查**：每周自动检测过期/矛盾知识
- **会话收割**：PostToolUse 钩子自动提取关键信息

### 来源引用协议

每个回答中的判断必须标注来源（vault 知识节点/案例/联网搜索/自行推测），确保可追溯。

---

## 创建你自己的员工团队

参考 KK-NEXUS-SKILL.md 中的员工注册协议，你可以为任意领域创建专属 AI 员工：

1. 定义员工能力（SKILL.md）
2. 初始化 vault 骨架
3. 导入领域素材
4. 编写蒸馏策略（按 domain 独立设计）
5. 注册自然语言路由（KKNEXUS-REGISTRY.json）
6. 建立语义索引
7. 持续通过 WAL 协议喂养知识

---

## 许可证

MIT License — 自由使用、修改、分享。

---

*用 KK Nexus 搭建你自己的 AI 员工军团。*
