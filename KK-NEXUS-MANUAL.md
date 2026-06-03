# KK Nexus (KNC) — 架构说明书

> **KK Nexus (Knowledge Nexus)** — 多层知识基础设施平台  
> 项目根：`C:\Users\hexk\OneDrive\文档\New project 6`  
> 版本：1.2.0 | 最后更新：2026-06-02  
> 简称：KNC / KK / Nexus

---

## 目录

1. [项目概览](#1-项目概览)
2. [架构全景](#2-架构全景)
3. [四层架构详解](#3-四层架构详解)
4. [环境与依赖](#4-环境与依赖)
5. [快速上手](#5-快速上手)
6. [日常运维](#6-日常运维)
7. [项目文件索引](#7-项目文件索引)

---

## 1. 项目概览

### 1.1 这是什么

KK Nexus 是一个**多层知识基础设施平台**，构建在 Codex AI 之上，为每个领域 skill 配备专属知识库（vault），并通过语义检索引擎、知识蒸馏流程和自动化运维形成**自循环的知识生态系统**。

### 1.2 解决什么问题

| 问题 | KK Nexus 的解法 |
|------|----------------|
| AI 会话无记忆 | vault 持久化存储 + WAL 协议跨会话衔接 |
| 知识碎片化 | 统一 YAML schema + Zettelkasten ID + 命名规范 |
| 知识过期 | 自动化健康检查 + 过期标记 + 冗余归档 |
| Web 内容无法沉淀 | 外部知识摄取流程（网页/公众号/视频→MD）| 
| 多 skill 知识孤岛 | UNIFIED_INDEX.md 统一索引 + 检索优先级协议 |
| 语义搜索精度低 | 四级检索链（语义→模糊→索引→全文）+ LLM 答案合成 |

---

## 2. 架构全景

### 2.1 四层架构

```
+----------------------------------------------------------------------+
| Layer 4: 应用交互层 (Application & Interaction)                      |
| Agent应答 + SKILL.md + WAL协议 + 自纠错机制                          |
|                                                                      |
| Layer 3: 检索合成层 (Retrieval & Synthesis)                          |
| 四级检索链(语义→模糊→索引→全文) + LLM合成                           |
|                                                                      |
| Layer 2: 知识加工层 (Knowledge Processing)                           |
| 蒸馏流程 + 质量控制 + 案例处理 + 索引                                |
|                                                                      |
| Layer 1: 素材沉淀层 (Material Collection)                            |
| 素材来源→导入管道→原始存储 + 外部知识库                              |
+----------------------------------------------------------------------+
```

### 2.2 数据流

```
外部素材(PDF/网页/公众号/视频)
    |
    | 素材导入(摄取/批量/自动)
    |
    ▼
原始存储(raw/) + 外部知识库(_wiki_ingest)
    |
    | 蒸馏(LLM蒸馏 / KAM转换)
    |
    ▼
知识库(knowledge/) + 案例库(cases/) + 模板(templates/)
    |
    | O(1)索引 + 向量索引导入
    |
    ▼
检索引擎(四级检索链)
    |
    | LLM答案合成
    |
    ▼
Agent应答(用户问题→解析需求→检索知识库→专业答案→输出方案)
    |
    | WAL协议：记录采集日志 + 蒸馏状态(反馈环)
    |
    ▼
日志与健康报告(驱动下一轮采集/蒸馏)
```

---

## 3. 四层架构详解

### 3.1 Layer 1：素材沉淀层

**职责：** 从多种渠道采集原始素材，转换为统一 Markdown 格式，存储为不可变原始文件。

| 要素 | 说明 |
|--------|--------|
| 素材来源 | 本地文件(PDF/DOCX/已有MD)，网页(URL)，公众号(搜索下载)，视频(YouTube)，自动采集(公告/文章) |
| 导入管道 | 格式转换(→MD)，批量下载(搜索→列表→采集)，URL抓取，视频转录 |
| 存储结构 | raw/user/(用户导入)，raw/agent/(自动采集)，raw/original/(原始备份) |
| 外部知识库 | _wiki_ingest/raw/(articles/notes/pdfs) + _wiki_ingest/wiki/(entities/topics/comparisons/synthesis) |

### 3.2 Layer 2：知识加工层

**职责：** 将原始素材蒸馏为结构化知识节点，建立索引，确保质量。

| 要素 | 说明 |
|--------|--------|
| 蒸馏流程 | raw/ → LLM蒸馏 → 知识节点(knowledge/) ；_wiki_ingest → KAM转换 → 结构化节点 |
| 质量控制 | 合规校验(命名/元数据/ZK-ID)，健康检查(过期/矛盾/缺失)，冗余归档(重复/过时) |
| 案例处理 | 时间线提取，缺失数据补全，对标分析生成 |
| 知识产出 | 知识库(法规/实务/案例/外部四大模块 + 精化节点) + 案例库 + 方案模板 + 索引文件 |
| 索引体系 | knowledge/index.md (O(1)全量索引) + zk-categories.md (分类码映射) + UNIFIED_INDEX.md (跨vault统一索引) |

### 3.3 Layer 3：检索合成层

**职责：** 提供多级检索链，从语义搜索到全文降级，组合 LLM 合成完整答案。

| 要素 | 说明 |
|--------|--------|
| ① 语义搜索 | 向量+关键词+图谱混合检索(本地持久化索引 + 离线CPU嵌入模型) |
| ② 模糊搜索 | 分词+TF-IDF+拼音模糊匹配，降级检索 |
| ③ 索引直达 | O(1)精确命中 knowledge/index.md |
| ④ 全文搜索 | 纯文本最后降级方案 |
| 答案合成 | LLM API 融合多源信息，补全缺口，输出完整专业答案 |
| MCP 服务 | 工具调用接口，Codex 自动调用检索引擎 |

**检索链路：**
```
用户问题→①语义搜索→(不满意)→②模糊搜索→(不满意)→③索引直达→(不满意)→④全文搜索→LLM合成答案
```

### 3.4 Layer 4：应用交互层

**职责：** Agent 执行应答、行为规范、自我优化，通过 WAL 协议实现跨会话连续性。

| 要素 | 说明 |
|--------|--------|
| 应答机制 | 用户问题→解析需求→检索知识库(四层检索链)→合成专业答案→输出方案/建议 |
| 行为规范 | AGENTS.md(全局规则)+SKILL.md(领域精通)+SOUL.md(身份)+USER.md(用户画像) |
| WAL 协议 | SESSION-STATE.md(任务状态) + memory/YYYY-MM-DD.md(决策记录) + MEMORY.md(长期记忆) + working-buffer.md(上下文溢出) |
| 自纠错 | 学习记录汇聚 + 主动优化 + 健康报告 |
| 反馈环 | WAL记录采集日志(→Layer 1) + 蒸馏状态(→Layer 2)，驱动下一轮循环 |

---

## 4. 环境与依赖

| 类别 | 依赖 | 用途 |
|--------|--------|--------|
| 运行时 | Codex CLI | Agent 应答 + 脚本执行 |
| 语义检索 | txtai + 嵌入模型(离线CPU) | 向量索引 + 混合检索 |
| LLM 合成 | LLM API | 答案合成 + RAG Gap 填补 |
| 文件转换 | Python 3.10+ | 素材摄取(→MD) |
| 网页采集 | Chrome CDP + 网络 | URL抓取/公众号下载 |
| 视频转录 | YouTube API | 视频录制→文本 |
| 工具调用 | MCP stdio | Codex → 检索引擎通道 |

---

## 5. 快速上手

### 5.1 初始化新 vault

1. 确认 AGENTS.md 存在且包含 Super KAM 规则
2. 运行 vault 初始化脚本(创建 8 个标准目录)
3. 创建 zk-categories.md(分类码映射表)
4. 将原始文件导入 raw/ 目录
5. 运行蒸馏流程：原始文件→知识节点(→knowledge/)
6. 重建索引(knowledge/index.md)
7. 创建或更新 UNIFIED_INDEX.md

### 5.2 导入素材

- **本地文件**: 运行素材摄取脚本(支持 PDF/DOCX/XLSX/Markdown)，自动转换→MD→raw/
- **公众号批量**: 指定公众号名称，搜索列表→确认→批量下载
- **单篇URL**: URL抓取工具，自动转换为 Markdown
- **YouTube**: 视频链接，提取字幕→MD

### 5.3 检索与咨询

- Agent 自动调用四级检索链，无需手动指定
- 可直接提问(如"股权激励方案设计要点")，Agent 自动检索并合成答案
- 查看 canvas：进入 vault/ 目录，用 Obsidian 打开 .canvas 文件

---

## 6. 日常运维

### 6.1 每日工作流

1. 会话启动：AGENTS.md→SOUL.md→USER.md→MEMORY.md→SESSION-STATE.md→UNIFIED_INDEX.md
2. 处理用户问题(自动检索知识库)
3. 会话结束(执行 WAL 协议)

### 6.2 定期任务

| 任务 | 频率 | 说明 |
|--------|--------|--------|
| 健康检查 | 每次会话结束 | 检查知识过期/矛盾/缺失蒸馏 |
| 索引重建 | vault变更后 | 更新 knowledge/index.md + UNIFIED_INDEX.md |
| 知识汇聚 | 每次会话结束 | consolidating learnings → MEMORY.md |
| 蒸馏状态检查 | 会话开始 | 检查未蒸馏原始文件，触发增量蒸馏 |

### 6.3 状态查看

- **知识节点状态**: knowledge/index.md（O(1)全量索引）
- **蒸馏状态**: .distilled.json 跟踪文件
- **健康报告**: 健康检查脚本输出
- **统一索引**: UNIFIED_INDEX.md

---

## 7. 项目文件索引

### 7.1 项目根目录

```
/ (项目根目录)
├── AGENTS.md              # Super KAM 全局规则(命名/元数据/检索协议/WAL)
├── SOUL.md                # Agent 身份
├── USER.md                # 用户画像
├── MEMORY.md              # 长期记忆
├── SESSION-STATE.md       # 会话状态(任务跟踪)
├── UNIFIED_INDEX.md       # 统一知识索引(自动生成)
├── KK-NEXUS-MANUAL.md     # ★ 本文档
├── scripts/               # 工具脚本(30+)
├── templates/             # SKILL.md 注入模板
├── memory/                # 会话日志(YYYY-MM-DD)
├── docs/                  # 辅助文档
├── logs/                  # 健康/心跳报告
├── .learnings/            # 学习记录
└── *.canvas               # 架构图
```

### 7.2 Skill vault 目录结构

```
vault/
├── raw/user/          # 用户导入的原始资料(不可变)
├── raw/agent/         # Agent 自动采集的原始资料
├── raw/original/      # 原始文件备份(PDF/DOCX等)
├── knowledge/         # 知识节点(Zettelkasten ID命名)
├── templates/         # 方案模板
├── cases/             # 案例(日期前缀)
├── journal/           # 操作日志(YYYY-MM-DD)
├── auto-update/       # 定时任务写入
└── _wiki_ingest/      # 外部知识库(网页/文章/视频)
    ├── raw/articles/     # 网页文章(原始)
    ├── raw/notes/        # 笔记(原始)
    ├── raw/pdfs/         # PDF(原始)
    ├── wiki/entities/    # 实体提取
    ├── wiki/topics/      # 专题汇总
    ├── wiki/sources/     # 来源摘要
    ├── wiki/comparisons/ # 对比分析
    ├── wiki/synthesis/   # 综合评述(+ sessions/)
    └── .distilled.json    # 蒸馏状态跟踪
```

### 7.3 关键文件

| 文件 | 说明 |
|--------|--------|
| AGENTS.md | Super KAM 全局规则(命名规范/元数据 schema/检索协议/WAL协议) |
| SKILL.md | 领域 skill 说明书(股权激励/税务/金融分析等) |
| knowledge/index.md | O(1)全量索引(自动生成) |
| zk-categories.md | 分类码映射表 |
| UNIFIED_INDEX.md | 跨vault统一索引 |
| KK Nexus Core-核心架构.canvas | 核心架构图(概念层) |
| KK Nexus Company-数据流向图.canvas | 数据流向图(逻辑层) |

---

> **KK Nexus v1.2.0** — 让你的 AI 拥有永不遗忘的领域知识。
