# KK Nexus — 多员工知识系统搭建与审计 Skill

> **版本**: 1.0
> **用途**: 从零搭建完整的 KK Nexus 多员工知识系统，或审计现有安装的完整性
> **触发词**: "build KK nexus", "搭建 KK nexus", "审计 KK nexus"

---

## 1. 架构总览

KK Nexus 是一个基于 Codex 的**多员工知识系统**，采用四层架构：

`
第4层  集成层  — MCP / Obsidian / Ontology / txtai
第3层  员工层  — 独立 skill 化员工，各配专属 vault
第2层  知识库  — vault 体系（raw / knowledge / cases / templates）
第1层  工具链  — Python 自动化脚本
`

### 核心设计原则

- **Don't tell it what to do. Give it success criteria and watch it go.**
- 每员工 = 一个 Codex skill，有独立 vault
- 知识统一语义索引（txtai），跨 vault 检索
- 自优化：memory/ + consolidate_learnings + WAL 协议
- 自审计：每周健康检查 + 编码/BOM 检查 + 索引验证

### 员工自然语言路由协议

为使 KKnexus 能直接响应口语化指令，各员工 skill 需在目录下提供 KKNEXUS-REGISTRY.json。Supervisor（或当前会话中的总调度器）按以下协议路由：

1. **触发词匹配**：当用户输入包含某员工的 	rigger_words 时，定位到对应 skill 目录
2. **读取注册表**：加载 <skill_path>/KKNEXUS-REGISTRY.json，获取 employee_id、skill_path、intents
3. **意图匹配**：按 intents[].patterns 顺序用正则匹配用户输入；若命中，提取命名捕获组，填充到 command 模板
4. **执行**：在 skill 目录下执行填充后的命令；supervisor 只负责路由，不替员工完成具体任务
5. **回退**：若未命中任何意图，加载并显示该员工的 SKILL.md 自然语言命令映射，由用户确认后执行

> 注：本协议为路由契约。完整的 supervisor 实现可在后续迭代中基于该协议开发；当前各 skill 仍可独立加载并按 SKILL.md 中的自然语言映射运行。

---

## 2. 前置环境检查清单

### 2.1 Python 环境

`powershell
python --version
# 要求: >= 3.10
`

pip 依赖（按需安装）：
`powershell
pip install txtai sentence-transformers
`

### 2.2 磁盘空间

`powershell
# 要求: >= 3GB 剩余空间
`

### 2.3 内存

`powershell
# 要求: >= 8GB
`

### 2.4 Git

`powershell
git --version
# 要求: 有输出即可
`

---

## 3. 创建新员工 Skill

### 3.1 使用 CLI 创建

`powershell
python scripts/enhance_skillmd.py --skill-dir <skill-path> --domain <domain>
`

### 3.2 使用模板创建

从 	emplates/vault-skeleton/ 复制 vault 骨架，编写 SKILL.md 并注入 vault 配置块。

### 3.3 新员工注册

在员工目录下创建 KKNEXUS-REGISTRY.json：

`json
{
  "employee_id": "XXX",
  "skill_path": "~/.codex/skills/<your-skill>",
  "description": "员工职责描述",
  "trigger_words": ["XXX", "触发词1", "触发词2"],
  "intents": [
    {
      "name": "intent_name",
      "patterns": ["正则表达式1", "正则表达式2"],
      "command": "python scripts/command.py {captured_group}"
    }
  ]
}
`

---

## 4. 初始化 Vault

`powershell
# 初始化 vault 骨架
python scripts/bootstrap_vault.py --vault <vault-path> --domain <domain>

# 导入原始素材
python scripts/vault_ingest.py --input <file> --vault <vault-path> --source user

# 验证 vault 结构
python scripts/validate_vault.py <vault-path>

# 建立语义索引
python scripts/txtai_index.py --full

# 建立知识索引
python scripts/build_index.py <vault-path>

# 建立作者索引
python scripts/build_authors_index.py <vault-path>

# 刷新统一索引
python scripts/unified_index.py --refresh
`

---

## 5. 自优化机制

### 5.1 记忆系统

- 每次会话的决策和教训写入 ault/memory/YYYY-MM-DD.md
- 格式：## 关键决策 + ## 教训 + ## 待办

### 5.2 学习汇聚

