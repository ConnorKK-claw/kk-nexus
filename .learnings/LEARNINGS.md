## [2026-05-20] 11家案例逐期收益分析 + 数据导入

**Corrections:**

1. **上港集团第2批上市日偏差** — 案例文件记录为2025-11-06，实际原始公告写明上市流通日为2025-11-13。7天差异会影响股价取值。
   - Source: 上港集团第2批上市公告原文
   - 教训：蒸馏时以原始公告为准，案例文件可能简化/写错日期

2. **东方创业授予总量冲突** — 实施案例表(2026-05-16)记录628.60万股，具体案例文件(2026-05-17)记实际登记1,506.80万股。差异2.4倍。
   - Source: 上海国资股权激励实施案例(较早) vs 东方创业具体案例(较新)
   - 教训：具体案例文件更可靠，实施案例表的汇总数据可能自行计算/口径不同

3. **华谊集团上市流通日 vs 条件成就日差15%** — 第1批条件成就日5.67元(2024-09-11) vs 上市流通日6.70元(2024-10-30)，差异15%。用户要求用上市流通日计算收益，直接改变结果。
   - 教训：条件成就日和上市流通日必须严格区分

**Insights:**

1. **tushare API在Windows代理环境下的访问** — 系统代理(localhost:15236)会阻塞eastmoney API但tushare通过HTTP直接连接。需在Python中显式清除os.environ["HTTP_PROXY"]等变量。脚本文件执行比命令行传参更可靠。

**Best Practices:**

1. **收益计算精确到上市流通日** — 条件成就日和上市流通日可差数周，股价差异可达15%+
2. **终止实施案例的独特价值** — 上海电气(全部终止)和申能(部分取消)提供了正向案例之外的重要对照
3. **高管薪酬数据的用途** — 178号文40%上限检查需高管年薪数据，Excel导入后可用于交叉验证
4. **dd分类码** — 新增行业对标/统计类知识分类，用于exec-compensation等横向数据

## [2026-05-21] 全局检索系统升级

**Insights:**

1. **中文搜索的核心难点** — 简单的 substring lower() 对中文基本无效，必须用 jieba 做分词。但分词有性能成本，需先子串预筛再验证。
   - 工程策略：两阶段搜索（快速子串→jieba 验证）

2. **拼音模糊匹配的实用性** — 用户输入 "guquan" 能匹配到"股权"文档，对中文输入法错误场景很有用。

3. **DuckDuckGo 在中国网络的可用性** — 尽管 duckduckgo.com 可访问，但 ddgs 库直接访问可能被拦截，需测试确认。

**Best Practices:**

1. **全局工具装机策略** — 全局功能（搜索、网页获取）应装到 .codex/bin/，供所有项目共享；项目特有规则（蒸馏流程、内容路由）留在项目 AGENTS.md 中。

2. **TF-IDF 自定义 tokenizer** — scikit-learn 的 TF-IDF 默认 token_pattern 不支持中文，必须传入 tokenizer=jieba_tokenizer。

3. **PowerShell 中国绀问题** — PowerShell 传递中文参数时可能乱码，优先用 Python 写文件 + python -c 执行，而非 PowerShell here-string。


## [2026-05-23] 工程 vault 构建 — 模式提炼

**Corrections (本次新增):**

1. **PowerShell 字符串转义** — 只要涉及 Python inline + 多行文本 + 特殊字符，必出问题。
   - 规则：多行 Python 永远写 .py 文件；单行简单命令才用 `-c`
   - 创建临时文件用 `$env:TEMP\script.py`，执行完可删

2. **shared vault 的多 SKILL.md 注入** — `enhance_skillmd.py` 假设本地 vault/ 目录，不支持共享 vault。
   - 手动注入可，但每次修改模板后需更新 7+ 个 SKILL.md
   - 改进方向：给 enhance_skillmd.py 加 `--shared <vault-path>` 参数

3. **文件创建后验证** — Set-Content 可能出现静默失败。
   - 规则：每次文件写入后用 `Get-Item / Test-Path` 确认存在
   - 建索引后用 `build_index.py --dry-run` 确认条目数

**Insights (本次新增):**

1. **共享 vault vs 本地 vault 的分工决策正确** — 7 个 workflow skills 共用 1 个 vault 避免了大量的知识碎片。每次跨 skill 的知识检索只需查 1 个 index，O(1)。

2. **AZ 分类码映射维护** — 每个 vault 的 zk-categories.md 需要手工更新以匹配实际分类。bootstrap 脚本生成的通用 aa/bb/cc 映射对 engineering-practices 不适用，需要覆盖为 aa(CI)/bb(PR)/cc(目标)/dd(安全)/ee(工具)。

3. **模板注入的幂等性** — 每次注入前检查 marker 是否存在很重要，否则重复注入会损坏 SKILL.md。本 session 的 `MARKER` 检查避免了此问题。

**Best Practices (本次新增):**

1. **脚本路径映射表** — 各脚本期望的 path 参数类型：

   | 脚本 | 期望路径 | 示例 |
   |------|----------|------|
   | bootstrap_vault.py | skill 目录 | `~/.codex/skills/xxx` |
   | enhance_skillmd.py | skill 目录 | `~/.codex/skills/xxx` |
   | build_index.py | vault 目录 | `~/.codex/skills/xxx/vault` |
   | validate_vault.py | skill 目录 | `~/.codex/skills/xxx` |
   | unified_index.py | (无参, 自动) | — |
   | vault_ingest.py | vault 目录 | `--vault <vault-path>` |

2. **PowerShell → Python 数据通道策略**：
   - 写 Python 脚本 → `Set-Content` 到 `.py` 文件 → 执行
   - 不在 PowerShell 中构造 Python 多行字符串
   - 路径用双反斜杠 `\` 或 raw string + 转义版

3. **SKILL.md 注入完整性检查**：
   - 注入后运行 `Select-String "## 共享工程实践知识库" SKILL.md` 确认存在
   - 运行 `Select-String "## Vault 知识库" SKILL.md` | Measure-Object 确认不重复
