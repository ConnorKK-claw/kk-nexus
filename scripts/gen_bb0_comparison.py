#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_bb0_comparison.py — 11家上市公司股权激励横向对比报告"""
import os, sys, re, time
from pathlib import Path
from datetime import datetime, timedelta

try:
    import tushare as ts
    HAS_TUSHARE = True
except ImportError:
    HAS_TUSHARE = False

VAULT_DIR = Path(r"C:\Users\hexk\.codex\skills\equity-incentive\vault\knowledge")
OUTPUT_FILE = VAULT_DIR / "zk-ei-bb0-0-11-cases-comparison-report.md"

def safe(v, fmt=None):
    if v is None or (isinstance(v, str) and v.strip() in ("", "未收录", "—")):
        return "—"
    if fmt == "f2" and isinstance(v, (int, float)):
        return f"{v:.2f}"
    if fmt == "f1" and isinstance(v, (int, float)):
        return f"{v:.1f}"
    return str(v)

def safe_str(v):
    if v is None or (isinstance(v, str) and v.strip() in ("", "未收录")):
        return "—"
    return str(v)

def fetch_tushare_data(ts_code, draft_date):
    if not HAS_TUSHARE or not draft_date or "年" in str(draft_date):
        return None
    try:
        pro = ts.pro_api()
        dt = draft_date
        dt_obj = datetime.strptime(dt, "%Y-%m-%d")
        start = (dt_obj - timedelta(days=30)).strftime("%Y%m%d")
        end = (dt_obj + timedelta(days=30)).strftime("%Y%m%d")
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end, fields="trade_date,close,pct_chg")
        if df is None or df.empty:
            return None
        df = df.sort_values("trade_date").reset_index(drop=True)
        ann_date = dt_obj.strftime("%Y%m%d")
        mask = df["trade_date"] == ann_date
        ann_row = df[mask]
        if not ann_row.empty:
            ref_idx = ann_row.index[0]
            ann_chg = float(ann_row.iloc[0]["pct_chg"])
            ann_close = float(ann_row.iloc[0]["close"])
        else:
            after = df[df["trade_date"] > ann_date]
            if after.empty:
                return None
            ref_idx = after.index[0]
            ann_chg = float(after.iloc[0]["pct_chg"])
            ann_close = float(after.iloc[0]["close"])
        post1w_chg = None
        future_idx = ref_idx + 5
        if future_idx < len(df):
            close_ref = float(df.iloc[ref_idx]["close"])
            close_1w = float(df.iloc[future_idx]["close"])
            post1w_chg = round((close_1w - close_ref) / close_ref * 100, 2)
        return {"announce_chg_pct": ann_chg, "post1w_chg_pct": post1w_chg, "announce_price": ann_close}
    except Exception as e:
        print(f"[WARN] tushare error for {ts_code} ({draft_date}): {e}")
        return None

def fetch_current_prices():
    if not HAS_TUSHARE:
        print("[WARN] tushare unavailable, skipping current price fetch")
        return
    print("[INFO] 拉取当前股价计算浮盈...")
    pro = ts.pro_api()
    for c in COMPANIES:
        code = c["code"]
        gp = c.get("grant_price")
        cnt = c.get("incentive_count")
        shares = c.get("grant_shares_wan")
        if not gp or not cnt or not shares:
            continue
        try:
            df = pro.daily(ts_code=code, start_date="20260510", end_date="20260517", fields="trade_date,close")
            if df is not None and not df.empty:
                cp = float(df.iloc[0]["close"])
                fp = round((cp - gp) / gp * 100, 1)
                pp = round((cp - gp) * shares * 10000 / cnt / 10000, 1)
                c["current_float_pct"] = fp
                c["actual_per_person_profit"] = pp
                print(f"  [PRICE] {c['company']} ({c['plan_year']}{c['round']}): current={cp}, float={fp}%, pp={pp}wan")
            time.sleep(0.3)
        except Exception as e:
            print(f"  [WARN] price error for {c['company']} ({code}): {e}")

