#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
005 financial-analysis — AKShare 宏观数据管道
从 AKShare 拉取中国经济数据并生成 knowledge 节点。

使用方法：
    python fetch_macro_data_005.py              # 拉取所有数据
    python fetch_macro_data_005.py --list        # 列出可拉取的数据集
    python fetch_macro_data_005.py --only cpi    # 仅拉取指定数据集

依赖：pip install akshare pandas
"""

import os, sys, textwrap, time, json
from datetime import datetime

import pandas as pd
from scripts import config

# ============================================================
# 配置
# ============================================================
VAULT_KNOWLEDGE_DIR = config.FA_VAULT_KNOWLEDGE
AUTHOR = "AKShare 宏观数据管道"
DOMAIN = "financial-analysis"

# ============================================================
# 数据集注册表
# ============================================================
DATASETS = []

def register(name, category, seq, fn, desc, tags, update_strategy="replace"):
    """注册一个数据集"""
    DATASETS.append({
        "name": name,
        "category": category,
        "seq": seq,
        "fn": fn,
        "desc": desc,
        "tags": tags,
        "update_strategy": update_strategy,
    })

# ---------- 中国宏观 ----------
register("china-cpi", "cc0", 16,
    lambda: __import__("akshare").macro_china_cpi_yearly(),
    "中国CPI年率历史数据（1986-今）", ["中国CPI", "通胀", "macrod_cpi"])

register("china-ppi", "cc0", 17,
    lambda: __import__("akshare").macro_china_ppi_yearly(),
    "中国PPI年率历史数据（1995-今）", ["中国PPI", "通胀", "macrod_ppi"])

register("china-pmi", "cc0", 18,
    lambda: __import__("akshare").macro_china_pmi_yearly(),
    "中国官方制造业PMI历史数据（2005-今）", ["中国PMI", "制造业", "macrod_pmi"])

register("china-industrial-output", "cc0", 19,
    lambda: __import__("akshare").macro_china_industrial_production_yoy(),
    "中国工业增加值同比增速历史数据", ["中国工业", "经济增长", "macrod_industrial"])

register("china-money-supply", "bb0", 11,
    lambda: __import__("akshare").macro_china_money_supply(),
    "中国货币供应量M2历史数据（2008-今）", ["中国M2", "货币政策", "macrod_m2"])

register("china-lpr", "bb0", 12,
    lambda: __import__("akshare").macro_china_lpr(),
    "中国LPR贷款市场报价利率历史数据（2013-今）", ["中国LPR", "利率", "macrod_lpr"])

register("china-gdp", "ee0", 6,
    lambda: __import__("akshare").macro_china_gdp_yearly(),
    "中国GDP同比增速历史数据（季度）", ["中国GDP", "经济增长", "macrod_gdp"])

# ---------- 美国/美联储 ----------
register("fed-interest-rate", "bb0", 13,
    lambda: __import__("akshare").macro_bank_usa_interest_rate(),
    "美联储基准利率历史数据（294行，覆盖多轮加息降息周期）", ["美联储", "利率", "macrod_fed"])

register("us-core-pce", "bb0", 14,
    lambda: __import__("akshare").macro_usa_core_pce_price(),
    "美国核心PCE物价指数历史数据（670行，美联储首选通胀指标）", ["美国PCE", "通胀", "macrod_pce"])

register("us-nonfarm", "ff0", 9,
    lambda: __import__("akshare").macro_usa_non_farm(),
    "美国非农就业人数历史数据（669行，关键就业指标）", ["美国非农", "就业", "macrod_nonfarm"])

register("us-unemployment", "ff0", 10,
    lambda: __import__("akshare").macro_usa_unemployment_rate(),
    "美国失业率历史数据（669行）", ["美国失业率", "就业", "macrod_unemployment"])

register("us-ism-pmi", "ff0", 11,
    lambda: __import__("akshare").macro_usa_ism_pmi(),
    "美国ISM制造业PMI历史数据（671行）", ["美国ISM", "PMI", "制造业", "macrod_ism"])

register("us-cpi", "ff0", 12,
    lambda: __import__("akshare").macro_usa_cpi_monthly(),
    "美国CPI月率历史数据（669行）", ["美国CPI", "通胀", "macrod_us_cpi"])

# ---------- 全球 ----------
register("euro-cpi", "bb0", 15,
    lambda: __import__("akshare").macro_euro_cpi_yoy(),
    "欧元区CPI同比历史数据", ["欧元区CPI", "通胀", "macrod_euro"])

register("japan-cpi-rate", "bb0", 16,
    lambda: None,  # 复合数据集，手动处理
    "日本CPI和央行利率历史数据", ["日本CPI", "日本利率", "macrod_japan"])

register("bdi-index", "ff0", 13,
    lambda: __import__("akshare").macro_shipping_bdi(),
    "波罗的海干散货指数BDI历史数据（全球航运/贸易先行指标）", ["BDI", "航运", "贸易", "macrod_bdi"])

register("semi-index", "ff0", 14,
    lambda: __import__("akshare").macro_global_sox_index(),
    "全球半导体SOX指数历史数据（科技周期先行指标）", ["SOX", "半导体", "科技周期", "macrod_sox"])


def make_node_id(category, seq):
    return "zk-fa-{cat}-{seq}".format(cat=category, seq=seq)


def summarize_df(df, max_rows=5):
    """生成DataFrame的文字摘要"""
    if df is None or len(df) == 0:
        return "无数据"
    lines = []
    cols = list(df.columns)
    lines.append("列: " + ", ".join(cols))
    lines.append("总行数: %d" % len(df))

    # 日期范围
    date_cols = [c for c in cols if "日期" in c or "date" in c.lower() or "时间" in c or "月份" in c]
    if date_cols:
        dc = date_cols[0]
        try:
            lines.append("时间范围: %s ~ %s" % (df[dc].iloc[0], df[dc].iloc[-1]))
        except:
            pass

    # 最新值（取最后一行非空数值）
    val_cols = [c for c in cols if c not in date_cols and c not in ["商品", "TRADE_DATE"]]
    if val_cols:
        lines.append("\n最新数据:")
        last = df.iloc[-1]
        for vc in val_cols[:4]:
            try:
                val = last[vc]
                if pd.notna(val):
                    lines.append("  %s: %s" % (vc, val))
            except:
                pass

    # 历史趋势摘要
    if val_cols:
        vc = val_cols[0]
        try:
            vals = df[vc].dropna()
            if len(vals) > 0:
                lines.append("\n历史趋势:")
                lines.append("  最小值: %.2f" % float(vals.min()))
                lines.append("  最大值: %.2f" % float(vals.max()))
                lines.append("  平均值: %.2f" % float(vals.mean()))
                lines.append("  最近10期: %s" % ", ".join(["%.1f" % float(x) for x in vals.tail(10)]))
        except:
            pass

    return "\n".join(lines)


def generate_node(ds, df):
    """生成知识节点内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    node_id = make_node_id(ds["category"], ds["seq"])
    title = ds["desc"]
    tags_str = ", ".join(ds["tags"])

    summary = summarize_df(df)
    
    # 数据质量评估
    quality_notes = []
    if df is not None:
        quality_notes.append("- 数据来源: AKShare（东方财富/华尔街见闻等公开数据聚合）")
        quality_notes.append("- 数据频度: 月度/季度")
        quality_notes.append("- 总行数: %d" % len(df))
        empty_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
        quality_notes.append("- 缺失率: %.1f%%" % empty_pct)
        if empty_pct > 20:
            quality_notes.append("- ⚠️ 缺失率较高，部分最新数据点可能尚未发布")

    content = """---
title: "{title}"
id: {node_id}
date: {today}
source: agent
domain: {domain}
tags: [{tags_str}, macrod_auto]
author: "{author}"
status: verified
update_frequency: monthly
last_fetched: {today}
data_source: AKShare
---

# {title}

## 数据摘要

{summary}

## 数据质量

{quality}

## 使用说明

- 此节点由 AKShare 宏观数据管道自动生成
- 运行 python scripts/fetch_macro_data_005.py --only {ds_name} 可刷新
- 数据延迟约 1-2 个月（官方发布滞后）
- 与本 skill 中分析师解读文章（如陶川/林彦/钟渝梅的公众号文章）配合使用效果最佳
""".format(
        title=title,
        node_id=node_id,
        today=today,
        domain=DOMAIN,
        tags_str=tags_str,
        author=AUTHOR,
        summary=summary,
        quality="\n".join(quality_notes) if quality_notes else "无",
        ds_name=ds["name"],
    )

    return content, node_id


