# KK Nexus — txtai 层改造方案

> 状态：计划阶段 | 版本：v1.0 | 日期：2026-06-01
> 目的：将 KK Nexus Layer 2 从 gbrain 替换为 txtai，解决 Windows Defender EPERM 问题，融入已有 Python 生态

---

## 1. 改造总览

### 1.1 为什么替换 gbrain

| 问题 | gbrain | txtai |
|------|--------|-------|
| Windows EPERM | ✅ bun 被 Defender 拦截 | ✅ Python 原生，零兼容问题 |
| 成熟度 | 2 个月，786 open issues | **5.8 年，10 open issues** |
| 安装 | bun install -g（37 npm 依赖） | **pip install txtai** |
| 与现有脚本生态 | ❌ TypeScript，独立体系 | ✅ Python，完全融入 scripts/ |
| 运营成本 | 3-15 元/月 | **0-15 元/月**（可全离线） |

### 1.2 架构变化

```
改造前：
Layer 1: Super KAM（行为规范）
Layer 2: gbrain（检索合成引擎）  ← PGLite WASM + bun，有兼容问题
Layer 3: Vault（知识内容）
Layer 4: LLM-Wiki（内容采集）

改造后：
Layer 1: Super KAM（行为规范） ← 不变
Layer 2: txtai（检索合成引擎）  ← SQLite + Python，稳定
Layer 3: Vault（知识内容）     ← 不变
Layer 4: LLM-Wiki（内容采集）   ← 不变
```

### 1.3 txtai 在架构中的角色

| 角色 | 说明 |
|------|------|
| 向量搜索引擎 | 语义搜索 vault 中的 knowledge/、cases/、raw/ 等目录 |
| RAG 合成引擎 | 搜索结果 → DeepSeek 或本地 LLM → 合成回答 + 引用 |
| MCP 服务 | 通过 MCP stdio 协议向 Codex 暴露搜索/问答/统计工具 |
| 索引管理 | 增量索引、全量重建、健康检查 |

### 1.4 txtai 不做的

- ❌ 不管理文件系统（Vault 层职责）
- ❌ 不做知识蒸馏（Super KAM 职责）
- ❌ 不抓取网页（LLM-Wiki 职责）
- ❌ 不修改 vault 文件（只读）
- ❌ 不干预 WAL 协议

---

## 2. 环境与依赖

### 2.1 运行时

| 项目 | 要求 | 现状 |
|------|------|------|
| Python | >= 3.10 | ✅ 3.12 |
| pip | 任意 | ✅ 已安装 |
| 内存 | 200-500 MB | ✅ 充足 |
| 磁盘 | 100-500 MB | ✅ 充足 |

### 2.2 模型选择

**推荐：本地 Sentence Transformer（BAAI/bge-small-zh-v1.5）**

| 模型 | 大小 | 维度 | 中文 | 网络需求 |
|------|:----:|:----:|:----:|:--------:|
| BAAI/bge-small-zh-v1.5 | ~30 MB | 512 | ✅ 优 | 下载一次，后全离线 |
| BAAI/bge-base-zh-v1.5 | ~100 MB | 768 | ✅ 优 | 下载一次，后全离线 |
| sentence-transformers/all-MiniLM-L6-v2 | ~80 MB | 384 | ⚠️ 英文为主 | 下载一次，后全离线 |

**选择建议：bge-small-zh-v1.5** — 体积小（30MB）、中文优化、512维（足够的区分度）、完全离线。

### 2.3 网络需求

| 操作 | 网络 | 次数 |
|------|:----:|:----:|
| `pip install txtai` | ✅ 需要 | 一次性（~5 MB） |
| 下载 bge-small-zh-v1.5 模型 | ✅ 需要 | 一次性（~30 MB） |
| 日常嵌入向量化 | ❌ 不需要 | — |
| 日常搜索 | ❌ 不需要 | — |
| RAG 合成（如果用 DeepSeek） | ✅ 需要 | 每次查询（少量） |
| RAG 合成（如果用本地 Ollama） | ❌ 不需要 | — |

