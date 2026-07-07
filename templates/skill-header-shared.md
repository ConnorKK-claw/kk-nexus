# KAM Shared Vault 上下文注入（工程实践）

> 将此段插入 SKILL.md 第一个 ## 标题之前，以启用共享 vault 知识注入。
> 本 vault 由多个 engineering workflow skills 共享。

---

## 共享工程实践知识库

本 skill 共享 engineering-practices vault，用于工程实践知识管理。

vault 路径: C:\Users\hexk\.codex\skills\engineering-practices\vault\

### 启动时检索

每次加载时**必须**先检索 vault 知识：

1. **优先读索引**: 读取 C:\Users\hexk\.codex\skills\engineering-practices\vault\knowledge\index.md（O(1) 全貌）
2. **索引命中后**: 按路径读取具体的 knowledge/ 或 cases/ 文件
3. **索引未命中时**: Select-String -Path "C:\Users\hexk\.codex\skills\engineering-practices\vault" -Pattern "关键词" -Recurse 全文搜索
4. **外部 vault**: 查 ontology 发现关联 vault（如 equity-incentive），进入搜索

### 操作指引

| 操作 | 方式 |
|------|------|
| 检索知识 | 先读 ault/knowledge/index.md，按需读具体文件 |
| 记录新洞察 | 写入 ault/journal/YYYY-MM-DD.md |
| 引用模板 | 读取 ault/templates/ 目录下的文件 |
| 参考案例 | 搜索 ault/cases/ 目录 |
| 跨 vault 查询 | 查 ontology 中关联的 Vault 实体 |
| **蒸馏知识** | 见下方蒸馏 SOP |
| **导入文件** | python vault_ingest.py <文件> --vault <vault-path> --source user\|agent |

### Agent 导入 SOP（半自动）

当用户提出的问题在当前 vault 中无法被充分回答时，执行以下流程：

1. **识别缺口**: 确认 vault 中缺少哪些知识导致无法完整回答
2. **提议扩充**: 向用户说明缺口所在，提议补充特定资料
3. **用户批准**: 获得明确许可后，方可执行导入
4. **指定来源**: 优先使用用户直接指定的来源，默认优先选择官方、权威信息源
5. **半自动导入**: 执行 python vault_ingest.py <文件> --vault <vault-path> --source agent --tags "<标签>"
   - --source agent: 标记为 agent 发现、用户批准的素材
   - --tags: 按用户指示或内容自动生成标签
6. **告知结果**: 导入完成后，告知用户并在 journal 中记录

**重要规则**:
- 未经用户明确批准，不得私自扩充 vault
- aw/agent/ = agent 发现 → 用户批准 → agent 导入（半自动）
- aw/user/ = 用户直接提供 → agent 导入（全手动）
- 两者在蒸馏时同等对待，但 source 字段保留溯源信息

### 知识使用追踪

每次从 ault/knowledge/ 引用知识节点后，在 ault/journal/ 当日文件追加一行引用记录：

`
- [ref] knowledge/zk-ep-xx-x-xxx.md — 用于<查询主题>
`

此记录用于统计知识使用频率，识别冷热节点。

### 知识蒸馏 SOP

当用户要求蒸馏，或 vault/raw/ 下有超过 5 个未蒸馏文件时，执行：

1. 读取 ault/raw/ 下 status: raw 的待蒸馏文件
2. 提取关键概念、规则、方法论 → 写入 ault/knowledge/
   - 命名: zk-{domain}-{catseq}-{docseq}-{title}.md
   - 带完整 YAML frontmatter（source: distilled, original_source 保留, distilled_from 指向源文件）
3. 提取实操案例 → 写入 ault/cases/
4. 修改源文件 YAML status: raw → status: distilled
5. 运行 python build_index.py <vault-path> 重建索引

### 目录结构

`
vault/
├── raw/user/          # 用户导入的原始资料
├── raw/agent/         # agent 导入的原始资料
├── raw/original/      # 原始文件备份（PDF/DOCX 等）
├── knowledge/         # 精化知识节点
│   └── index.md       # 自动生成的知识索引（优先检索）
├── templates/         # 方案模板
├── cases/             # 案例/参考
├── journal/           # 操作日志
└── auto-update/       # 定时任务写入
`

---

## 配置需求

- [x] vault 目录已创建（scripts/bootstrap_vault.py）
- [x] vault 已在 ontology 中注册
- [ ] （可选）scheduled-tasks 定时更新已设置