def fetch_unlock_prices():
    if not HAS_TUSHARE:
        return {}
    result = {}
    try:
        pro = ts.pro_api()
        for c in COMPANIES:
            batches = c.get("unlock_batches")
            if not batches:
                continue
            code = c["code"]
            gp = c["grant_price"]
            shares = c["grant_shares_wan"]
            cnt = c["incentive_count"]
            company_key = f"{c['company']} ({c['plan_year']}{c['round']})" if c['round'] else f"{c['company']} ({c['plan_year']})"
            batch_data = []
            for bd in batches:
                dt_obj = datetime.strptime(bd, "%Y-%m-%d")
                start_d = (dt_obj - timedelta(days=5)).strftime("%Y%m%d")
                end_d = (dt_obj + timedelta(days=5)).strftime("%Y%m%d")
                try:
                    df = pro.daily(ts_code=code, start_date=start_d, end_date=end_d, fields="trade_date,close")
                except Exception as e:
                    print(f"  [WARN] unlock rate limit for {company_key} {bd}: {e}")
                    time.sleep(2)
                    continue
                if df is not None and not df.empty:
                    df = df.sort_values("trade_date").reset_index(drop=True)
                    target = bd.replace("-", "")
                    match = df[df["trade_date"] == target]
                    if not match.empty:
                        price = float(match.iloc[0]["close"])
                    else:
                        after = df[df["trade_date"] > target]
                        price = float(after.iloc[0]["close"]) if not after.empty else None
                    if price:
                        fp = round((price - gp) / gp * 100, 1)
                        pp = round((price - gp) * shares * 10000 / cnt / 10000, 1)
                        batch_data.append({"date": bd, "price": price, "float_pct": fp, "pp_profit": pp})
                        print(f"  [UNLOCK] {company_key} {bd}: price={price}, float={fp}%, pp={pp}wan")
                time.sleep(0.5)
            if batch_data:
                result[company_key] = batch_data
    except Exception as e:
        print(f"[WARN] fetch_unlock_prices error: {e}")
    return result