**网络受限时的安装顺序：**
1. 先尝试 `pip install txtai`（可能被代理拦截）
2. 如果 pip 不通：下载 txtai wheel + 依赖到本地 → `pip install --no-index`
3. 模型文件：从 HuggingFace Hub 下载 .bin 文件 → 复制到缓存目录

---

## 3. 新增文件清单

### 3.1 核心文件

| 文件 | 用途 | 代码量 |
|------|------|:------:|
| `.txtai/config.yml` | txtai 配置（模型、索引路径、LLM） | ~20 行 |
| `scripts/txtai_index.py` | vault → txtai 索引工具（增量/全量） | ~80 行 |
| `scripts/txtai_mcp.py` | MCP 服务器（搜索/问答/统计工具） | ~60 行 |
| `scripts/txtai_query.py` | CLI 查询工具（快速测试用） | ~50 行 |
| `scripts/txtai_health.py` | txtai 索引健康检查 | ~30 行 |
| `scripts/txtai_rebuild.py` | 全量重建索引 | ~20 行 |
| `scripts/txtai_utils.py` | 共享工具函数（vault 发现、文件解析） | ~40 行 |

**总计新增代码：约 300 行 Python**（相比之下 gbrain 是 628 个 TypeScript 文件 + 37 npm 依赖）

### 3.2 需要修改的现有文件

| 文件 | 改动 | 行数 |
|------|------|:----:|
| `AGENTS.md` | 新增 txtai 检索路由规则 | +5 行 |
| `~/.codex/mcp.json` | gbrain → txtai MCP 配置 | 替换 1 块 |
| `scripts/auto_health.py` | 新增 txtai 健康检查 | +10 行 |
| `scripts/unified_index.py` | 新增 txtai 索引状态 | +10 行 |
| `SESSION-STATE.md` | 更新完成状态 | +3 行 |
| `KK-NEXUS-MANUAL.md` | 更新架构说明 | +10 行 |

**总计修改代码：约 40 行**

---

## 4. 核心实现设计

### 4.1 txtai 配置（.txtai/config.yml）

```yaml
# txtai 配置
embeddings:
  path: BAAI/bge-small-zh-v1.5    # 中文优化，30MB，全离线
  content: true                     # 存储全文，支持 SQL 查询
  sqlite:
    cache: 2GB                      # 索引缓存
  batch: 128                        # 批处理大小
  encode:
    batch: 64                       # 编码批处理

# 索引存储路径
writable: true
path: .txtai/index

# 用于 MCP 服务的 API 配置
api:
  mcp: true
  autodocs: false
```

### 4.2 索引流程（txtai_index.py）

```
输入：9 个 vault 目录（从 UNIFIED_INDEX.md 读取）
处理：
  for each vault:
    for each .md file in knowledge/ cases/ raw/:
      1. 读取 frontmatter（title, date, tags, status, source, domain）
      2. 读取正文内容（去除 frontmatter）
      3. 组装文本 = title + "\n" + tags + "\n" + content
      4. 构建元数据字典（filepath, domain, status, source, date）
      5. 添加到 txtai embeddings
  txtai embeddings.index() → 向量化 + SQLite 存储

输出：.txtai/index 目录（SQLite 数据库文件）
支持：--incremental（增量更新） / --full（全量重建）
```

### 4.3 MCP 服务（txtai_mcp.py）

暴露给 Codex 的工具：

| 工具名 | 功能 | 参数 | 返回 |
|--------|------|------|------|
| `txtai_search` | 语义搜索 | query, limit(10), domain(可选) | [{filepath, score, text, tags}] |
| `txtai_ask` | RAG 问答 | query, domain(可选) | {answer, sources[], gap_analysis} |
| `txtai_stats` | 索引统计 | — | {total_docs, by_domain, by_status, last_build} |
| `txtai_rebuild` | 重建索引 | — | {status, docs_indexed} |

