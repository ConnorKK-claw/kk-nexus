# TOOLS -- serenity-a-share-investor(006号员工)

## 文档处理

| 场景 | 首选工具 | 说明 |
|------|---------|------|
| PDF报表提取 | pdfplumber | 优于markitdown，适合表格 |
| 通用PDF转MD | markitdown | 非表格类PDF |
| DOCX转MD | markitdown | -- |
| 网页文章转MD | baoyu-url-to-markdown | 公众号/新闻文章 |

## 数据源优先级

| 优先级 | 证据类型 | 来源 | 证据等级 |
|--------|---------|------|---------|
| 1 | 公告/财报 | 年报/半年报/季报/临时公告/交易所问询函 | L1 |
| 2 | 交易所互动 | 互动易(深交所)/上证e互动(上交所) | L1 |
| 3 | 官方项目数据 | 招投标/环评能评/地方项目备案 | L2 |
| 4 | 贸易数据 | 海关进出口数据/设备招标公告 | L2 |
| 5 | 第三方研究 | 券商研报/行业期刊/专利数据库 | L3 |
| 6 | 专利数据 | 国家知识产权局/USPTO | L3 |
| 7 | 媒体线索 | 可信行业媒体/官方公众号 | L4 |

## 检索优先级

1. txtai语义检索 -- 向量搜索+RAG合成(最优先)
2. UNIFIED_INDEX.md -- O(1)判断结果位置
3. vault/knowledge/index.md -- 精准知识索引
4. 跨员工vault检索 -- 005 fa(宏观数据)/001 ei(政策法规)
5. obsidian-cli模糊搜索 -- 分词+TF-IDF+拼音(需安装)
6. Select-String全文搜索 -- PowerShell纯文本降级

## 已知问题

- PowerShell传递中文参数可能乱码，优先用Python写文件执行
- 系统代理可能阻塞数据API，需在Python中清除HTTP_PROXY环境变量
- markitdown对部分复杂DOCX格式转换可能失败，降级到pdfplumber
- BOM污染：PowerShell Out-File默认带UTF-8 BOM，全部脚本用encoding=utf-8
- txtai沙箱外执行(Torch DLL限制)，需full-access模式