COMPANIES = [
{"id":1,"company":"上海建科","code":"603153.SH","plan_year":"2025","round":"","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2025-12-16","grant_date":"2026-02-09","grant_price":11.50,"lockup_period":"24个月","unlock_schedule":"40% / 30% / 30%","validity":"最长6年","status":"刚授予，尚未解锁","employees_total":10454,"incentive_count":198,"incentive_pct":1.89,"grant_shares_wan":608.09,"grant_pct_total":1.484,"per_person_wan":3.07,"exec_get_pct":"—","unlock_structure":"40%/30%/30%","perf_targets":"EPS≥0.90/0.93/0.95元;净利增长≥8%/11%/14%;研发增长≥12%/19%/26%;均≥75分位","first_unlock_date":"2028-03-23（预计）","unlock_progress":"尚未解锁","canceled_shares":"—","announce_price_before":16.98,"announce_price":16.98,"announce_chg_pct":-0.82,"post1w_chg_pct":0.3,"grant_vs_announce_discount":67.7,"current_float_pct":33.3,"actual_per_person_profit":11.8,"pb_at_draft":1.9955,"notes":"不含董高"},
{"id":2,"company":"东方创业","code":"600278.SH","plan_year":"2021","round":"","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2021-11-30","grant_date":"2021-12-31","grant_price":3.95,"lockup_period":"24个月","unlock_schedule":"33% / 33% / 34%","validity":"最长约6年","status":"首批已解锁（首次+预留）","employees_total":6099,"incentive_count":275,"incentive_pct":4.51,"grant_shares_wan":1577.3,"grant_pct_total":1.79,"per_person_wan":5.74,"exec_get_pct":"—","unlock_structure":"33%/33%/34%","perf_targets":"EPS>=0.31/0.33/0.35元;净利增长>=57%/65%/75%(较2018-2020均值);东松公司净利>=12,800/13,000/14,000万","first_unlock_date":"2024-04-27","unlock_progress":"首批（首次）253人463.7万股完成;首批（预留）32人50.2万股完成;第二三批待解锁","canceled_shares":"有离职回购注销","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":1.5566,"notes":"含预留授予"},
{"id":3,"company":"国泰君安/国泰海通","code":"601211.SH","plan_year":"2020","round":"","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2020-06-08","grant_date":"2020-09-17","grant_price":7.64,"lockup_period":"24个月","unlock_schedule":"33% / 33% / 34%","validity":"最长约6年","status":"全生命周期已完成（首次+预留共4批全部解锁）","employees_total":15233,"incentive_count":451,"incentive_pct":2.96,"grant_shares_wan":8159.3,"grant_pct_total":0.916,"per_person_wan":18.09,"exec_get_pct":"—","unlock_structure":"33%/33%/34%","perf_targets":"营收复合增长≥8%+75分位;ROE≥9.0%/9.5%/10.0%+50分位;研发≥3%","first_unlock_date":"已完成（全部3+3批）","unlock_progress":"首次3批+预留3批全部完成解锁（含合并更名后）","canceled_shares":"有回购注销","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":1.2681,"notes":"2024年国泰君安吸收合并海通证券","unlock_batches":["2022-09-19","2023-09-18","2024-09-17"]},
{"id":4,"company":"华建集团","code":"600629.SH","plan_year":"2018","round":"第一轮","incentive_type":"限制性股票（第一类）","stock_source":"定向增发","draft_date":"2018-12-25","grant_date":"2019-03-20","grant_price":5.86,"lockup_period":"24个月","unlock_schedule":"36个月内分三期","validity":"最长5年","status":"全生命周期已完成","employees_total":6292,"incentive_count":379,"incentive_pct":6.02,"grant_shares_wan":1296.62,"grant_pct_total":"约3%","per_person_wan":3.82,"exec_get_pct":"—","unlock_structure":"36个月内分三期","perf_targets":"营收复合增长≥8%+75分位;ROE≥9.0%/9.5%/10.0%+50分位;研发≥3%","first_unlock_date":"2021-03-29","unlock_progress":"三期全部完成解锁+回购注销","canceled_shares":"多轮回购注销","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":4.9475,"notes":"2018年计划（完整周期）;员工6292人(2017末)","unlock_batches":["2021-03-29","2022-03-29","2023-03-29"]},
{"id":5,"company":"华建集团","code":"600629.SH","plan_year":"2022","round":"第二轮","incentive_type":"限制性股票（第一类）","stock_source":"定向增发","draft_date":"2022-01-29","grant_date":"2022-02-21","grant_price":3.19,"lockup_period":"24个月","unlock_schedule":"36个月内分三期","validity":"最长5年","status":"进行中（第一、二批已解锁/条件成就）","employees_total":8350,"incentive_count":102,"incentive_pct":1.22,"grant_shares_wan":2173.18,"grant_pct_total":3.43,"per_person_wan":21.95,"exec_get_pct":"—","unlock_structure":"36个月分三期","perf_targets":"归母净利润增长(门槛)+营收+ROE+研发费用增长;首批2022年调整后:净利≥62%(≥28,300万)/营收≥764,000万(设计咨询≥486,000万)/ROE≥8.5%/研发≥13%;二三批原方案:净利≥125%/132%/营收≥101亿/105亿/ROE≥10.6%/10.7%/研发≥44%/52%","first_unlock_date":"2024-03-02","unlock_progress":"第一批已完成(845.8万股);第二批条件已成就(98人);第三批待解锁","canceled_shares":"有回购注销;第一批条件曾被调整","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":1.3589,"notes":"从普惠型转向核心人才重奖型"},
{"id":6,"company":"华谊集团","code":"600623.SH","plan_year":"2020","round":"","incentive_type":"限制性股票（第一类）","stock_source":"定向增发","draft_date":"2020-11-25","grant_date":"2020-12-16","grant_price":3.85,"lockup_period":"36个月","unlock_schedule":"40% / 30% / 30%","validity":"最长6年","status":"全生命周期已完成（首次3批+预留2批已完成）","employees_total":12580,"incentive_count":258,"incentive_pct":2.05,"grant_shares_wan":516.8,"grant_pct_total":0.245,"per_person_wan":2.0,"exec_get_pct":"—","unlock_structure":"40%/30%/30%","perf_targets":"归母净利增长率+ROE+研发≥2.2%+老字号品牌增长≥3%(蜂花/回力)+安全环保(约束)","first_unlock_date":"2024-09-11","unlock_progress":"三期全部完成:首期272人487万股;二期完成;三期232人396.7万股","canceled_shares":"多轮回购注销","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":0.7342,"notes":"40%/30%/30%经典结构;含老字号品牌考核","unlock_batches":["2024-09-11","2025-03-11","2026-03-11"]},
{"id":7,"company":"锦江酒店","code":"600754.SH","plan_year":"2024","round":"","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2024-08-10","grant_date":"2024-10-11","grant_price":11.85,"lockup_period":"24个月","unlock_schedule":"三批（比例待首次解锁公告确认）","validity":"最长6年","status":"尚未解锁（2026-11-08预计首批解锁）","employees_total":30561,"incentive_count":148,"incentive_pct":0.48,"grant_shares_wan":647.7,"grant_pct_total":0.75,"per_person_wan":4.38,"exec_get_pct":"—","unlock_structure":"三批","perf_targets":"ROE≥5.8%/7%/8%+75分位;净利增长≥30%/65%/100%+75分位","first_unlock_date":"2026-11-08（预计）","unlock_progress":"尚未解锁;预留授予已完成(108人84.54万股)","canceled_shares":"首次回购已实施（2025-04-30）","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":1.5289,"notes":"含预留授予;首次+预留两轮授予"},
{"id":8,"company":"上港集团","code":"600018.SH","plan_year":"2021","round":"","incentive_type":"限制性股票（第一类）","stock_source":"定向增发","draft_date":"2021-04-24","grant_date":"2021-07-16","grant_price":2.21,"lockup_period":"36个月","unlock_schedule":"40% / 30% / 30%","validity":"最长6年","status":"首批+第二批已完成;第三批待解锁","employees_total":13796,"incentive_count":220,"incentive_pct":1.59,"grant_shares_wan":2508.46,"grant_pct_total":0.108,"per_person_wan":11.40,"exec_get_pct":"—","unlock_structure":"40%/30%/30%","perf_targets":"扣非加权ROE>=8.55%/8.60%/8.65%+行业均值;扣非净利复合增长>=4%/6%/8%(较2020);吞吐量(门槛)","first_unlock_date":"2024-08-27","unlock_progress":"首批(首次)206人4,090万股完成;第二批(首次)+首批(预留)完成;第三批待解锁","canceled_shares":"有回购注销","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":1.2765,"notes":"超大股本(231.7亿股)样本;预留授予成功执行"},
{"id":9,"company":"上海机场","code":"600009.SH","plan_year":"2024","round":"","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2024-05-14","grant_date":"2024-09-12","grant_price":18.22,"lockup_period":"24个月","unlock_schedule":"40% / 30% / 30%","validity":"最长不超过6年","status":"尚未解锁（2026-10-11预计首批解锁）","employees_total":12999,"incentive_count":289,"incentive_pct":2.22,"grant_shares_wan":826.25,"grant_pct_total":0.335,"per_person_wan":2.86,"exec_get_pct":2.1,"unlock_structure":"40%/30%/30%","perf_targets":"EPS≥0.71/0.84/0.98元;净利增长≥90%/125%/160%;主业毛利率≥19%/22.5%/26%","first_unlock_date":"2026-10-11（预计）","unlock_progress":"尚未解锁","canceled_shares":"有回购注销（2025-08-30）","announce_price_before":36.11,"announce_price":36.11,"announce_chg_pct":0.00,"post1w_chg_pct":-2.85,"grant_vs_announce_discount":50.5,"current_float_pct":43.1,"actual_per_person_profit":52.0,"pb_at_draft":2.3146,"notes":"289人覆盖2.2%员工;人均约2.86万股"},
{"id":10,"company":"外服控股","code":"600662.SH","plan_year":"2022","round":"","incentive_type":"限制性股票（第一类）","stock_source":"定向增发","draft_date":"2022-01-27","grant_date":"2022-03-16","grant_price":3.53,"lockup_period":"24个月","unlock_schedule":"33% / 33% / 34%","validity":"最长不超过6年","status":"首批+第二批均已解锁上市","employees_total":2998,"incentive_count":215,"incentive_pct":7.17,"grant_shares_wan":2007.08,"grant_pct_total":1.00,"per_person_wan":9.34,"exec_get_pct":"—","unlock_structure":"33%/33%/34%","perf_targets":"EPS>=0.230/0.253/0.290元;营收增长>=33%/52.9%/75.9%(较2020)+国际对标75分位;新兴业务收入>=100.60/116.70/135.37亿","first_unlock_date":"2024-12-06","unlock_progress":"首批(首次)209人650.3万股完成;首批(预留)16人29.8万股完成;第二批条件已成就","canceled_shares":"多轮回购注销（每次解锁均伴随）","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":4.5390,"notes":"解锁进度最深的案例"},
{"id":11,"company":"赢合科技","code":"300457.SZ","plan_year":"2017","round":"第一轮","incentive_type":"限制性股票（第一类）","stock_source":"定向增发","draft_date":"2017-10-24","grant_date":"2017-11-27","grant_price":17.05,"lockup_period":"12/24/36个月","unlock_schedule":"30% / 30% / 40%","validity":"最长5年","status":"全生命周期已完成","employees_total":2444,"incentive_count":73,"incentive_pct":2.99,"grant_shares_wan":488.5,"grant_pct_total":2.03,"per_person_wan":6.69,"exec_get_pct":"—","unlock_structure":"30%/30%/40%","perf_targets":"以2016年净利为基数:2017≥60%,2018≥140%,2019≥260%","first_unlock_date":"2018-12-11","unlock_progress":"首次3批+预留2批全部完成解锁","canceled_shares":"有预留机制（预留100万股）","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":19.6216,"notes":"民营→国有转型范例;含预留机制","unlock_batches":["2018-12-11","2019-12-23"]},
{"id":12,"company":"赢合科技","code":"300457.SZ","plan_year":"2022","round":"第二轮","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2022-11-12","grant_date":"2023-02-15","grant_price":10.68,"lockup_period":"24个月","unlock_schedule":"33% / 33% / 34%","validity":"最长5年","status":"第一、二批已解锁;第三批待解锁","employees_total":9421,"incentive_count":168,"incentive_pct":1.78,"grant_shares_wan":346.59,"grant_pct_total":0.535,"per_person_wan":2.06,"exec_get_pct":"—","unlock_structure":"33%/33%/34%","perf_targets":"营收增长≥35%/55%/75%;EPS≥0.60/0.66/0.72元;专利保有量≥1287/1470/1654项","first_unlock_date":"2025-03-27","unlock_progress":"第一批140人99.2万股完成;第二批136人94.5万股完成;第三批待解锁","canceled_shares":"计划738万→实际346.6万股(认购缩水53%)","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":2.5468,"notes":"认购缩水53%;含专利保有量考核"},
{"id":13,"company":"申能股份","code":"600642.SH","plan_year":"2021","round":"","incentive_type":"限制性股票（第一类）","stock_source":"二级市场回购","draft_date":"2021-01-26","grant_date":"2021-07-08","grant_price":2.89,"lockup_period":"24/36/48个月","unlock_schedule":"33% / 33% / 34%","validity":"最长不超过6年","status":"首批被取消,第二三批已完成","employees_total":2600,"incentive_count":289,"incentive_pct":11.12,"grant_shares_wan":4402.4,"grant_pct_total":0.96,"per_person_wan":15.23,"exec_get_pct":"—","unlock_structure":"33%/33%/34%","perf_targets":"ROE≥8.10%/8.20%/8.30%;净利增长≥16.1%/22.0%/28.2%(较2019);风电光伏装机≥80万kW/年","first_unlock_date":"2023-07-20（未达成）","unlock_progress":"第一批(33%)因业绩未达标全部取消(约1,510万股回购注销);第二批(33%)14,102,220股完成;第三批(34%)14,772,650股完成","canceled_shares":"第一批33%全部取消(约1,510万股)","announce_price_before":None,"announce_price":None,"announce_chg_pct":None,"post1w_chg_pct":None,"grant_vs_announce_discount":None,"current_float_pct":None,"actual_per_person_profit":None,"pb_at_draft":0.8495,"notes":"第一批因业绩未达标被取消（33%回购注销）;最低授予价格之一"},
]