### 4.4 查询工具（txtai_query.py）

CLI 命令行查询：
```bash
python scripts/txtai_query.py "授予价格如何确定"
# → 语义搜索，返回 top-5 片段

python scripts/txtai_query.py "授予价格如何确定" --rag
# → RAG 合成回答，带引用

python scripts/txtai_query.py "华建集团方案" --domain equity-incentive
# → 按领域过滤搜索

python scripts/txtai_query.py "授予价格如何确定" --explain
# → 搜索 + 解释为什么返回这些结果
```

---

## 5. 与现有 KK Nexus 各层的集成

### 5.1 与 Super KAM（Layer 1）的集成

**AGENTS.md 新增路由规则（添加到检索协议段落）：**

```
### txtai 语义检索（替代 gbrain）
当需要搜索 vault 知识库时：
1. txtai_search — 语义搜索（向量匹配，适合模糊查询）
2. txtai_ask — RAG 合成问答（自动检索+合成+gap 分析）
3. 搜索优先级：① txtai ② obsidian-cli ③ Select-String
```

**与已有检索协议的整合：**

```
当前检索优先级（按 UNIFIED_INDEX.md）：
① UNIFIED_INDEX.md
② obsidian-cli（关键词搜索）
③ KAM vault knowledge/index.md
④ llm-wiki index.md
⑤ Select-String（降级）

改造后检索优先级：
① txtai（语义搜索 + RAG 合成） ← 新增，最优先
② UNIFIED_INDEX.md（判断知识在哪）
③ obsidian-cli（关键词搜索兜底）
④ KAM vault knowledge/index.md
⑤ Select-String（纯文本降级）
```

**与已有脚本的集成：**

| 脚本 | 集成方式 |
|------|---------|
| auto_health.py | 新增 txtai 健康检查（索引是否存在、是否过期） |
| build_index.py | 新增 txtai 索引重建 |
| unified_index.py | 新增 txtai 索引状态字段 |
| auto_heartbeat.py | 新增 txtai 索引快照 |

### 5.2 与 Vault（Layer 3）的集成

- txtai **只读** vault 文件，不修改
- vault 文件是权威源头（system of record）
- vault 更新后 → 运行 `python scripts/txtai_index.py --incremental` 增量更新
- 蒸馏完成后 → 自动触发 txtai 索引更新

### 5.3 与 LLM-Wiki（Layer 4）的集成

- LLM-Wiki 采集 → 蒸馏到 vault → 运行 txtai 索引
- 不需要修改 LLM-Wiki 流程

### 5.4 与 Codex 的集成

**MCP 配置（~/.codex/mcp.json）：**

```json
{
  "servers": {
    "txtai": {
      "command": "python",
      "args": [
        "scripts/txtai_mcp.py"
      ],
      "env": {
        "DEEPSEEK_API_KEY": "sk-...",
        "TXT_CONFIG": ".txtai/config.yml"
      }
    }
  }
}
```

---

## 6. 使用场景与工作流

### 6.1 日常使用路径

```
用户问："上海国资股权激励的授予价格有什么限制？"

→ Codex 自动调 txtai_search（语义搜索）
   → 命中：knowledge/zk-ei-bb0-1-定价方法与模型.md（score: 0.89）
   → 命中：knowledge/zk-ei-aa0-3-上海国资指导意见.md（score: 0.82）
   → Codex 读#1 → 得到答案
   
或

→ Codex 调 txtai_ask（RAG 合成）
   → txtai 检索 + DeepSeek 合成
   → 返回："授予价格不得低于...（来源：zk-ei-bb0-1, zk-ei-aa0-3）"
   → 附注："脑内暂无 2026 年最新修订信息"
```

### 6.2 知识更新路径

