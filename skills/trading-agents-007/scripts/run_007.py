"""007号员工 CLI — 触发多agent个股分析。

用法:
  python scripts/run_007.py --code 002594 --name "比亚迪"
  python scripts/run_007.py --code 600895 --name "张江高科" --date 2026-06-08
  python scripts/run_007.py --code 600519 --name "贵州茅台" --employee 005
  python scripts/run_007.py --list           # 列出当日已缓存报告
"""
import os, sys, argparse, datetime, json, shutil

sys.stdout.reconfigure(encoding="utf-8")

# ── 路径 ──
SKILL_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_CASES = os.path.join(SKILL_HOME, "vault", "cases")
VAULT_MEMORY = os.path.join(SKILL_HOME, "vault", "memory")
VAULT_JOURNAL = os.path.join(SKILL_HOME, "vault", "journal")
EMPLOYEES_PATH = os.path.join(SKILL_HOME, "EMPLOYEES.json")
ASTOCK_HOME = os.path.join(os.path.dirname(SKILL_HOME), "..", "..", "..", "OneDrive", "文档", "New project 7", "TradingAgents-astock")

# 确保 vault 目录存在
os.makedirs(VAULT_CASES, exist_ok=True)
os.makedirs(VAULT_MEMORY, exist_ok=True)
os.makedirs(VAULT_JOURNAL, exist_ok=True)

# DeepSeek API key
os.environ["DEEPSEEK_API_KEY"] = "YOUR_DEEPSEEK_API_KEY"

