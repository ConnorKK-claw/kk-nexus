import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

def check_health():
    """返回 (overall, issues, fail_count, warn_count) 4 元组。

    overall ∈ {"OK", "WARN", "ERROR"}。
    所有提前退出路径必须返回 4 元组以保持调用处解包一致。
    """
    index_dir = config.TEXTAI_INDEX_DIR
    issues = []

    # 1. Check index directory exists
    if not index_dir.exists():
        issues.append({"check": "index_exists", "status": "FAIL",
                       "message": f"索引目录不存在: {index_dir}"})
        return "ERROR", issues, 1, 0

    # 2. Check config file
    config_file = index_dir / "config.json"
    if not config_file.exists():
        issues.append({"check": "config_exists", "status": "FAIL", "message": "config.json 不存在"})
    else:
        issues.append({"check": "config_exists", "status": "OK", "message": "config.json 存在"})

    # 3. Check stats
    stats_file = index_dir / "stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        doc_count = stats.get("total_docs", 0)
        build_date = stats.get("date", "unknown")
        build_ts = stats.get("timestamp", 0)
        age_hours = (datetime.now().timestamp() - build_ts) / 3600 if build_ts else 999

        if doc_count == 0:
            issues.append({"check": "doc_count", "status": "WARN", "message": "文档数为 0，可能索引损坏"})
        else:
            issues.append({"check": "doc_count", "status": "OK", "message": f"{doc_count} 个文档已索引"})

        if age_hours > 168:  # 7 days
            issues.append({"check": "freshness", "status": "WARN", "message": f"索引已过期 {age_hours:.1f} 小时（>168h）"})
        elif age_hours > 24:
            issues.append({"check": "freshness", "status": "OK", "message": f"索引较新 {build_date}（{age_hours:.1f} 小时）"})
        else:
            issues.append({"check": "freshness", "status": "OK", "message": f"索引最新 {build_date}"})

        vaults = stats.get("vaults", [])
        if vaults:
            issues.append({"check": "domain_coverage", "status": "OK",
                           "message": f"覆盖 {len(vaults)} 个 domain: {', '.join(vaults[:5])}{'...' if len(vaults) > 5 else ''}"})
        else:
            issues.append({"check": "domain_coverage", "status": "WARN", "message": "无 domain 覆盖信息"})
    else:
        issues.append({"check": "stats", "status": "FAIL", "message": "stats.json 不存在，索引可能未构建"})

    # 4. Try to load and query
    try:
        from txtai import Embeddings

        embeddings = Embeddings()
        embeddings.load(str(index_dir))
        count = embeddings.count()
        issues.append({"check": "embeddings_load", "status": "OK", "message": f"Embeddings 加载成功，{count} 个文档"})

        # Test search
        test_results = embeddings.search("测试", 1)
        if test_results:
            issues.append({"check": "search_test", "status": "OK", "message": "搜索测试通过"})
        else:
            issues.append({"check": "search_test", "status": "WARN", "message": "搜索无结果，可能索引为空"})
    except Exception as e:
        issues.append({"check": "embeddings_load", "status": "FAIL", "message": f"Embeddings 加载失败: {e}"})

    # Determine overall status
    fail_count = sum(1 for i in issues if i.get('status') == 'FAIL')
    warn_count = sum(1 for i in issues if i["status"] == "WARN")
    if fail_count > 0:
        overall = "ERROR"
    elif warn_count > 0:
        overall = "WARN"
    else:
        overall = "OK"

    return overall, issues, fail_count, warn_count

def main():
    overall, issues, fail_count, warn_count = check_health()
    print(f"txtai Health Check: [{overall}]")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Index: {config.TEXTAI_INDEX_DIR}")
    print()
    for issue in issues:
        icon = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}.get(issue["status"], "?")
        print(f"  [{issue['status']}] {icon} {issue['check']}: {issue['message']}")
    print()
    print(f"Summary: {len(issues)} checks, {fail_count} FAIL, {warn_count} WARN")

    if overall == "ERROR":
        sys.exit(1)

if __name__ == "__main__":
    main()