运行以下命令将 .learnings/ 下的分散记录汇聚到 MEMORY.md：
`powershell
python scripts/consolidate_learnings.py
`

### 5.3 工作缓冲

当上下文使用超过 60% 时，将当前状态追加到 working-buffer.md：
`
## 当前任务
## 已完成
## 上下文
## 待办
`

### 5.4 心跳监控

配置定时任务运行 uto_heartbeat.py：
`powershell
python scripts/auto_heartbeat.py
`

---

## 6. 自审计机制

### 6.1 每周健康检查

运行 python scripts/health_check.py --mode weekly，检查项包括：
- raw/ 下过期未蒸馏文件
- knowledge/ 下可能过期的节点
- 标签重复/冲突
- 文件编码完整性（BOM 检测）

### 6.2 索引完整性验证

`powershell
# 验证 txtai 索引
python scripts/txtai_health.py

# 验证统一索引
python scripts/unified_index.py --refresh
`

### 6.3 过期知识标记

定期检查 knowledge/ 中节点是否过期：
- 超过 2 年未更新的法规节点 → 标记 status: expired
- 已失效的案例 → 标记 status: archived 或移入 cases/

---

## 7. 集成配置

### 7.1 Obsidian CLI

如果安装了 obsidian-cli：
`powershell
obsidian-cli search --vault <vault-path> --query "关键词"
`

### 7.2 txtai MCP

提供 MCP 服务，允许 Codex agent 通过 MCP 协议直接调用语义搜索：
`powershell
python scripts/txtai_mcp.py
`

### 7.3 Ontology 知识图谱恢复

`powershell
# 从备份恢复
Copy-Item backup\ontology.jsonl "$env:USERPROFILE\.codex\memories\ontology\graph.jsonl"
`

### 7.4 统一索引刷新

任何时候 vault 有变更，都需要刷新：
`powershell
python scripts/unified_index.py --refresh
`

---

## 8. 故障排除

### 8.1 txtai 索引问题

症状：语义搜索无返回结果
解决：
`powershell
python scripts/txtai_index.py --full
# 首次需要下载模型（约 30MB）
`

### 8.2 LLM DLL 错误（torch_python.dll）

症状：OSError: [WinError 126] The specified module could not be found
原因：Windows 沙箱环境限制了 C 扩展 DLL 加载
解决：在 full-access 模式下运行，或跳过 embeddings_load 检查项

### 8.3 编码问题

症状：文件开头有 \uFEFF（BOM）
解决：
`powershell
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
`

### 8.4 回退到上一次快照

`powershell
git log --oneline
git checkout <commit-hash>
`

---

## 附录：项目路径速查

| 项目 | 路径 |
|------|------|
| 项目根目录 | <project-root> |
| 脚本目录 | <project-root>/scripts/ |
| 模板目录 | <project-root>/templates/ |
| txtai 索引 | ~/.txtai_index/ |
| Codex skills | ~/.codex/skills/ |
| Codex 本体 | ~/.codex/memories/ontology/graph.jsonl |

---

*KK Nexus v1.0 — 架构固化于 2026-01-01*


## 9. 新增强化模块（v1.1+）

### 9.1 语义检索增强
- **二阶段重排**：bge-reranker-base 交叉编码器，召回 top-N → rerank → top-5
- **混合检索**：txtai hybrid 模式，BM25 关键词 + 向量双路融合
- **父子分块**：按 `##` 标题切分，max_chunk=800, overlap=100

### 9.2 文档解析
- **docling 优先**：对 PDF/DOCX 的表格、版式、公式解析更优
- **markitdown 降级**：docling 不可用时自动降级

### 9.3 可观测性
- **OTel JSONL**：零 Langfuse 依赖，trace 写入本地 JSONL 文件
- **统一 LLM client**：收口所有 LLM 调用，统一限流 + OTel trace

### 9.4 通知
- **Webhook 派发**：HMAC-SHA256 签名，支持飞书等渠道
- **事件点**：蒸馏完成/失败/步骤失败等 6 处触发点

### 9.5 健康检查增强
- **--json 参数**：结构化输出供 dashboard 消费
- **退出码分离**：CLI 退出码反映工具执行状态，JSON payload 表达健康状态
- **asyncio 并发**：多 vault 并发检查替代串行调用

