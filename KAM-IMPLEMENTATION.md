# KAM 架构实施跟踪

> 项目根目录：`C:\Users\hexk\OneDrive\文档\New project 6`
> 更新日期：2026-05-17
> 基于：v2 修复计划（KM 成熟度评估驱动）

---

## 修复执行状态

### Phase 1：检索 + 获取

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | 全局 AGENTS.md 限定作用域 + ZK ID 规则 + 检索优先级 + 外部兼容 | ✅ |
| 2 | build_index.py 索引生成脚本 | ✅ |
| 3 | vault_ingest.py 文件转化导入（去重/批量/归档） | ✅ |
| 4 | 端到端验证（bootstrap -> ingest -> build_index -> 检索命中） | ✅ |

### Phase 2：组织 + 质量

| 步骤 | 内容 | 状态 |
|------|------|------|
| 5 | ZK ID 生成规则（已合并入步骤 1） | ✅ |
| 6 | validate_vault.py Schema 校验脚本 | ✅ |
| 7 | enhance_skillmd.py 备份/卸载/更新 + 插入逻辑修复 | ✅ |

### Phase 3：维护 + 应用

| 步骤 | 内容 | 状态 |
|------|------|------|
| 8 | 蒸馏 SOP 内嵌到 skill-header.md | ✅ |
| 9 | health_check.py 健康检查脚本 | ✅ |
| 10 | 知识使用追踪（skill-header.md ref 规则） | ✅ |
| 11 | query_ontology.py 查询工具 | ✅ |
| 12 | KAM-IMPLEMENTATION.md 更新 | ✅ |

---

## Skill 适配状态

| Skill | Vault | knowledge | cases | SKILL.md | Ontology | 状态 |
|-------|:-----:|:---------:|:-----:|:--------:|:--------:|------|
| equity-incentive | ✅ | 15 | 14 | ✅ | ✅ | 就绪 ✅ |
| tax-compliance-expert | ✅ | 14 | 1 | ✅ | ✅ | 就绪 ✅ |
| engineering-practices | ✅ | 10 | 1 | ✅ (4+3 shared) | ✅ | 就绪 ✅ |
| 其他 skill（量化交易等，详见 HANDOVER.md） | ❌ | — | — | ❌ | ❌ | 待开始 |

---

## 脚本清单

| 脚本 | 功能 | 状态 |
|------|------|------|
| `bootstrap_vault.py` | 创建 vault 8 目录 + 注册 ontology | ✅ |
| `enhance_skillmd.py` | SKILL.md vault 上下文注入/卸载/更新 | ✅ |
| `vault_ingest.py` | 文件转化导入（markitdown + 去重 + 归档） | ✅ |
| `build_index.py` | 扫描 vault 生成 knowledge/index.md | ✅ |
| `validate_vault.py` | YAML schema + 命名规范校验 | ✅ |
| `health_check.py` | 未蒸馏检测 + 过期检测 + 重复标签检测 | ✅ |
| `query_ontology.py` | 跨 vault 查询（按 domain/company） | ✅ |
| `gen_bb0_comparison.py` | 生成案例横向对比报告 | ✅ |
| `update_cases.py` | 批量更新 case 文件 | ✅ |
| `fetch_market_data.py` | 获取历史股价数据 | ✅ |
| `fix_stock_source.py` | 修复股票来源数据一致性 | ✅ |
| `_deploy_all.py` | 一键部署更新到 vault | ✅ |

---

## 环境状态

| 项目 | 状态 |
|------|------|
| Python 3.12 | ✅ |
| markitdown | ✅（PDF 转换成功，DOCX 偶有失败） |
| ontology graph.jsonl | ✅ 5 个实体（含 equity-incentive Vault + tax-compliance Vault） |
| equity-incentive vault 校验 | ✅ 337/337 通过（2026-05-17） |
| tax-compliance vault 校验 | ✅ 17/17 通过（2026-05-16） |
| Obsidian CLI | ⏳ 需用户手动启用 |

---

## 已知限制

1. **markitdown 对部分 DOCX 格式转换失败** — 需调查或降级到纯文本提取
2. **health_check 对法规类知识（date = 发布年份）会产生过期误报** — 标记 `status: verified` 可排除
3. **跨 vault 检索依赖 ontology JSONL 解析** — agent 需在 SKILL.md 注入块中明确调用 query_ontology.py
4. **journal 多 YAML 块文件** — journal 可能包含多个 YAML frontmatter，每个都需满足 schema

---

## 后续迭代

| 项 | 优先级 | 状态 |
|------|--------|:----:|
| 分母计算口径确认（178号文循环计算） | P1 | ⏳ 待做 |
| Obsidian CLI 启用 | P1 | ⏳ 需用户手动操作 |
| 张江高科 company vault 注册到 ontology | P2 | ⏳ 待做 |
| destroy_vault.py 销毁脚本 | P3 | ⏳ 待做 |
| ~~微信股权激励素材批量导入~~ | P1 | ✅ 完成（250+ raw 文件，已蒸馏 10+ 案例） |
| ~~蒸馏 SOP 首次执行~~ | P1 | ✅ 已嵌入 skill-header.md |
| ~~上海机场案例导入~~ | — | ✅ 31份公告 -> 1个案例（2026-05-17） |
| ~~11家公司案例导入蒸馏~~ | P1 | ✅ 全部完成（2026-05-17） |
| ~~对比报告生成~~ | P1 | ✅ zk-ei-bb0-0-11-cases-comparison-report.md |
| ~~aa0-0/aa0-3 乱码修复~~ | — | ✅ 已修复（2026-05-17） |

