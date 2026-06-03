# Super KAM 001 号员工搭建流程固化

> 归档日期：2026-05-16
> 归档人：Agent (Equity-Incentive Expert)
> 状态：固化完成 ✓

---

## 一、Super KAM 是什么

Knowledge-Augmented Memory 架构。为每个 Codex skill 配备专属知识库（vault），
提升 agent 在特定领域的知识深度和检索效率。

**核心理念**: 知识不写在 SKILL.md 里，写在 vault 里。SKILL.md 只负责指挥和路由。

---

## 二、001 号员工档案

| 项目 | 内容 |
|------|------|
| 编号 | 001 |
| 名称 | equity-incentive（股权激励专家） |
| 角色 | A 股/国资/科创板股权激励方案设计 + 法规合规 |
| Skill 路径 | `~/.codex/skills/equity-incentive/` |
| Vault 路径 | `~/.codex/skills/equity-incentive/vault/` |
| 知识节点数 | 9 个（法规框架 4 + 操作实务 5） |
| 案例数 | 3 个 |
| 模板数 | 3 个 |
| 原始素材 | 12 个文件导入（PDF/DOCX/MD） |
| 运行状态 | 已蒸馏 5/12，可正常检索使用 |

---

## 三、搭建流程（可复制到新 skill）

### Phase 0: 前置条件

```
Python 3.12+
pip install markitdown
ontology graph.jsonl 就绪（bootstrap 自动创建）
```

### Phase 1: 创建 vault

```bash
# 1. 创建 vault 目录结构 + 注册 ontology + 生成 zk-categories.md
python bootstrap_vault.py ~/.codex/skills/<skill-name>
# 输出: vault/ 8 子目录 + ontology 注册 + zk-categories.md
```

### Phase 2: 注入 SKILL.md

```bash
# 2. 向 SKILL.md 注入 vault 上下文块（自动备份原文件）
python enhance_skillmd.py ~/.codex/skills/<skill-name>
# 输出: SKILL.md.bak.{timestamp} + 注入后的 SKILL.md
```

### Phase 3: 导入原始素材

```bash
# 3a. 用户直接给的素材 → raw/user/
python vault_ingest.py <文件> --vault <vault-path> --source user --tags "标签1,标签2" --domain <domain>

# 3b. Agent 发现 + 用户批准的素材 → raw/agent/
python vault_ingest.py <文件> --vault <vault-path> --source agent --tags "标签1,标签2" --domain <domain>
```

导入后自动重建 `knowledge/index.md`。

### Phase 4: 蒸馏知识

当 `raw/` 下有 5+ 个未蒸馏文件，或用户要求蒸馏时：

1. 读取 raw/ 下 status: raw 的文件
2. 提取关键概念 → knowledge/zk-{domain}-{catseq}-{docseq}-{title}.md
3. 提取实操案例 → cases/
4. 修改源文件 status: raw → status: distilled
5. 运行 `python build_index.py <vault-path>` 重建索引

### Phase 5: 验证与维护

```bash
# Schema 校验
python validate_vault.py <vault-path>

# 健康检查（过期检测 + 重复标签 + 未蒸馏提醒）
python health_check.py <vault-path>

# 知识使用追踪（手动写入 journal/YYYY-MM-DD.md）
- [ref] knowledge/zk-xxx.md — 用于<查询主题>
```

---

## 四、Vault 目录结构规范

```
vault/
├── raw/user/          # 用户导入的原始资料 → --source user
├── raw/agent/         # Agent 发现+用户批准的素材 → --source agent
├── raw/original/      # 原始文件备份（PDF/DOCX 等）
├── knowledge/         # 精化知识节点
│   └── index.md       # 自动生成的索引（优先检索）
├── templates/         # 方案模板（{purpose}-template.md）
├── cases/             # 案例/参考（日期前缀）
├── journal/           # 操作日志（YYYY-MM-DD.md）
└── auto-update/       # 定时任务写入
```

---

## 五、关键规则

### 文件命名

| 目录 | 格式 | 示例 |
|------|------|------|
| raw/ | `YYYY-MM-DD-{slug}-{source}.md` | `2026-05-15-上海国资股权激励指导意见-agent.md` |
| knowledge/ | `zk-{domain}-{catseq}-{docseq}-{title}.md` | `zk-ei-aa0-0-state-owned-equity-incentive-regulation.md` |
| templates/ | `{purpose}-template.md` | `equity-incentive-proposal-template.md` |
| cases/ | `YYYY-MM-DD-{company}-{topic}-{source}.md` | `2026-05-15-张江高科-股权激励-user.md` |
| journal/ | `YYYY-MM-DD.md` | `2026-05-16.md` |