def fetch_dataset(ds):
    """拉取单个数据集，返回 DataFrame"""
    name = ds["name"]
    if name == "japan-cpi-rate":
        # 复合数据集：日本CPI + 利率
        ak = __import__("akshare")
        cpi = ak.macro_japan_cpi_yearly()
        rate = ak.macro_japan_bank_rate()
        # 合并为单一结构用于摘要
        combined = pd.DataFrame({
            "cpi_date": cpi["日期"] if "日期" in cpi.columns else [""],
            "cpi_value": cpi["今值"] if "今值" in cpi.columns else [],
            "rate_date": rate["日期"] if "日期" in rate.columns else [""],
            "rate_value": rate["今值"] if "今值" in rate.columns else [],
        })
        return combined
    
    fn = ds["fn"]
    if fn is None:
        return None
    try:
        return fn()
    except Exception as e:
        print("  ❌ %s: %s" % (name, str(e)[:100]))
        return None


def write_node(node_id, content):
    """写入 knowledge 目录"""
    fname = "%s-%s.md" % (node_id, node_id.split("-")[-1])
    # 用数据集名称为后缀
    for ds in DATASETS:
        test_id = make_node_id(ds["category"], ds["seq"])
        if test_id == node_id:
            fname = "%s-%s.md" % (node_id, ds["name"])
            break
    fpath = os.path.join(VAULT_KNOWLEDGE_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("  ✅ 写入: %s" % fname)
    return fpath


def main():
    print("=" * 60)
    print("  005 AKShare 宏观数据管道")
    print("  %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)

    # 解析参数
    only_names = []
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        if idx + 1 < len(sys.argv):
            only_names = [sys.argv[idx + 1]]
    if "--list" in sys.argv:
        print("\n可用数据集:")
        for ds in DATASETS:
            node_id = make_node_id(ds["category"], ds["seq"])
            print("  %-25s → %s" % (ds["name"], node_id))
        return

    os.makedirs(VAULT_KNOWLEDGE_DIR, exist_ok=True)

    results = []
    for ds in DATASETS:
        if only_names and ds["name"] not in only_names:
            continue

        print("\n[%s] %s..." % (make_node_id(ds["category"], ds["seq"]), ds["desc"]))
        
        t0 = time.time()
        df = fetch_dataset(ds)
        elapsed = time.time() - t0
        
        if df is None or (isinstance(df, pd.DataFrame) and len(df) == 0):
            print("  ⚠️ 无数据返回 (%.1fs)" % elapsed)
            continue
        
        content, node_id = generate_node(ds, df)
        fpath = write_node(node_id, content)
        results.append((ds["name"], node_id, len(df)))

    # 汇总
    print("\n" + "=" * 60)
    print("  拉取完成: %d / %d 数据集" % (len(results), len(DATASETS)))
    for name, node_id, rows in results:
        print("  ✅ %-25s %s (%d行)" % (name, node_id, rows))
    print("=" * 60)


if __name__ == "__main__":
    main()
