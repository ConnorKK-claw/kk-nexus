# Super KAM 006 号员工部署与操作 SOP

> 归档日期：2026-06-05
> 归档人：Agent (serenity-a-share-investor)
> 状态：固化完成

---

## 一、006 号员工档案

| 项目 | 内容 |
|------|------|
| 编号 | 006 |
| 名称 | serenity-a-share-investor（A股AI半导体产业链研究）|
| 角色 | 采用Serenity/@aleabitoreddit式供应链瓶颈分析法，专注A股AI半导体全产业链投资研究 |
| Domain | asi |
| Skill路径 | `~/.codex/skills/serenity-a-share-investor/` |
| Vault路径 | `~/.codex/skills/serenity-a-share-investor/vault/` |
| 底层Skills | serenity-skill / serenity-method / serenity-chokepoint-investor / serenity-radar / follow-aleabito |
| 聚焦方向 | A股AI半导体全产业链（GPU/ASIC/存储互连/设备/材料/先进封测/光通信/电力上游）|
| 知识节点数 | 1个（zk-categories.md）|
| 案例数 | 0（待填充）|
| 模板数 | 0（待填充）|---

## 二、架构概览

006 是一个 orchestrator skill，将 5 个底层 Serenity 系 skill 编排为统一的 4 阶段研究流水线。

```
用户提问
    |
    v
Phase 1: 候选发现   <- serenity-radar (GENERATOR 模式)
    |                  + serenity-chokepoint-investor (thesis-ledger 参考)
    v
Phase 2: 产业链研究  <- serenity-skill (完整 9 步工作流)
    |                  + A 股专用证据源路径
    v
Phase 3: 个股质检    <- serenity-method (5 步法)
    |                  + serenity-chokepoint-investor (0-5 打分 + Anti-Parrot)
    v
Phase 4: 结构化输出  <- serenity-chokepoint-investor (中文模板)
                       + serenity-method (研究地图 vs 可投资结论)
```
## 三、底层 Skills 分工

| Skill | 来源 | 角色 | 激活条件 |
|-------|------|------|---------|
| serenity-skill | muxuuu/serenity-skill | Phase 2 研究引擎：产业链拆解、9步工作流、A股数据源路径 | Phase 2 开始时加载；单公司挑战时跳过Phase 1直接加载 |
| serenity-method | lanfuli/aleabito-serenity-skills | Phase 3 质检方法：5步法、第一性原理、Buffett质量门 | Phase 3 开始时加载 |
| serenity-chokepoint-investor | Yao990x16/serenity-chokepoint-investor | Phase 1/3/4 知识库+打分+模板：thesis-ledger、0-5打分校准、输出模板 | Phase 1/3/4 按需加载 |
| serenity-radar | lanfuli/aleabito-serenity-skills | Phase 1 信号逻辑：GENERATOR三模式（往上游/往早/往小）| 主题扫描模式时 Phase 1 加载 |
| follow-aleabito | lanfuli/aleabito-serenity-skills | 可选数据源：追踪 @aleabitoreddit 的 X 动态 | 用户明确要求跟踪 AleaBito 时加载 |

## 四、触发路由

### 4.1 主题扫描

当用户请求涉及产业链扫描、主题研究、候选发现时：

1. **Phase 1**：用 serenity-radar 的 GENERATOR 三模式在 A 股语境中识别候选卡点层
2. **Phase 2**：加载 serenity-skill 完整 9 步工作流，使用 A 股专用证据源路径
3. **Phase 3**：对每个候选执行 serenity-method 5 步法 + 0-5 打分
4. **Phase 4**：输出结构化中文备忘录

### 4.2 单公司挑战

当用户直接提到具体 A 股公司时：
- 跳跃 Phase 1
- 从 Phase 2 开始：定位公司在产业链中的位置
- Phase 3：完整 5 步质检 + 打分
- Phase 4：输出

### 4.3 压力测试

当用户输入含单边叙事关键词（最明显赢家/轻松翻倍/准备重仓等）时自动激活：
- 钩子：一句话打断最弱假设
- 反身性检查：区分基本面 vs 社交媒体驱动的涨幅
- 原始论点拆解：把用户叙事拆成可验证 claim

### 4.4 学习模式

