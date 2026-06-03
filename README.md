# Super KAM（Knowledge-Augmented Memory）

> 项目根目录：`C:\Users\hexk\OneDrive\文档\New project 6`
> 更新日期：2026-05-15

---

## 项目说明

为每个 Codex skill 配备专属知识库（vault），实现领域知识的摄取、蒸馏、检索和维护。

## 当前状态

| 指标 | 数值 |
|------|------|
| 适配 skill | 1（equity-incentive） |
| Ontology vault | 2（equity-incentive + 张江高科） |
| knowledge 节点 | 4 |
| raw 文件 | 12（3 已蒸馏, 9 待蒸馏） |
| 工具脚本 | 7 |

## 核心文件

| 文件 | 说明 |
|------|------|
| `~/.codex/AGENTS.md` | **全局配置** — vault 协议 + 命名规范 + schema + 检索协议 + 蒸馏流程 |
| `AGENTS.md` | 项目级规则 |
| `HANDOVER.md` | 交接文档 |
| `KAM-IMPLEMENTATION.md` | 实施跟踪表 |
| `scripts/bootstrap_vault.py` | 创建 vault 8 目录 + ontology 注册 |
| `scripts/enhance_skillmd.py` | SKILL.md vault 上下文注入/卸载/更新（自动备份） |
| `scripts/vault_ingest.py` | 文件转化导入（markitdown + 去重 + 归档） |
| `scripts/build_index.py` | 扫描 vault 生成 knowledge/index.md |
| `scripts/validate_vault.py` | YAML schema + 命名规范校验 |
| `scripts/health_check.py` | 未蒸馏检测 + 过期检测 + 重复标签检测 |
| `scripts/query_ontology.py` | 跨 vault 查询（按 domain/company） |
| `templates/skill-header.md` | vault 注入块模板（含蒸馏 SOP + 使用追踪） |

## 常用命令

```bash
# 为 skill 创建 vault
python scripts/bootstrap_vault.py ~/.codex/skills/<skill-name>

# 增强 SKILL.md
python scripts/enhance_skillmd.py ~/.codex/skills/<skill-name>

# 导入文件
python scripts/vault_ingest.py 文件.pdf --vault <vault-path> --source user

# 重建索引
python scripts/build_index.py <vault-path>

# 校验 vault
python scripts/validate_vault.py <vault-path>

# 健康检查
python scripts/health_check.py <vault-path>

# 查询 ontology
python scripts/query_ontology.py --type Vault --domain equity-incentive
```

## 定期维护

建议每周运行一次健康检查：

```bash
python scripts/health_check.py ~/.codex/skills/equity-incentive/vault
```

或设置 Windows Task Scheduler 定时执行。

## 关联外部 vault

- equity-incentive: `~/.codex/skills/equity-incentive/vault`
- 张江高科: `C:\Users\hexk\OneDrive\Desktop\张江高科\database\`（旧 schema，只读）

## 待完成

- [ ] Obsidian CLI 启用（设置 → 常规 → 启用命令行接口）
- [ ] 剩余 9 个 raw 文件蒸馏
- [ ] 更多 skill 适配（tax-compliance-expert, a-share-research 等）