```
新增文档到 vault/raw/user/
→ 蒸馏到 knowledge/ 和 cases/
→ 运行 python scripts/txtai_index.py --incremental
→ txtai 增量更新向量索引
→ 完成
```

### 6.3 全量重建路径

```
python scripts/txtai_index.py --full
→ 遍历所有 9 个 vault 的全部 .md 文件
→ 重建完整索引
→ 时间预估：~5-10 分钟（1600+ 文件）
```

---

## 7. 从 gbrain 迁移的步骤

### Step 1: 环境准备
```
pip install txtai sentence-transformers
# 如果 pip 网络不通，改用本地 wheel 安装
```

### Step 2: 创建配置和脚本
```
创建 .txtai/ 目录及 config.yml
创建 scripts/txtai_utils.py
创建 scripts/txtai_index.py
创建 scripts/txtai_mcp.py
创建 scripts/txtai_query.py
创建 scripts/txtai_health.py
```

### Step 3: 首次索引
```
python scripts/txtai_index.py --full
# 遍历所有 vault，建立向量索引
```

### Step 4: 配置 MCP
```
修改 ~/.codex/mcp.json → 指向 txtai_mcp.py
```

### Step 5: 更新 AGENTS.md
```
新增 txtai 检索路由规则
更新检索优先级
```

### Step 6: 验证
```
# 测试搜索
python scripts/txtai_query.py "授予价格"
# 测试 MCP
python scripts/txtai_mcp.py --test
# 测试健康检查
python scripts/txtai_health.py
```

### Step 7: 清理旧 gbrain 数据
```
保留 .gbrain/brain.pglite 作为存档备份
```

### Step 8: 更新集成脚本
```
修改 auto_health.py → 新增 txtai 检查
修改 unified_index.py → 新增 txtai 状态
```

---

## 8. 验证标准

| 验证项 | 方法 | 预期结果 |
|--------|------|---------|
| txtai 索引 | 运行 txtai_stats | 显示 1600+ 文档，9 个 domain |
| 语义搜索 | 搜索"授予价格" | 返回定价模型文档，score > 0.7 |
| RAG 合成 | 用 DeepSeek 问一个问题 | 返回带引用的合成回答 |
| MCP 服务 | Codex 调 txtai_search | 返回结构化搜索结果 |
| 增量更新 | 新增一个文件后更新索引 | 索引文档数 +1 |
| 健康检查 | 运行 txtai_health | 返回 OK 状态 |

---

## 9. 运营与维护

### 9.1 日常运维命令

```bash
# 语义搜索
python scripts/txtai_query.py "查询内容"

# RAG 问答（使用 DeepSeek 合成）
python scripts/txtai_query.py "查询内容" --rag

# 查看索引统计
python scripts/txtai_query.py --stats

# 增量更新索引（vault 有变化时）
python scripts/txtai_index.py --incremental

# 全量重建索引（索引损坏时）
python scripts/txtai_index.py --full

# 健康检查
python scripts/txtai_health.py

# 启动 MCP 服务（手动）
python scripts/txtai_mcp.py
```

### 9.2 自动运维

- `auto_health.py` 每次启动时自动检查 txtai 索引健康状态
- `unified_index.py --refresh` 同步 txtai 状态到统一索引
- 蒸馏完成后自动触发 `txtai_index.py --incremental`

### 9.3 备份与恢复

```
# 备份索引（SQLite 单文件，直接复制）
copy .txtai/index .txtai/index.backup

# 恢复
copy .txtai/index.backup .txtai/index

# 重建索引（无需备份，从 vault 重建）
python scripts/txtai_index.py --full
```