def gen_overview():
    lines = [
        "## 公司概览",
        "",
        "| # | 公司 | 代码 | 计划年份 | 轮次 | 当前状态 |",
        "|:---:|:---|:---:|:---:|:---:|:---|",
    ]
    for c in COMPANIES:
        r = c.get("round", "") if c.get("round", "") else "—"
        lines.append(f"| {c['id']} | {c['company']} | {c['code']} | {c['plan_year']} | {r} | {c['status']} |")
    return "\n".join(lines)

def gen_table1():
    lines = [
        "## 表1：激励计划基本参数对比",
        "",
        "| 公司/计划 | 激励方式 | 股票来源 | 草案公告日 | 草案日PB | 授予日 | 授予价格(元/股) | 授予价/公告日市价比(%) | 锁定期 | 解锁安排 | 当前状态 |",
        "|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|",
    ]
    for c in COMPANIES:
        label = f"{c['company']} ({c['plan_year']}{c['round']})" if c.get('round') else f"{c['company']} ({c['plan_year']})"
        apb = c.get("announce_price_before")
        gp = c.get("grant_price")
        if apb and gp:
            discount = f"{gp/apb*100:.1f}%"
        else:
            discount = "—"
        pb = c.get("pb_at_draft")
        pb_str = f"{pb:.2f}" if pb else "—"
        lines.append(f"| {label} | {c['incentive_type']} | {safe(c['stock_source'])} | {safe(c['draft_date'])} | {pb_str} | {safe(c['grant_date'])} | {safe(c['grant_price'],'f2')} | {discount} | {safe(c['lockup_period'])} | {safe(c['unlock_schedule'])} | {c['status']} |")
    return "\n".join(lines) + "\n"