# ── 员工 vault 映射 ──
def load_employees():
    """从 EMPLOYEES.json 加载员工编号 → skill 目录映射。"""
    if os.path.exists(EMPLOYEES_PATH):
        with open(EMPLOYEES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def resolve_employee_vault(emp_id):
    """根据员工编号返回 vault/cases/ 路径。不存在则返回 None。"""
    employees = load_employees()
    if emp_id not in employees:
        print(f"[007] ⚠️ 未知员工编号: {emp_id}，请在 EMPLOYEES.json 中添加")
        return None
    skill_name = employees[emp_id]["skill"]
    vault_path = os.path.join(os.path.dirname(SKILL_HOME), skill_name, "vault", "cases")
    if not os.path.exists(vault_path):
        print(f"[007] ⚠️ 员工 {emp_id} ({skill_name}) 的 vault/cases/ 目录不存在，跳过分发")
        return None
    return vault_path

# ── 报告文件命名 ──
def build_report_filename(code, name, date_str):
    """按 AGENTS.md 规范生成文件名: YYYY-MM-DD-{公司}-7agent多空辩论分析-007.md"""
    safe_name = name.replace("（", "(").replace("）", ")").replace(" ", "")
    return f"{date_str}-{safe_name}-7agent多空辩论分析-007.md"

def get_report_path(code, name, date_str):
    filename = build_report_filename(code, name, date_str)
    return os.path.join(VAULT_CASES, filename)

def list_cached_reports():
    """列出当日已缓存的报告。"""
    today = datetime.date.today().isoformat()
    if not os.path.exists(VAULT_CASES):
        print("(vault/cases 目录为空)")
        return
    found = 0
    for f in sorted(os.listdir(VAULT_CASES)):
        if not f.endswith(".md") or f == ".gitkeep":
            continue
        path = os.path.join(VAULT_CASES, f)
        mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
        if mod_date == today:
            size = os.path.getsize(path)
            print(f"  {f}  ({size/1024:.0f} KB)")
            found += 1
    if found == 0:
        print("(当日无缓存报告)")

def write_journal(date_str, name, code, employee_id=None):
    """写一条操作日志到 vault/journal/{date}.md"""
    path = os.path.join(VAULT_JOURNAL, f"{date_str}.md")
    entry = f"- [007] {datetime.datetime.now().strftime('%H:%M')} 生成 {name}({code}) 个股分析报告"
    if employee_id:
        entry += f" → 已分发至员工 {employee_id}"
    entry += "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)

def run_analysis(code, name, date_str=None, employee_id=None):
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    
    report_path = get_report_path(code, name, date_str)
    
    # 缓存检查
    if os.path.exists(report_path):
        size = os.path.getsize(report_path)
        print(f"[007] 缓存命中: {os.path.basename(report_path)} ({size/1024:.0f} KB)")
        return report_path
    
    print(f"[007] 开始分析 {name}({code}) / {date_str}...")
    print(f"[007] 预计耗时 5-15 分钟...")
    
    # 动态添加 astock 路径
    astock_path = os.path.abspath(ASTOCK_HOME)
    if os.path.exists(astock_path):
        sys.path.insert(0, astock_path)
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
    except ImportError:
        print("[007] 错误: tradingagents 包未安装。请先: cd TradingAgents-astock && pip install -e .")
        sys.exit(1)
    
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "deepseek"
    config["deep_think_llm"] = "deepseek-chat"
    config["quick_think_llm"] = "deepseek-chat"
    config["backend_url"] = "https://api.deepseek.com/v1"
    config["output_language"] = "Chinese"
    config["max_debate_rounds"] = 3
    config["max_risk_discuss_rounds"] = 3
    config["checkpoint_enabled"] = True
    
    ta = TradingAgentsGraph(debug=False, config=config)
    final_state, decision = ta.propagate(code, date_str)
    
    if not isinstance(final_state, dict):
        final_state = {}
    
    action = decision if isinstance(decision, str) else "Hold"
    
    # ── 组装报告 ──
    def safe_str(val):
        if val is None: return ""
        return str(val)
    
    lines = []
    lines.append(f"# {name}（{code}）个股分析报告")
    lines.append("")
    lines.append(f"**生成日期**: {date_str}")
    lines.append(f"**生成时间**: {datetime.datetime.now().strftime('%H:%M')}")
    lines.append(f"**数据源**: mootdx + 腾讯 + 新浪 + 同花顺 + 东财")
    lines.append(f"**生成员工**: 007" + (f" | 委托员工: {employee_id}" if employee_id else ""))
    lines.append("")
    
    # 1. 决策概览
    lines.append("## 1. 决策概览")
    lines.append("")
    lines.append(f"**操作建议**: {action}")
    lines.append("")
    lines.append("**最终交易决策**:")
    lines.append(f"> {safe_str(final_state.get('final_trade_decision', 'N/A'))}")
    lines.append("")
    lines.append("**交易员决策**:")
    lines.append(f"> {safe_str(final_state.get('trader_investment_decision', 'N/A'))}")
    lines.append("")
    lines.append("---")
    
    # 2. 技术分析
    lines.append("## 2. 技术分析摘要")
    lines.append("")
    lines.append(safe_str(final_state.get("market_report", "N/A")))
    lines.append("")
    lines.append("---")
    
    # 3. 基本面分析
    lines.append("## 3. 基本面分析")
    lines.append("")
    lines.append(safe_str(final_state.get("fundamentals_report", "N/A")))
    lines.append("")
    lines.append("---")
    
    # 4. 多空辩论
    lines.append("## 4. 多空辩论")
    lines.append("")
    debate_state = final_state.get("investment_debate_state", {})
    if isinstance(debate_state, dict):
        bull_raw = safe_str(debate_state.get("bull_history", ""))
        bear_raw = safe_str(debate_state.get("bear_history", ""))
        judge = safe_str(debate_state.get("judge_decision", ""))
        
        import re
        bull_rounds = re.split(r"\n(?=Bull Analyst:)", bull_raw)
        bear_rounds = re.split(r"\n(?=Bear Analyst:)", bear_raw)
        bull_rounds = [r for r in bull_rounds if r.strip()]
        bear_rounds = [r for r in bear_rounds if r.strip()]
        max_rounds = max(len(bull_rounds), len(bear_rounds))
        
        for i in range(max_rounds):
            lines.append(f"### 第 {i+1} 轮辩论")
            lines.append("")
            if i < len(bull_rounds):
                rt = bull_rounds[i].strip()
                se = min(200, len(rt))
                for sep in ["\n\n", "\u3002", "\uff01", "\uff1f"]:
                    idx = rt.find(sep)
                    if 50 < idx < 300:
                        se = idx + 1
                        break
                lines.append(f"**看多方**: {rt[:se].strip()}")
                lines.append("")
                lines.append("**看多方完整论述**:")
                lines.append(f"> {rt}")
                lines.append("")
            if i < len(bear_rounds):
                rt = bear_rounds[i].strip()
                se = min(200, len(rt))
                for sep in ["\n\n", "\u3002", "\uff01", "\uff1f"]:
                    idx = rt.find(sep)
                    if 50 < idx < 300:
                        se = idx + 1
                        break
                lines.append(f"**看空方**: {rt[:se].strip()}")
                lines.append("")
                lines.append("**看空方完整论述**:")
                lines.append(f"> {rt}")
                lines.append("")
        if judge:
            lines.append("### 裁判裁定")
            lines.append("")
            lines.append(judge)
            lines.append("")
    lines.append("---")
    
    # 5. 推理逻辑流
    lines.append("## 5. 推理逻辑流和核心逻辑节点")
    lines.append("")
    for key, title in [
        ("news_report", "新闻分析"),
        ("sentiment_report", "情绪分析"),
        ("policy_report", "政策分析"),
        ("hot_money_report", "游资追踪"),
        ("lockup_report", "解禁监控"),
    ]:
        content = safe_str(final_state.get(key, "N/A"))
        if content and content != "N/A":
            lines.append(f"### {title}")
            lines.append(content)
            lines.append("")
    lines.append("---")
    
    # 6. 风险讨论
    lines.append("## 6. 风险讨论")
    risk_state = final_state.get("risk_debate_state", {})
    if isinstance(risk_state, dict):
        risk_judge = safe_str(risk_state.get("judge_decision", ""))
        for key, label in [("aggressive_history", "激进派"), ("conservative_history", "保守派"), ("neutral_history", "中立派")]:
            hist = risk_state.get(key, [])
            if hist and isinstance(hist, str) and hist.strip():
                lines.append(f"\n**{label}观点**:")
                lines.append(f"> {hist}")
        if risk_judge:
            lines.append("\n**风险裁判决策**:")
            lines.append(risk_judge)
    lines.append("")
    lines.append("---")
    lines.append("*本报告由 TradingAgents-007 多智能体框架自动生成，仅作信息跟踪，不构成投资建议。*")
    
    report_text = "\n".join(lines)
    
    # ── 写入 007 自己的 vault ──
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    size_kb = len(report_text) / 1024
    print(f"[007] ✅ 分析完成: {name}({code})")
    print(f"[007]   操作建议: {action}")
    print(f"[007]   报告: {report_path} ({size_kb:.0f} KB)")
    
    # ── 跨员工分发 ──
    if employee_id:
        emp_path = resolve_employee_vault(employee_id)
        if emp_path:
            filename = build_report_filename(code, name, date_str)
            dest = os.path.join(emp_path, filename)
            shutil.copy2(report_path, dest)
            print(f"[007]   → 已分发至员工 {employee_id}: {dest}")
    
    # ── 写 journal ──
    write_journal(date_str, name, code, employee_id)
    
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="007号员工 — 多agent个股分析")
    parser.add_argument("--code", help="股票代码，如 002594")
    parser.add_argument("--name", help="股票名称，如 比亚迪")
    parser.add_argument("--date", default=datetime.date.today().isoformat(), help="分析日期，默认今天")
    parser.add_argument("--employee", help="委托员工编号，如 005（可选，报告将同时分发到该员工 vault）")
    parser.add_argument("--list", action="store_true", help="列出当日缓存报告")
    
    args = parser.parse_args()
    
    if args.list:
        list_cached_reports()
        sys.exit(0)
    
    if not args.code or not args.name:
        parser.print_help()
        sys.exit(1)
    
    run_analysis(args.code, args.name, args.date, args.employee)

