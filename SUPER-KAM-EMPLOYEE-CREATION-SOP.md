---
title: Super KAM 员工创建 SOP
date: 2026-05-25
source: agent
domain: super-kam
tags: [SOP, 方法论, 员工创建]
status: verified
freshness_months: 12
last_reviewed: 2026-05-25
---

# Super KAM 员工创建 SOP

> 基于004号员工（hk-ipo）创建过程提炼的可复用方法论
> 适用场景：创建新 KAM 员工 / 对现有 KAM 进行架构优化

## 一、前置准备

### 1.1 选择参考对象
选定一个已有的成熟 KAM 作为架构参考（如001 equity-incentive），**不要从零发明架构**。

| 参考维度 | 具体内容 |
|---------|---------|
| 知识分类 | 复制 `zk-{domain}-{catseq}-{docseq}-{title}` 命名体系 |
| YAML schema | 复用 field 定义（含 related/freshness_months 等增强字段） |
| SKILL.md 章节结构 | 协议章节布局直接复制后修改 |
| vault 目录结构 | bootstrap_vault.py 一键生成 |

### 1.2 调查已有技能生态
扫描现有 skills 列表，识别哪些可作**增强技能**接入。规则：不在 SKILL.md 中显式声明激活条件 = 永远不跑。

### 1.3 审查领域最佳实践
- 搜索该领域的权威方法论（如 Karpathy llm-wiki）
- 对比现有架构，识别差距
- 审查 Super KAM 历史优化记录，避免重复发明

## 二、需求分析阶段

### 2.1 必须回答的8个问题

| # | 问题 | 产出物 |
|:-|------|--------|
| 1 | Skill 名称和 domain 缩写是什么？ | 如 `hk-ipo` / domain=`hk-ipo` |
| 2 | 知识覆盖范围是什么？ | 如 A股IPO+H股IPO+A-to-H+上市后合规 |
| 3 | 分类码体系如何设计？ | aa0/bb0/cc0/dd0/ee0/gg0 等 |
| 4 | 核心能力模块有哪些？ | 每个模块有知识映射和激活条件 |
| 5 | 哪些增强技能可以接入？ | 每个技能有触发条件 |
| 6 | 跨KAM协作对象是谁？ | 如001(股权激励)、002(税务) |
| 7 | 知识节点如何创建？（三路径） | Agent写入 + 用户上传 + 经批准后下载 |
| 8 | 自优化机制采纳哪些？ | 13项（含Karpathy衍生） |

### 2.2 三层审查法

在决策前执行三层审查，确保没有遗漏：

**第一层：参考已有的 Super KAM 员工（001/002/...）**
- 复制架构模式，识别差异化

**第二层：审查已有技能生态**
- 识别可作为增强技能的现有 skill

**第三层：审查领域最佳实践 + KAM历史优化**
- 对标权威方法论，吸收已有经验教训

## 三、架构设计规范

### 3.1 分类码约定

| 码 | 名称 | 用途 |
|----|------|------|
| aa0 | 法规/理论框架 | aa0-0, aa0-1, ... |
| bb0 | 操作实务/流程 | bb0-0 ~ bb0-7 |
| cc0 | 可比/对标数据 | cc0-0 ~ cc0-3 |
| dd0 | 测算/分析 | dd0-0 ~ dd0-5 |
| ee0 | 实操经验/踩坑 | ee0-0 ~ ee0-3 |
| gg0 | 蒸馏知识 | gg0-0, gg0-1 |

格式：`zk-{domain}-{catseq}-{docseq}-{slug}.md`

### 3.2 SKILL.md 必须包含的12个章节

| # | 章节 | 用途 | 必选 |
|:-|------|------|:---:|
| 1 | 会话启动序列 | SOUL.md -> TOOLS.md -> index.md -> 按需加载 | Y |
| 2 | Vault 知识库 | 检索协议、操作指引、目录结构 | Y |
| 3 | YAML Schema | 知识节点 frontmatter 定义 | Y |
| 4 | 工具偏好 | 文档处理/数据源选择策略 | Y |
| 5 | 大文档分块策略 | >100页文档拆分规则 | Y |
| 6 | 核心能力 | 知识映射+增强技能+触发条件 | Y |
| 7 | 增强技能协议 | 每个外部技能的激活条件 | Y |
| 8 | 跨KAM协作协议 | 委托其他KAM的场景和数据格式 | Y |
| 9 | 对话结晶协议 | 有价值问答->知识节点 | Y |
| 10 | Lint 协议 | 定期维基健康检查 | Y |
| 11 | 知识保鲜协议 | 各分类的审查周期 | Y |
| 12 | WAL 协议 | 会话结束前收尾流程 | Y |

### 3.3 知识节点 YAML 规范

```yaml
title: 节点标题
date: YYYY-MM-DD
source: user | agent | distilled
domain: {skill-domain}
tags: [标签1, 标签2]
status: raw | distilled | verified | expired
related:
  - id: "zk-{domain}-{catseq}-{docseq}-{slug}"
    type: "引用 | 对比 | 上位法 | 补充 | 案例参考 | 同级"
freshness_months: 6
last_reviewed: YYYY-MM-DD
```

### 3.4 激活条件原则

**每个脚本、每个能力、每个协议都必须在 SKILL.md 中有显式触发条件。** 不写=不跑。

| 反例（挂机） | 正例（激活） |
|-------------|-------------|
| 创建 health_check.py | SKILL.md 写"每5次会话运行 health_check.py" |
| 创建 gen_report.py | SKILL.md 写"用户要求横向对比时运行 gen_report.py" |
| 写了 SOUL.md | SKILL.md 写"会话启动序列第1步加载 SOUL.md" |