def gen_table2():
    lines = [
        "## 表2：激励范围与力度对比",
        "",
        "| 公司/计划 | 员工总数 | 激励人数 | 激励占比(%) | 授予总量(万股) | 占总股本比例(%) | 人均授予(万股) | 股票来源 |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|",
    ]
    for c in COMPANIES:
        label = f"{c['company']} ({c['plan_year']}{c['round']})" if c.get('round') else f"{c['company']} ({c['plan_year']})"
        lines.append(f"| {label} | {safe_str(c['employees_total'])} | {safe(c['incentive_count'])} | {safe_str(c['incentive_pct'])} | {c['grant_shares_wan']:.2f} | {safe_str(c['grant_pct_total'])} | {c['per_person_wan']:.2f} | {safe(c['stock_source'])} |")
    return "\n".join(lines) + "\n"

def gen_table3():
    lines = [
        "## 表3：解禁与业绩考核对比",
        "",
        "| 公司/计划 | 锁定期 | 解锁结构 | 业绩考核指标摘要 | 首批解锁时间 | 当前解锁进度 | 已取消/回购注销情况 |",
        "|:---|:---:|:---|:---|:---|:---|:---|",
    ]
    for c in COMPANIES:
        label = f"{c['company']} ({c['plan_year']}{c['round']})" if c.get('round') else f"{c['company']} ({c['plan_year']})"
        lines.append(f"| {label} | {safe(c['lockup_period'])} | {safe(c['unlock_structure'])} | {safe(c['perf_targets'])} | {safe(c['first_unlock_date'])} | {safe(c['unlock_progress'])} | {safe(c['canceled_shares'])} |")
    return "\n".join(lines) + "\n"

