# Super KAM — 项目根目录

## 项目说明

Super KAM（Knowledge-Augmented Memory）架构项目。
为每个 Codex skill 配备专属知识库（vault），提升 agent 的领域知识深度。

## 项目内容

- `scripts/` — 通用工具脚本（vault_ingest, bootstrap_vault, enhance_skillmd）
- `templates/` — SKILL.md vault 注入块模板
- `KAM-IMPLEMENTATION.md` — 适配跟踪表

## 全局规则

所有通用规则（vault 结构、命名规范、检索协议、元数据 schema）定义在：
`~/.codex/AGENTS.md`

## 关联外部 vault

- 张江高科 company vault: `C:\Users\hexk\OneDrive\Desktop\张江高科\database\`


## 会话启动序列

每次会话开始前，按以下顺序加载上下文：
1. `AGENTS.md`（本文件）— 项目规则
2. `SOUL.md` — Agent 身份
3. `USER.md` — 用户画像
4. `MEMORY.md` — 长期记忆
5. `SESSION-STATE.md` — 当前任务状态
6. `UNIFIED_INDEX.md` — 统一知识索引



## 原始素材处理协议（Raw Material Processing Protocol）

> 任何新文件导入 vault 后，必须完成以下全部环节才能视为可被 005 使用。
> 这是默认规则，除非用户明确说不做某一步。

### 公共骨架（所有 vault 通用）

`
导入 -> 验证 -> 语义索引(txtai) -> [领域蒸馏] -> 知识索引 -> 作者索引 -> 统一索引 -> 健康检查
`

| 环节 | 脚本 | 通用? |
|------|------|:----:|
| 导入 | 手动或 vault_ingest.py | yes |
| 验证 | python scripts/validate_vault.py <vault-path> | yes |
| 语义索引 | python scripts/txtai_index.py --full | yes |
| **蒸馏** | **每个 vault 独立设计** | **no** |
| 知识索引 | python scripts/build_index.py <vault-path> | yes |
| 作者索引 | python scripts/build_authors_index.py <vault-path> | yes |
| 统一索引 | python scripts/unified_index.py --refresh | yes |
| 健康检查 | python scripts/weekly_vault_health.py | yes |

> 蒸馏策略必须按 vault 独立设计，不可跨域套用。
> 每个 vault 在初始化时需定义其蒸馏分类法（分类码映射表），写入 vault/zk-categories.md。

### 便捷命令（全流程）

`powershell
python scripts/validate_vault.py <vault-path>
python scripts/txtai_index.py --full
python scripts/distill_<domain>.py --vault <vault-path>
python scripts/build_index.py <vault-path>
python scripts/build_authors_index.py <vault-path>
python scripts/unified_index.py --refresh
python scripts/weekly_vault_health.py
`

### 失败回退

任何一步失败时：
1. 中止后续步骤
2. 报告具体错误
3. 修复问题后从头运行全流程
4. 不允许跳过错步骤继续

### 验证标准

全流程完成后必须全部满足：
- vault/raw/ 下无 status: raw 的文件（蒸馏覆盖）
- txtai 索引存在且 query 返回结果
- knowledge/index.md 存在且包含所有节点
- UNIFIED_INDEX.md 中该 vault 被正确索引
- 健康检查无报错
- 所有文件 UTF-8 编码，无双重 BOM
## 完整处理链

```
导入 -> 验证 -> 语义索引 -> 蒸馏 -> 知识索引 -> 作者索引 -> 统一索引 -> 健康检查
```

### 各环节说明

| 步骤 | 脚本/操作 | 产出 | 必须? |
|------|----------|------|:----:|
| 0. 导入 | 文件放入 vault/raw/user/ 或 vault/raw/agent/ | 原始 MD 文件 | yes |
| 1. 验证 | python scripts/validate_vault.py <vault-path> | 确认 frontmatter/编码/命名合规 | yes |
| 2. 语义索引 | python scripts/txtai_index.py --full | txtai 向量索引，启用语义搜索 | yes |
| 3. 蒸馏 | python scripts/auto_distill_vault.py <vault-path> 或人工 | knowledge/ 节点 + cases/ 案例 | note 1 |
| 4. 知识索引 | python scripts/build_index.py <vault-path> | knowledge/index.md | yes |
| 5. 作者索引 | python scripts/build_authors_index.py <vault-path> | knowledge/authors-index.md | note 2 |
| 6. 统一索引 | python scripts/unified_index.py --refresh | UNIFIED_INDEX.md | yes |
| 7. 健康检查 | python scripts/weekly_vault_health.py | 确认无 BOM/编码/重复 | yes |

> note 1: 公众号/新闻类素材必须蒸馏（提取观点归入 knowledge/）；法规原文/原始数据表可跳过。
> note 2: 多作者/多来源的 vault 需要作者索引；单一来源可跳过。

### 快捷命令（全流程）

```powershell
python scripts/validate_vault.py .\vault
python scripts/txtai_index.py --full
python scripts/auto_distill_vault.py .\vault
python scripts/build_index.py .\vault
python scripts/build_authors_index.py .\vault
python scripts/unified_index.py --refresh
python scripts/weekly_vault_health.py
```

### 失败回退

任何一步失败时：
1. 中止后续步骤
2. 报告具体错误
3. 修复问题后从头运行全流程
4. 不允许跳过错步骤继续

### 验证标准

全流程完成后必须全部满足：
- vault/raw/ 下无 status: raw 的文件（蒸馏覆盖）
- txtai 索引存在且 query 返回结果
- knowledge/index.md 存在且包含所有节点
- UNIFIED_INDEX.md 中该 vault 被正确索引
- 健康检查无报错
- 所有文件 UTF-8 编码，无双重 BOM


## WAL 协议

每次会话结束前必须执行：
1. 更新 SESSION-STATE.md（"本轮完成" + "剩余工作队列"）
2. 写入 memory/YYYY-MM-DD.md（关键决策 + 教训）
3. 如果上下文 > 60%，追加到 working-buffer.md
4. 运行 python scripts/unified_index.py --refresh（如果 vault 有变更）
5. 运行 python scripts/consolidate_learnings.py（汇聚 .learnings/ 到 MEMORY.md）