---

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|:----:|:----:|------|
| pip 网络不通 | 中 | 安装失败 | 下载 wheel 离线安装 |
| 模型下载被拦截 | 中 | 嵌入失败 | 用 Ollama 做嵌入（已有）或换用 DashScope API |
| 中文语义精度不足 | 低 | 搜索结果偏差 | bge-small-zh 是中文优化模型，且可升级到 bge-base-zh |
| txtai API 变化 | 低 | 升级需适配 | 封装层薄，适配成本低（~30 行） |
| SQLite 过大 | 低 | 查询变慢 | 1600 个文件远低于 SQLite 性能拐点（10万+） |
| DeepSeek API 不稳定 | 低 | RAG 合成降级 | 降级为纯搜索（不合成），用户自己读结果 |

---

## 11. 实施时间预估

| 阶段 | 内容 | 预估时间 |
|------|------|:--------:|
| 安装 | pip install + 下载模型 | 5-10 分钟 |
| 开发 | 创建 6 个脚本 + 配置 | 30-45 分钟 |
| 首次索引 | 索引 1600+ 文件 | 5-10 分钟 |
| MCP 配置 | 更新 mcp.json | 2 分钟 |
| AGENTS.md 更新 | 新增路由规则 | 5 分钟 |
| 验证测试 | 搜索 + RAG + MCP | 10-15 分钟 |
| 集成脚本修改 | auto_health.py 等 | 10 分钟 |
| **总计** | | **约 1.5 小时** |

---

## 12. 文件结构（改造后）

```
C:\Users\hexk\OneDrive\文档\New project 6\
├── AGENTS.md                    ← 新增 txtai 路由规则
├── SESSION-STATE.md
├── UNIFIED_INDEX.md             ← 新增 txtai 状态
├── KK-NEXUS-MANUAL.md           ← 更新架构说明
├── PLAN.md                      ← ★ 本文档
│
├── .txtai/                      ← 新增：txtai 索引目录
│   ├── config.yml               ← txtai 配置
│   └── index/                   ← SQLite 索引文件
│
├── scripts/
│   ├── txtai_utils.py           ← 新增：共享工具
│   ├── txtai_index.py           ← 新增：索引工具
│   ├── txtai_mcp.py             ← 新增：MCP 服务器
│   ├── txtai_query.py           ← 新增：CLI 查询
│   ├── txtai_health.py          ← 新增：健康检查
│   ├── auto_health.py           ← 修改：新增 txtai 检查
│   ├── unified_index.py         ← 修改：新增 txtai 状态
│   └── ...（其他现有脚本不变）
│
├── .gbrain/                     ← 保留为存档（不删除）
│   └── brain.pglite             ← 旧 gbrain 数据库
│
└── vault/（9 个 skill vault，不变）
```

---

## 13. 附录：txtai 与 gbrain 详细能力对比

| 能力 | gbrain | txtai | 对我们的重要性 |
|------|--------|-------|:-------------:|
| 语义搜索 | ✅ | ✅ | **核心** |
| 关键词搜索 | ✅ tsvector | ✅ SQLite FTS | **重要** |
| 混合搜索(RRF) | ✅ | ✅ weighted | **重要** |
| RAG 合成 | ✅ DeepSeek | ✅ 任意 LLM | **重要** |
| Gap Analysis | ✅ 原生 | ➕ 需加 prompt | 良好 |
| 知识图谱 | ✅ 实体关系图 | ✅ 语义相似图 | 一般 |
| 自动 Entity 提取 | ✅ 零 LLM | ➕ 需 workflow | 低优先 |
| 自动 Enrichment | ✅ dream cycle | ➕ 需脚本 | 低优先 |
| MCP 原生 | ✅ | ✅ | **核心** |
| REST API | ❌ | ✅ | 锦上添花 |
| Workflow | ❌ | ✅ 原生 | 锦上添花 |
| 多模态 | ❌ | ✅ | 不需要 |
| Windows 稳定 | ❌ | ✅ | **核心** |
| 与 Python 生态整合 | ❌ | ✅ | **核心** |
| 运营成本 | 3-15 元/月 | 0-15 元/月 | — |
