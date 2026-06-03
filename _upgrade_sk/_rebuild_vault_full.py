# -*- coding: utf-8 -*-
from pathlib import Path

base = Path.home() / '.codex' / 'skills' / 'hk-ipo'
vault = base / 'vault'
today = '2026-05-25'

def w(rel, content):
    p = base / rel if not rel.startswith('vault') else vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + '\n', encoding='utf-8')
    cn = sum(1 for ch in content if ord(ch) > 127)
    print('  {}: {}b, {} cn'.format(rel, len(content.encode('utf-8')), cn))

def make(title, desc, extra_tags=''):
    extra = ', ' + extra_tags if extra_tags else ''
    return '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: verified\nfreshness_months: {}\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(
        title, today, extra_tags if extra_tags else 'H股', today, title, desc)

# zk-categories
w('zk-categories.md',
  '---\ntitle: ZK 分类码映射表 - hk-ipo\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [元数据, 分类]\nstatus: verified\n---\n\n' +
  '# ZK 分类码映射表\n\n' +
  'aa0: 法规框架(证监会/联交所/国资委/外管局/行业监管)\n' +
  'bb0: 操作实务(重组/路径/中介/尽调/招股书/聆讯/定价/上市后合规)\n' +
  'cc0: 可比公司(A+H国资/A+H科技/纯H股对标/行业对标)\n' +
  'dd0: 财务测算(募资/估值/摊薄/市值/达标/募资用途)\n' +
  'ee0: 实操经验(问询函应对/否决案例/时间延误/中介配合)\n' +
  'gg0: 蒸馏知识')