## 四、实施流程

### Phase 1：骨架搭建

```
mkdir {skill-dir}
bootstrap_vault.py {skill-dir}
enhance_skillmd.py --update {skill-dir}
```

### Phase 2：核心文件编写

```
SKILL.md       # 12个协议章节（含全部激活条件）
SOUL.md        # 身份定义
TOOLS.md       # 工具偏好 + 分块策略 + 数据源
zk-categories.md  # 分类码映射表
```

### Phase 3：知识节点创建

**第1批 - 法规/理论（12-15节点）：** 核心知识框架
**第2批 - 操作流程（8-10节点）：** 分阶段实操流程
**第3批 - 对标/测算/经验（10-15节点）：** 数据、方法论、经验库

节点要包含 related 关系声明和 freshness_months 保鲜字段。

### Phase 4：模板 + 脚本

**模板（6个）：** 高频使用的结构化文档模板
**脚本（2个）：** 领域特定的数据处理/报告生成工具

### Phase 5：部署与验证

```
build_index.py {vault-path}
validate_vault.py {skill-dir}
verify 激活条件 - 检查每个组件是否在 SKILL.md 中有触发条件
```

## 五、初始知识节点规模标准

| 版本 | 知识节点 | 模板 | 脚本 | 激活条件 |
|------|:-------:|:----:|:----:|:--------:|
| v1 初始 | 30-40 | 6 | 2 | 每组件有触发 |
| v2 成熟 | 80-120 | 8-10 | 3-4 | +定时任务 |
| v3 完备 | 150+ | 10+ | 5+ | +自动蒸馏 |

## 六、检查清单

- [ ] 所有12个SKILL.md章节存在
- [ ] SOUL.md 在启动序列中被引用
- [ ] TOOLS.md 在工具偏好中被引用
- [ ] 每个增强技能有激活条件
- [ ] 每个脚本有触发场景描述
- [ ] 每个知识节点有 related 和 freshness_months
- [ ] journal 记录采用 `## [YYYY-MM-DD] operation | Title` 格式
- [ ] 跨KAM协作协议已配置
- [ ] build_index 成功运行
- [ ] validate_vault 无错误
- [ ] .learnings/ 目录已初始化
- [ ] WAL 协议已配置

## 七、必须从历史优化中采纳的项目

| 来源 | 优化项 | 采纳方式 |
|------|--------|---------|
| engineering-practices | 共享 vault 模式 | 评估是否需要共享知识库 |
| log_skill_call.py | 执行日志系统 | journal 统一前缀格式 |
| gh-fix-ci + KAM | 踩坑知识库 | 新增 ee0 分类码 |
| security-* + KAM | 合规红线知识库 | 建立合规检查清单模板 |
| yeet 工作流 | 标准化工作流编排 | 定义3-5个领域标准化工作流 |
| consolidate_learnings | 自改进闭环 | .learnings/ + WAL第5步 |

## 八、Karpathy llm-wiki 必须采纳的7项增强

| # | 增强项 | 实施方式 |
|:-|--------|---------|
| 1 | related 关系声明 | 每个节点 YAML 增加 related 字段 |
| 2 | 对话结晶协议 | SKILL.md 新增结晶协议章节 |
| 3 | Lint 协议 | SKILL.md 新增定期健康检查 |
| 4 | 知识保鲜周期 | SKILL.md 定义各分类审查频率 |
| 5 | 日志统一前缀 | `## [YYYY-MM-DD] operation | Title` |
| 6 | 大文档分块 | TOOLS.md 记录拆分规则 |
| 7 | Dataview 查询 | Obsidian Dataview 动态筛选 |
## 九、PowerShell 中文编码陷阱与对策

> 004 创建过程中消耗最多调试时间的坑，必须预先写入 SOP。

### 9.1 管道编码损坏：根因

PowerShell 管道（|）在传递含中文的文本时，会将中文字符静默替换为 ?（0x3F）。以下写法**全部失效**：

`powershell
# ❌ 失败：命令行管道到 python -c
python -c "print('中文')"

# ❌ 失败：here-string 管道到 Set-Content
@'中文'@ | Set-Content file.txt

# ❌ 失败：add-content / out-file 经过管道
'中文' | Out-File file.txt -Encoding UTF8
`

### 9.2 正确做法

| 场景 | 正确写法 | 原理 |
|------|---------|------|
| 写文件 | [System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new(False)) | .NET API 直接写，不经管道 |
| 写脚本 | [System.IO.File]::WriteAllLines(path, , [System.Text.UTF8Encoding]::new(False)) | 逐行数组写入 |
| 写 Python 脚本 | 先用 .NET API 写 .py 文件，再 python script.py | 不能 inline python -c |
| PowerShell 函数封装 | unction wf($rel, $content) { ... WriteAllText ... } | 传参用双引号字符串 |

### 9.3 批量创建 vault 文件的推荐模式

`powershell
# 在同一个 PowerShell 脚本中：
Add-Type -AssemblyName System.Text.Encoding
function wf($rel, $content) {
    $path = "$base\$rel"
    $dir = Split-Path $path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($path, $content.Trim() + "
", [System.Text.UTF8Encoding]::new($false))
}

# 每个文件独立调用，内容用双引号字符串 + 嵌入换行
wf "vault\knowledge\file.md" "---
title: 中文标题
---

正文内容..."
`

### 9.4 验证技巧

- 始终用 Python 读取文件字节验证：open(path, 'rb').read() 检查是否存在 UTF-8 多字节序列
- 批量验证：c.count('?') 配合 len(re.findall(r'[\u4e00-\u9fff]', c)) 交叉校验
- 不要在 PowerShell 终端 cat 文件看中文——显示问题不等于文件编码问题
