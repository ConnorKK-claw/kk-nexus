# 工具偏好与数据源

## 文档处理
| 场景 | 首选工具 | 说明 |
|------|---------|------|
| PDF表格提取（激励对象分配表） | pdfplumber | 优于markitdown |
| 通用PDF转MD | markitdown | 适合非表格类PDF |
| DOCX转MD | markitdown | — |

## 数据源

| 数据类型 | 首选来源 | 备选 | 工具 |
|---------|---------|------|------|
| A股历史股价 | tushare | eastmoney API | fetch_market_data.py |
| A股实时行情 | eastmoney API | — | browser |
| 公司公告全文 | cninfo API | 公司官网 | browser |
| 股权激励公告模板 | cninfo 特定格式 | 巨潮资讯 | browser |

## 大文档分块策略
- 激励计划公告：按"方案概要/授予明细/考核办法/法律意见"分块
- 年报：按"财务报表/附注/管理层讨论"分块
- 法规文件：按"章节/条款"分块（每块不超过50页）

## 已知问题

- PowerShell 传递中文参数可能乱码，优先用 Python 写文件执行
- 系统代理可能阻塞数据 API（如 tushare），需在 Python 中清除 HTTP_PROXY 环境变量
- markitdown 对部分复杂 DOCX 格式转换可能失败，降级到 pdfplumber
- BOM 污染：PowerShell Out-File 默认带 UTF-8 BOM，全部脚本用 encoding="utf-8"（不含 BOM）