def gen_table4():
    lines = ["## 表4：市场反应与收益对比\n"]
    lines.append("> 股价数据通过 tushare 自动补全。\n\n")
    lines.append("| 公司/计划 | 公告前收盘价(元) | 公告日涨跌幅(%) | 公告后1周涨跌幅(%) | 授予价/公告前价比(%) | 当前浮盈率(%) | 实际人均收益(万元) |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for c in COMPANIES:
        label = f"{c['company']} ({c['plan_year']}{c['round']})" if c.get('round') else f"{c['company']} ({c['plan_year']})"
        apb = c.get("announce_price_before")
        gp = c.get("grant_price")
        ratio = f"{gp/apb*100:.1f}%" if apb and gp else "—"
        lines.append(f"| {label} | {safe(c['announce_price_before'],'f2')} | {safe(c['announce_chg_pct'],'f2')} | {safe(c['post1w_chg_pct'],'f2')} | {ratio} | {safe(c['current_float_pct'],'f1')} | {safe(c['actual_per_person_profit'],'f1')} |")
    return "\n".join(lines) + "\n"

def gen_table5(unlock_data):
    lines = ["## 表5：已完成计划各批解禁收益分析\n"]
    if not unlock_data:
        lines.append("> 无数据（仅对已完成的计划拉取解禁日股价）\n")
        return "\n".join(lines) + "\n"
    lines.append("| 公司/计划 | 批次 | 解禁日(条件成就) | 解禁日股价(元) | 较授予价涨幅(%) | 人均收益(万元) |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|")
    for company, batches in unlock_data.items():
        first = True
        for i, b in enumerate(batches):
            label = company if first else ""
            lines.append(f"| {label} | 第{i+1}批 | {b['date']} | {b['price']:.2f} | {b['float_pct']}% | {b['pp_profit']} |")
            first = False
    return "\n".join(lines) + "\n"

def main():
    print("[INFO] 开始生成对比报告...")
    fetch_current_prices()
    
    print("[INFO] tushare 可用，尝试拉取股价数据...")
    for c in COMPANIES:
        code = c["code"]
        dt = c["draft_date"]
        if c["announce_chg_pct"] is not None:
            continue
        if not dt or "年" in str(dt) or "月" in str(dt):
            print(f"  [SKIP] {c['company']} ({c['plan_year']}): 无精确草案公告日")
            continue
        result = fetch_tushare_data(code, dt)
        if result:
            if result["announce_chg_pct"] is not None:
                c["announce_chg_pct"] = round(result["announce_chg_pct"], 2)
            if result["post1w_chg_pct"] is not None:
                c["post1w_chg_pct"] = result["post1w_chg_pct"]
            if result["announce_price"] is not None:
                c["announce_price"] = result["announce_price"]
                c["announce_price_before"] = result["announce_price"]
                if c["grant_price"]:
                    c["grant_vs_announce_discount"] = round(c["grant_price"] / result["announce_price"] * 100, 1)
            print(f"  [OK] {c['company']}: 公告日涨跌幅={result['announce_chg_pct']}, 后1周={result['post1w_chg_pct']}")
            time.sleep(0.5)
        else:
            print(f"  [--] {c['company']}: 未获取到数据")
    
    unlock_data = fetch_unlock_prices()
    
    today = datetime.now().strftime("%Y-%m-%d")
    sections = []
    fm = f"""---
title: "11家上市公司股权激励横向对比报告"
date: {today}
source: distilled
original_source: agent
domain: equity-incentive
tags: [对比报告, 横向对比, 股权激励, 上市公司, cases, 上海国资]
status: distilled
---"""
    sections.append(fm)
    sections.append("\n# 11家上市公司股权激励横向对比报告\n")
    sections.append("本报告对 equity-incentive vault 中 **11家上市公司** 的股权激励计划进行横向对比。\n\n")
    sections.append("**范围：** 上海建科、东方创业、国泰君安(国泰海通)、华建集团(两轮)、华谊集团、锦江酒店、上港集团、上海机场、外服控股、赢合科技(两轮)、申能股份，共 **13条记录**。\n\n")
    sections.append("**对比维度：** 激励方式、激励范围、解禁安排、业绩考核、市场反应、实际收益。\n\n")
    sections.append("**数据来源：** vault/cases/ 下各公司蒸馏案例文件 + tushare 自动补全股价数据。部分数据因蒸馏环节未收录，标记为「—」。\n")
    sections.append(gen_overview())
    sections.append("")
    sections.append(gen_table1())
    sections.append(gen_table2())
    sections.append(gen_table3())
    sections.append(gen_table4())
    sections.append(gen_table5(unlock_data))
    sections.append("\n---\n")
    sections.append(f"\n**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    sections.append("**生成方式：** scripts/gen_bb0_comparison.py 自动生成\n")
    
    report = "\n".join(sections)
    os.makedirs(VAULT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[OK] 报告已生成: {OUTPUT_FILE}")
    print(f"     大小: {len(report)} 字符")
    print(f"     记录: {len(COMPANIES)} 条")

if __name__ == "__main__":
    main()
