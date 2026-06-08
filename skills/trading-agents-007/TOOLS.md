# TOOLS — trading-agents-007（007号员工）

## 文档处理

| 场景 | 首选工具 | 说明 |
|------|---------|------|
| 网页文章转MD | baoyu-url-to-markdown | 公众号/新闻文章 |
| 通用文档转MD | markitdown | PDF/DOCX |

## 数据源优先级

| 优先级 | 数据类型 | 来源 | 状态 |
|--------|---------|------|------|
| 1 | K线/技术指标 | mootdx TCP 通达信 → sina HTTP fallback | ✅ |
| 2 | PE/PB/市值 | 腾讯 qt.gtimg.cn 实时 | ✅ |
| 3 | 财报三表 | 新浪 finance.sina.com.cn | ✅ |
| 4 | 北向资金/游资 | 东财 datacenter | ✅ |
| 5 | 解禁数据 | 东财 datacenter-web | ✅ |
| 6 | 新闻 | 新浪财经 | ✅ |
| 7 | 一致预期 | 同花顺 10jqka | ❌ HTML反爬 |
| 8 | 政策新闻 | 财联社 CLS | ❌ 空响应 |

## 依赖

| 依赖 | 安装方式 | 说明 |
|------|---------|------|
| tradingagents-astock (0.2.13) | pip install -e . | 核心引擎，位于 TradingAgents-astock/ |
| langgraph | pip | 图编排框架 |
| langchain-openai | pip | LLM 接口 |
| mootdx | pip | 通达信数据（TCP 7709 被封锁，降级 HTTP） |
| pandas | pip | 数据处理 |

## 检索优先级

1. vault/cases/ — 个股分析报告（直接读文件）
2. vault/memory/ — 操作日志
3. 委托 006 — 产业链卡点分析
4. 委托 005 — 宏观数据

## 已知问题

- DeepSeek API 限流：约 40 次/10 分钟，全量分析约需 40+ 次调用，连续分析多只股票需间隔 5-10 分钟
- mootdx TCP 7709：公司网络封锁，自动降级到 sina HTTP（不影响核心数据）
- 东财 push2：反爬检测，偶发被拒（不影响核心数据）
- 同花顺共识预期：返回 GBK HTML，解析失败
- CLS 政策新闻 API：返回空响应
- PowerShell 传递中文参数可能乱码，优先用 Python 写文件执行
- BOM 污染：全部脚本用 encoding=utf-8
