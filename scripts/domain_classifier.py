#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""domain_classifier.py - 多标签分类引擎。

识别文本内容所属的领域（domain），支持多标签输出。
先从关键词规则引擎匹配，充不住时可用 LLM 辅助。
"""

import re
from typing import List


# 关键词 → domain 映射表
# 第三个可选元素为 dict，支持
# - and_groups: list[list[str]] — 每组内 OR，组间 AND（仅 hk-ipo 使用）
DOMAIN_PATTERNS: list[tuple] = [
    # 001 - 股权激励：仅限于“股权激励”和“员工持股”两个精确词
    ("ei",       "股权激励",       ["股权激励", "员工持股"]),

    # 002 - 税务合规
    ("tax",      "税务合规",       ["税务", "发票", "凭证", "个税", "企业所得税", "增值税",
                                   "合规审计", "纳税申报", "汇算清缴", "抵扣", "税前扣除"]),

    # 004 - 港股 IPO：必须同时命中港股组 AND 上市组
    ("hk-domain",   "港股 IPO",      [],
        {"and_groups": [
            ["港股", "港交所", "香港联交所", "恒生", "香港交易所", "恒生指数"],
            ["上市", "IPO", "首次公开发行", "招股书", "聆讯", "红筹", "VIE架构"],
        ]}),

    # 005 - 宏观经济分析
    ("fa",       "宏观经济分析",   ["宏观经济", "宏观", "GDP", "CPI", "PPI", "货币政策", "央行",
                                   "降息", "降准", "通货膨胀", "通货紧缩", "PMI",
                                   "财政政策", "社融", "M2", "LPR",
                                   "国联民生", "外贸", "通胀", "经济数据", "经济分析"]),

#     # 007 - 交易策略
#     ("trading",  "交易策略",       ["交易策略", "K线", "量化交易", "量化策略", "量化回测",
#                                    "回测", "技术指标", "RSI", "均线", "布林带", "止损", "止盈",
#                                    "买卖信号", "仓位管理", "多空", "趋势跟踪"]),

    # 003 - 周报
    ("wr",       "周报",          ["周报", "周刊", "weekly report", "证券周报",
                                    "市场周报", "行情回顾"]),

    # 006 - A股AI半导体产业链
    ("serenity", "产业链分析",     ["AI", "人工智能", "半导体", "芯片", "算力", "大模型",
                                   "AI产业链", "半导体产业链", "卡点", "瓶颈", "设备材料",
                                   "先进封装", "封测", "光通信", "EDA工具",
                                   "功率半导体", "服务器", "存储", "互联芯片"]),

    
    # 在此添加你的自定义 domain...
    # 008 - IMA 知识库
    ("ima",      "IMA知识库",       ["IMA平台", "ima知识库", "知识库网关"]),
]


def classify_text(text: str) -> list[str]:
    """多标签分类：返回文本匹配的所有 domain 列表。

    规则：
    - 默认 OR 匹配：任一关键词命中即算匹配
    - hk-ipo 使用 AND 匹配：各组内任一命中 OR，组间 AND
    - RSI 使用词边界匹配
    """
    if not text or not text.strip():
        return ["general"]

    text_lower = text.lower()
    matched: list[str] = []

    for entry in DOMAIN_PATTERNS:
        domain = entry[0]
        keywords = entry[2]
        config = entry[3] if len(entry) > 3 else {}

        # AND 组匹配（如 hk-ipo：必须同时命中港股 AND 上市）
        if "and_groups" in config:
            all_groups_match = True
            for group in config["and_groups"]:
                group_match = False
                for kw in group:
                    if kw.lower() in text_lower:
                        group_match = True
                        break
                if not group_match:
                    all_groups_match = False
                    break
            if all_groups_match:
                matched.append(domain)
            continue

        # 标准 OR 匹配
        for kw in keywords:
            # RSI 需要词边界（避免 match persistent 里的 rsi）
            if kw == "RSI":
                if re.search(r'(?<![a-zA-Z])RSI(?![a-zA-Z])', text):
                    if domain not in matched:
                        matched.append(domain)
                    break
            elif kw.lower() in text_lower:
                if domain not in matched:
                    matched.append(domain)
                break

    if not matched:
        matched = ["general"]

    return matched


def get_domain_label(domain: str) -> str:
    """返回 domain 的中文标签。"""
    labels = {
        "wr": "周报",
        "ima": "IMA知识库",
        "ei": "股权激励",
        "tax": "税务合规",
        "hk-domain": "港股 IPO",
        "fa": "宏观经济分析",
        "trading": "交易策略",
        "serenity": "产业链分析",
        "zhangjiang": "张江高科",
        "general": "通用知识",
    }
    return labels.get(domain, domain)


def check_vault_targets() -> dict[str, str]:
    """快速检查所有目标 vault 路径是否存在，返回 domain→状态字典。"""
    from config import DOMAIN_VAULT_MAP
    from pathlib import Path
    result = {}
    for domain, path in DOMAIN_VAULT_MAP.items():
        p = Path(path)
        result[domain] = "OK" if p.is_dir() else f"MISSING: {p}"
    return result


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read()
    domains = classify_text(text)
    print("\n".join(domains))



