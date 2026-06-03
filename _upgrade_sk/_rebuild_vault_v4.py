# -*- coding: utf-8 -*-
from pathlib import Path

base = Path.home() / '.codex' / 'skills' / 'hk-ipo'
vault = base / 'vault'
today = '2026-05-25'

def w(rel, c):
    p = base / rel if not rel.startswith('vault') else vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(c.strip() + '\n', encoding='utf-8')
    n = sum(1 for ch in c if ord(ch) > 127)
    print(f'  {rel}: {len(c.encode(\"utf-8\"))}b, {n} cn')

w('zk-categories.md', '---\ntitle: ZK 分类码映射表 - hk-ipo\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [元数据, 分类]\nstatus: verified\n---\n\n# ZK 分类码映射表\n\naa0: 法规框架(证监会/联交所/国资委/外管局/行业监管)\nbb0: 操作实务(重组/路径/中介/尽调/招股书/聆讯/定价/上市后合规)\ncc0: 可比公司(A+H国资/A+H科技/纯H股对标/行业对标)\ndd0: 财务测算(募资/估值/摊薄/市值/达标/募资用途)\nee0: 实操经验(问询函应对/否决案例/时间延误/中介配合)\ngg0: 蒸馏知识')

# AA0
w('vault/knowledge/zk-hk-ipo-aa0-0-csrc-overseas-listing.md', '---\ntitle: 境内企业境外发行证券和上市管理试行办法\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, H股, IPO]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# 境内企业境外发行证券和上市管理试行办法\n\n2023年3月31日起施行。境内企业直接/间接境外上市均需向证监会备案。覆盖H股直接、红筹架构、A-to-H三种路径。')
w('vault/knowledge/zk-hk-ipo-aa0-1-hkex-main-board-listing-rules.md', '---\ntitle: 联交所主板上市规则(第8/19/19A章)\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, H股, IPO]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# 联交所主板上市规则(第8/19/19A章)\n\n第8章基本上市条件。第19章中国发行人特别规定。第19A章持续责任。市值至少5亿港元，公众持股至少25%。')
w('vault/knowledge/zk-hk-ipo-aa0-2-sasac-h-share-state-owned-equity.md', '---\ntitle: H股国有股权管理\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 国有股权]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# H股国有股权管理\n\n36号令上市公司国有股权监督管理办法。国有股东标识管理、国有股减持转持、审批流程。')
w('vault/knowledge/zk-hk-ipo-aa0-3-safe-foreign-exchange.md', '---\ntitle: 外汇管理与资金跨境\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 外汇]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# 外汇管理与资金跨境\n\nH股募集资金调回/留存、外汇登记、股息汇出。A-to-H特殊外汇安排。')
w('vault/knowledge/zk-hk-ipo-aa0-4-industry-specific-regulation.md', '---\ntitle: 行业监管特殊要求\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 行业监管]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# 行业监管特殊要求\n\n金融/地产/科技互联网各行业特殊监管要求。网络安全审查、数据出境、外商投资准入。')
w('vault/knowledge/zk-hk-ipo-aa0-5-a-share-ipo-framework.md', '---\ntitle: A股IPO法律法规框架\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, A股, IPO]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# A股IPO法律法规框架\n\n证券法、注册管理办法。注册制下交易所审核+证监会注册。审核周期6-12个月。')
w('vault/knowledge/zk-hk-ipo-aa0-6-a-to-h-listing-rules.md', '---\ntitle: A-to-H双重上市与第二上市规则\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, A-to-H]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# A-to-H双重上市与第二上市规则\n\n双重上市须同时满足两地规则。第二上市联交所监管较宽松。A股企业H股上市优势。')
w('vault/knowledge/zk-hk-ipo-aa0-7-h-share-full-circulation.md', '---\ntitle: H股全流通机制\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 全流通]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# H股全流通机制\n\n内资股转H股。流程：申请到备案到审批到转换到上市。国有股特殊规定。')
w('vault/knowledge/zk-hk-ipo-aa0-8-hkex-continuous-obligations.md', '---\ntitle: 联交所上市后持续责任\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 持续责任]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# 联交所上市后持续责任\n\n信息披露、须予公布的交易、关联交易管理、ESG报告。年报4个月内、中报3个月内。')
w('vault/knowledge/zk-hk-ipo-aa0-9-dual-listing-comparison.md', '---\ntitle: A股与H股IPO规则对比\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 对比]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# A股与H股IPO规则对比\n\nA股注册制6-12月。H股双重备案4-8月。A-to-H 3-6月。H股承销费较高但审核更灵活。')
w('vault/knowledge/zk-hk-ipo-aa0-10-red-chip-structure.md', '---\ntitle: 红筹架构法律框架\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 红筹]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# 红筹架构法律框架\n\n境外控股公司上市。10号文、37号文、外商投资负面清单。国企采用红筹受限。')
w('vault/knowledge/zk-hk-ipo-aa0-11-a-share-equity-refinancing.md', '---\ntitle: A股再融资规则框架\ndate: 2026-05-25\nsource: agent\ndomain: hk-ipo\ntags: [法规, 再融资]\nstatus: verified\nfreshness_months: 6\nlast_reviewed: 2026-05-25\n---\n\n# A股再融资规则框架\n\n增发/配股/可转债。注册制下审核简化。H股配售更灵活。')

print('Done writing AA0 (12 nodes)')