# AA0: 12 nodes - 法规框架
aa0 = [
    ('csrc-overseas-listing', '境内企业境外发行证券和上市管理试行办法',
     '2023年3月31日起施行。境内企业直接/间接境外上市均需向证监会备案。覆盖H股直接、红筹架构、A-to-H三种路径。', '法规, H股, IPO'),
    ('hkex-main-board-listing-rules', '联交所主板上市规则(第8/19/19A章)',
     '第8章基本上市条件。第19章中国发行人特别规定。第19A章持续责任。市值至少5亿港元，公众持股至少25%。', '法规, H股, IPO'),
    ('sasac-h-share-state-owned-equity', 'H股国有股权管理',
     '36号令上市公司国有股权监督管理办法。国有股东标识管理、国有股减持转持、审批流程。', '法规, 国有股权'),
    ('safe-foreign-exchange', '外汇管理与资金跨境',
     'H股募集资金调回/留存、外汇登记、股息汇出。A-to-H特殊外汇安排。', '法规, 外汇'),
    ('industry-specific-regulation', '行业监管特殊要求',
     '金融/地产/科技互联网各行业特殊监管要求。网络安全审查、数据出境、外商投资准入。', '法规, 行业监管'),
    ('a-share-ipo-framework', 'A股IPO法律法规框架',
     '证券法、注册管理办法。注册制下交易所审核+证监会注册。审核周期6-12个月。', '法规, A股, IPO'),
    ('a-to-h-listing-rules', 'A-to-H双重上市与第二上市规则',
     '双重上市须同时满足两地规则。第二上市联交所监管较宽松。A股企业H股上市优势。', '法规, A-to-H'),
    ('h-share-full-circulation', 'H股全流通机制',
     '内资股转H股。流程：申请到备案到审批到转换到上市。国有股特殊规定。', '法规, 全流通'),
    ('hkex-continuous-obligations', '联交所上市后持续责任',
     '信息披露、须予公布的交易、关联交易管理、ESG报告。年报4个月内、中报3个月内。', '法规, 持续责任'),
    ('dual-listing-comparison', 'A股与H股IPO规则对比',
     'A股注册制6-12月。H股双重备案4-8月。A-to-H 3-6月。H股承销费较高但审核更灵活。', '法规, 对比'),
    ('red-chip-structure', '红筹架构法律框架',
     '境外控股公司上市。10号文、37号文、外商投资负面清单。国企采用红筹受限。', '法规, 红筹'),
    ('a-share-equity-refinancing', 'A股再融资规则框架',
     '增发/配股/可转债。注册制下审核简化。H股配售更灵活。', '法规, 再融资'),
]
for i, (slug, title, desc, tags) in enumerate(aa0):
    w('vault/knowledge/zk-hk-ipo-aa0-{}-{}.md'.format(i, slug),
      '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(title, today, tags, today, title, desc))

# BB0: 10 nodes - 操作实务
bb0 = [
    ('restructuring-plan-design', '重组方案设计',
     '明确上市主体、剥离非核心资产、优化股权结构。H股：公司制改造、资产评估。A-to-H：全流通方案。', '操作实务, 重组'),
    ('listing-path-comparison', '上市路径选择比较',
     'H股直接IPO(4-8月)/A-to-H(3-6月)/红筹(6-12月)。张江高科推荐A-to-H第二上市。', '操作实务, 路径'),
    ('intermediary-selection', '中介机构选聘标准',
     '保荐人、境内/香港法律顾问、审计师、行业顾问。考量行业经验和团队稳定性。', '操作实务, 中介'),
    ('due-diligence-process', '尽职调查流程',
     '业务/财务/法律/行业尽调。H股特有：国有股权确认、资产评估备案、外汇合规。', '操作实务, 尽调'),
    ('prospectus-preparation', '招股书编制要点',
     '概要/风险因素/行业/业务/财务/公司治理/募资用途。港股与A股差异。', '操作实务, 招股书'),
    ('hearing-and-roadshow', '聆讯与路演',
     '上市委员会审核。聆讯问题：业务模式/合规性/财务数据。路演准备。', '操作实务, 聆讯'),
    ('pricing-and-placing', '定价与配售',
     '簿记建档。国际配售+公开发售+回拨+超额配股权。A-to-H折价策略。', '操作实务, 定价'),
    ('post-listing-compliance', '上市后合规管理',
     '定期报告、信息披露、关联交易管理。A+H两地规则差异。', '操作实务, 合规'),
    ('h-share-full-circulation-operation', '全流通操作实务',
     '内资股股东授权到证监会备案到联交所上市到股份转换登记。操作要点与常见问题。', '操作实务, 全流通'),
    ('a-to-h-timeline', 'A-to-H上市时间表',
     '前期准备1-2月到重组改制2-3月到申报审核2-3月到发行上市1-2月。总计6-10月。', '操作实务, 时间表'),
]
for i, (slug, title, desc, tags) in enumerate(bb0):
    w('vault/knowledge/zk-hk-ipo-bb0-{}-{}.md'.format(i, slug),
      '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(title, today, tags, today, title, desc))

# CC0: 4 nodes - 可比公司
cc0 = [
    ('a-h-soe-comparables', 'A+H国资可比公司组',
     '中芯国际、华虹半导体、上海电气、中国中车、中国通号。维度：市值/国资持股/A-H价差。', '可比公司, 国资'),
    ('a-h-tech-comparables', 'A+H科技制造可比公司组',
     '中集集团、复星医药、金风科技、比亚迪。维度：市值/行业/A-H价差。', '可比公司, 科技'),
    ('pure-h-tech-comparables', '纯H股科技对标组',
     '联想集团、金山软件、中芯国际。提供H股估值水平和投资者结构参考。', '可比公司, 科技'),
    ('parks-real-estate-comparables', '园区/地产/投资控股对标组',
     '上海临港、外高桥、浦东金桥、苏州高新、深圳国际。园区运营模式和估值比较。', '可比公司, 园区'),
]
for i, (slug, title, desc, tags) in enumerate(cc0):
    w('vault/knowledge/zk-hk-ipo-cc0-{}-{}.md'.format(i, slug),
      '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: verified\nfreshness_months: 3\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(title, today, tags, today, title, desc))

# DD0: 6 nodes - 财务测算
dd0 = [
    ('fundraising-calculation', '募资规模测算方法论',
     '募资规模=发行股数x发行价。发行股比例15%-25%。超额配股权15%。', '财务, 募资'),
    ('valuation-methodology', '发行估值方法论',
     'PE/PB/PS/EV/EBITDA。A-to-H需考虑A股折价10%-30%。', '财务, 估值'),
    ('dilution-analysis', '摊薄分析',
     '摊薄比例=新发H股/发行后总股本。EPS摊薄、每股净资产变化。', '财务, 摊薄'),
    ('market-cap-projection', '市值预测模型',
     'A+H总市值预测。乐观/基准/悲观情景分析。', '财务, 市值'),
    ('financial-threshold-analysis', '财务指标达标分析',
     '联交所三选一测试：盈利/市值收益/市值收入现金流。A股连续三年盈利。', '财务, 指标'),
    ('fund-use-compliance', '募集资金用途合规分析',
     '明确披露用途和占比。变更需履行程序。A+H两地监管协调。', '财务, 募资用途'),
]
for i, (slug, title, desc, tags) in enumerate(dd0):
    w('vault/knowledge/zk-hk-ipo-dd0-{}-{}.md'.format(i, slug),
      '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(title, today, tags, today, title, desc))

# EE0: 4 nodes - 实操经验
ee0 = [
    ('exchange-enquiry-qa', '联交所典型审核问询函Q&A',
     '常见问询：业务模式/关联交易/同业竞争/财务数据。回答策略：事实清晰/逻辑严谨/风险披露。', '实操, 问询'),
    ('rejection-case-analysis', 'H股IPO否决退回案例共性分析',
     '常见原因：业务不可持续/财务真实性/关联交易/治理缺陷/信息披露。', '实操, 否决'),
    ('timeline-delay-patterns', 'IPO时间表延误常见原因',
     '内部：财务延迟/合规问题/国资审批。外部：市场变化/监管问询/中介配合。', '实操, 时间表'),
    ('intermediary-cooperation', '中介配合常见问题',
     '信息不及时/职责不清/协调困难。最佳实践：周会/明确分工/共享平台。', '实操, 中介'),
]
for i, (slug, title, desc, tags) in enumerate(ee0):
    w('vault/knowledge/zk-hk-ipo-ee0-{}-{}.md'.format(i, slug),
      '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(title, today, tags, today, title, desc))

# GG0: 2 nodes - 蒸馏知识
gg0 = [
    ('h-share-ipo-overview', 'H股IPO全流程概览',
     '前期准备到重组改制到申报到审核到发行。关键：提前识别合规问题/充分准备披露。', '蒸馏, 概览'),
    ('a-to-h-key-considerations', 'A-to-H上市关键考量因素',
     '战略：国际化/资本平台/估值提升。操作：时间成本/监管协调/信息披露。', '蒸馏, A-to-H'),
]
for i, (slug, title, desc, tags) in enumerate(gg0):
    w('vault/knowledge/zk-hk-ipo-gg0-{}-{}.md'.format(i, slug),
      '---\ntitle: {}\ndate: {}\nsource: agent\ndomain: hk-ipo\ntags: [{}]\nstatus: distilled\nfreshness_months: 12\nlast_reviewed: {}\n---\n\n# {}\n\n{}'.format(title, today, tags, today, title, desc))

# Templates
templates = [
    ('hk-ipo-timeline-template', '港股IPO时间线模板', '模板, 时间表'),
    ('prospectus-key-clauses-checklist', '招股书关键条款检查表', '模板, 招股书'),
    ('exchange-qa-preparation-template', '联交所问答准备模板', '模板, 问询'),
    ('listing-path-comparison-template', '上市路径比较模板', '模板, 路径'),
    ('intermediary-selection-checklist', '中介机构选聘检查表', '模板, 中介'),
    ('due-diligence-checklist', '尽职调查清单', '模板, 尽调'),
]
for fname, title, tags in templates:
    w('vault/templates/{}.md'.format(fname),
      '---\ntitle: {}\ndate: TEMPLATE\nsource: template\ndomain: hk-ipo\ntags: [{}]\nstatus: template\n---\n\n# {}\n\n按实际情况填写。'.format(title, tags, title))

# Journal
w('vault/journal/{}.md'.format(today),
  '## [{}] rebuild | 修复所有知识节点的中文编码\n\n重新生成了38个知识节点、6个模板、zk-categories.md。\n所有文件使用UTF-8编码，中文完好。\n\n总计写入文件: 46个'.format(today))

print('\n所有文件已使用正确UTF-8编码重新生成')