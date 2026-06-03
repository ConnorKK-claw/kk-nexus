# 工具偏好与数据源

## 文档处理
| 场景 | 首选工具 | 说明 |
|------|---------|------|
| PDF表格提取（激励对象分配表） | pdfplumber | 优于markitdown |
| 通用PDF转MD | markitdown | 适合非表格类PDF |
| DOCX转MD | markitdown | — |

## 数据源
| 类型 | 来源 | 工具 |
|------|------|------|
| A股历史股价 | tushare | fetch_market_data.py |
| 公司公告 | cninfo API | browser |
| 市场数据 | eastmoney API | browser |

## 大文档分块策略
- 激励计划公告：按"方案概要/授予明细/考核办法/法律意见"分块
- 年报：按"财务报表/附注/管理层讨论"分块
- 法规文件：按"章节/条款"分块（每块不超过50页）
