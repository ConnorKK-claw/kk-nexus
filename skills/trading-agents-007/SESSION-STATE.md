# SESSION-STATE: 007 trading-agents 初始化

## 本轮完成 (2026-06-08)

### ✅ 员工创建
- 007号员工入职
- 目录结构：SKILL.md / SOUL.md / TOOLS.md / scripts/run_007.py / vault/{cases,raw,memory}
- 006 协作协议已更新

### ✅ Agent prompt 修改
- 技术分析字数限制：≤2000字
- 基本面字数限制：已恢复为不限
- 辩论轮次：max_debate_rounds=5, max_risk_discuss_rounds=5

### ✅ 运行验证
- 600519 茅台：7-agent分析通过，Action=Hold
- 600895 张江高科：报告已生成

### ❌ 已知数据源问题
- mootdx TCP 7709 端口被封锁 -> 降级 sina HTTP
- 东财 push2 反爬 -> 部分接口被拒（不影响核心数据）
- 同花顺共识预期 -> 返回 HTML 无法解析
- 财联社 CLS API -> 空响应

## 下一步
1. 006 数据管道集成：在 006 脚本中加 import tradingagents.dataflows 作为 fallback
2. 旧报告清理：比亚迪旧 CN 格式 -> 用 007 重跑
3. 007 定时任务：每日收盘后自动跑股票池

## 关键决策
- 007 以 deepseek-chat 模型运行
- 数据链路：核心数据（K线/PE/PB）来自 腾讯+Sina
- 辩论 5 轮 + 风险讨论 5 轮