当用户请求学习方法时：
- 进入 serenity-method 对话协议模式
- 每次只问一个问题
- 从大趋势拆到供应链卡点和证据
## 五、硬规则（Anti-Parrot 自检）

每次输出前必须执行以下 7 条自检，任一条失败即整份输出不通过：

1. 只说 AI 需求强，没有说明谁卡住谁 -> 失败
2. 只选最显眼的赢家，没有沿供应链往上找稀缺输入 -> 失败
3. 只复述 ticker，没有重建当前标的的约束链 -> 失败
4. 只看收入增长，没有检查毛利、backlog 质量、capex、现金流和稀释 -> 失败
5. 只说长期空间大，没有说明财务弹性和失效条件 -> 失败
6. 没有声明使用的最新财报/公告/电话会日期，却给出当前结论 -> 失败
7. 没有把公司标注为 demand beneficiary / integrator-conduit / constraint controller -> 失败

## 六、证据纪律

| 等级 | 描述 | 来源 | 使用规则 |
|------|------|------|---------|
| L1 | 官方披露 | 年报/半年报/季报/临时公告/交易所问询函 | 唯一可升级Buffett质量门字段的证据 |
| L2 | 政府/监管数据 | 招投标公告/环评能评/地方项目备案/海关进出口 | 可作为交叉验证 |
| L3 | 第三方专业分析 | 券商研报/行业期刊/专利数据库 | 辅助参考，不单独作为结论依据 |
| L4 | 媒体/公开信息 | 行业媒体/官方公众号/产业会议 | 线索级，不构成决策证据 |

- Buffett 质量门字段（护城河/盈利能力/客户替换风险）默认 unverified
- 新候选默认分类 研究地图，不可直接跳到 可投资结论
- Serenity 帖子=Serenity 观点证据，不是公司事实证据
- 所有输出末尾强制标注：仅作信息跟踪，不构成投资建议。
## 七、分类码映射表

Domain 代码：asi（A-share AI semiconductor investor）

| 分类码 | 分类名 | 说明 |
|--------|--------|------|
| aa | 产业链卡点 | 供应链瓶颈/卡点层识别 |
| bb | 公司分析 | 个股基本面/估值/竞争格局 |
| cc | 设备材料 | 半导体设备/材料/耗材 |
| dd | 封装测试 | 先进封装/HBM/测试 |
| ee | 光通信 | CPO/硅光/激光器/光模块 |
| ff | EDA/IP | 设计工具/IP授权/设计服务 |
| gg | 政策地缘 | 出口管制/国产替代/产业政策 |
| hh | 宏观映射 | 资本开支周期/需求趋势/景气度 |

知识节点命名：`zk-asi-{catseq}-{docseq}-{title}.md`

## 八、Vault 目录结构

```
vault/
  raw/user/          # 用户导入的原始资料
  raw/agent/         # Agent 导入的原始资料
  raw/original/      # 原始文件备份
  knowledge/         # 精化知识节点
    zk-categories.md  # 分类码映射表
  cases/             # 案例/参考
  templates/         # 方案模板
  journal/           # 操作日志
  auto-update/       # 定时任务写入
  memory/            # 会话记忆
```

## 九、跨员工协作矩阵

| 场景 | 委托员工 | 说明 |
|------|---------|------|
| 宏观数据/货币政策分析 | 005 (financial-analysis) | 获取宏观视角 |
| 股权激励方案分析 | 001 (equity-incentive) | 涉及公司治理 |
| 税务合规审查 | 002 (tax-compliance-expert) | 税务相关 |
| 港股IPO | 004 (hk-ipo) | 港股相关 |
| 证券周报生成 | 003 (weekly-report) | 定期报告 |

## 十、已知问题与限制

- 非实时行情工具：不做盘口分析、技术面、买卖点
- 证据依赖：每个结论标注了证据等级，L4 不会与 L1 混为一谈
- 默认标签：研究地图，非买入建议
- 底层 Skill 不修改：orchestrator 只调用，不修改底层 SKILL.md
- 聚焦范围：超出 A 股 AI 半导体产业链范围回退 serenity-skill 通用工作流
- 电力上游方向为额外关注方向（服务器电源/功率半导体/液冷散热）