### YAML Frontmatter Schema

```yaml
---
title: 文件标题
date: YYYY-MM-DD
source: user | agent | distilled
original_source: user | agent
source_path: original/源文件.pdf
domain: equity-incentive | ...
tags: [标签1, 标签2]
status: raw | distilled | verified | expired
expirable: false       # 法规等静态参考设为 false 避免过期误报
imported_by: vault_ingest.py | bootstrap | manual
imported_at: YYYY-MM-DDTHH:MM:SS
---
```

### Agent 导入 SOP（半自动）

当用户提问无法被 vault 充分回答时：
1. 识别知识缺口
2. 向用户提议补充
3. 用户批准 + 指定来源
4. 默认优先使用官方、权威信息源
5. 执行 `vault_ingest.py --source agent` 导入
6. 告知结果并记录 journal

**未经用户明确批准，不得私自扩充 vault。**

---

## 六、工具链清单

| 脚本 | 功能 | 调用时机 |
|------|------|---------|
| `bootstrap_vault.py` | 创建 vault 8 目录 + ontology 注册 + zk-categories.md | 新 skill 初始化 |
| `enhance_skillmd.py` | SKILL.md 注入/卸载/更新 vault 上下文块 | 新 skill 初始化 / 模板更新 |
| `vault_ingest.py` | 文件转化导入（支持 --tags --domain --source | 每次导入素材 |
| `build_index.py` | 扫描 vault 生成 knowledge/index.md | 每次导入/蒸馏后自动触发 |
| `validate_vault.py` | YAML schema + 命名规范校验 | 维护期 |
| `health_check.py` | 过期检测 + 重复标签 + 未蒸馏提醒 | 定期维护 |
| `query_ontology.py` | 跨 vault 查询（按 domain/company） | 检索时 |

**脚本位置**: `~/OneDrive/文档/New project 6/scripts/`
**全局规则**: `~/.codex/AGENTS.md`

---

## 七、从 001 号学到的教训

### 已解决的问题

1. **BOM 污染**: PowerShell 的 Out-File 默认带 UTF-8 BOM，会导致 `SyntaxError: invalid non-printable character U+FEFF`。
   → 全部脚本用 `encoding="utf-8"` 重写（不含 BOM）

2. **转义字符陷阱**: PowerShell 中 `$c -replace 'A',"B`r`nC"` 会写入字面量 `` `r`n `` 而非真正换行。
   → 写入文件始终用 Python 或 `Out-File -Encoding UTF8`

3. **法规节点过期误报**: `date: 2006-09-30` 的法规节点被 health_check 判定为 238 个月未更新。
   → 引入 `expirable: false` 字段豁免

4. **tags 为空**: 导入时无标签输入，所有 raw 文件 tags 为空。
   → vault_ingest.py 新增 `--tags` 参数

5. **ZK ID 命名歧义**: 文档中的 `aa1-0` 示例与实际文件 `aa0-0` 不一致。
   → AGENTS.md 重写为 4 段式 `{domain}-{catseq}-{docseq}-{title}`

6. **zk-categories.md 缺 frontmatter**: 通过 validate_vault.py 检测到并修复。
   → bootstrap_vault.py 自动生成带 frontmatter 的版本

### 待改进

- vault_ingest.py 导入的 raw 文件 tags 为空（历史遗留，新文件已修复）
- templates/ 下一个文件命名不规范（`-checklist` 而不是 `-template`）
- auto-update/ 未启用
- journal 刚起步，使用追踪数据积累不足

---

## 八、推广到新 skill 的检查清单

- [ ] `bootstrap_vault.py <skill-dir>` — 创建 vault
- [ ] `enhance_skillmd.py <skill-dir>` — 注入 SKILL.md
- [ ] 导入原始素材（user 或 agent 来源）
- [ ] 蒸馏 raw → knowledge + cases
- [ ] `validate_vault.py` 通过
- [ ] `health_check.py` 无意外告警
- [ ] ontology 中 Vault 实体已注册
- [ ] SKILL.md 中 `## Vault 知识库` 段正确
- [ ] 首次使用验证：检索 → 引用 → journal 记录
