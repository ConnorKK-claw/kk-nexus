import os
os.environ.setdefault("HF_HUB_OFFLINE","1")
os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import os, sys, json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_health():
    index_dir = Path(r"C:\Users\hexk\.txtai_index")
    issues = []
    
    # 1. Check index directory exists
    if not index_dir.exists():
        return "ERROR", [{"check": "index_exists", "status": "FAIL", "message": f"???????: {index_dir}"}]
    
    # 2. Check config file
    config_file = index_dir / "config.json"
    if not config_file.exists():
        issues.append({"check": "config_exists", "status": "FAIL", "message": "????????"})
    else:
        issues.append({"check": "config_exists", "status": "OK", "message": "??????"})
    
    # 3. Check stats
    stats_file = index_dir / "stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        doc_count = stats.get("total_docs", 0)
        build_date = stats.get("date", "unknown")
        build_ts = stats.get("timestamp", 0)
        age_hours = (datetime.now().timestamp() - build_ts) / 3600 if build_ts else 999
        
        if doc_count == 0:
            issues.append({"check": "doc_count", "status": "WARN", "message": "?????0 ???"})
        else:
            issues.append({"check": "doc_count", "status": "OK", "message": f"{doc_count} ??????"})
        
        if age_hours > 168:  # 7 days
            issues.append({"check": "freshness", "status": "WARN", "message": f"??? {age_hours:.1f} ??????>168h?"})
        elif age_hours > 24:
            issues.append({"check": "freshness", "status": "OK", "message": f"????? {build_date}?{age_hours:.1f} ????"})
        else:
            issues.append({"check": "freshness", "status": "OK", "message": f"???????? {build_date}"})
        
        vaults = stats.get("vaults", [])
        if vaults:
            issues.append({"check": "domain_coverage", "status": "OK", "message": f"?? {len(vaults)} ? domain: {', '.join(vaults[:5])}{'...' if len(vaults) > 5 else ''}"})
        else:
            issues.append({"check": "domain_coverage", "status": "WARN", "message": "? domain ????"})
    else:
        issues.append({"check": "stats", "status": "FAIL", "message": "stats.json ???????????"})
    
    # 4. Try to load and query
    try:
        from txtai import Embeddings
        embeddings = Embeddings()
        embeddings.load(str(index_dir))
        count = embeddings.count()
        issues.append({"check": "embeddings_load", "status": "OK", "message": f"Embeddings ?????{count} ???"})
        
        # Test search
        test_results = embeddings.search("??", 1)
        if test_results:
            issues.append({"check": "search_test", "status": "OK", "message": "??????"})
        else:
            issues.append({"check": "search_test", "status": "WARN", "message": "?????????"})
    except Exception as e:
        issues.append({"check": "embeddings_load", "status": "FAIL", "message": f"Embeddings ????: {e}"})
    
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
    print(f"  Index: {PROJECT_ROOT / '.txtai' / 'index'}")
    print()
    for issue in issues:
        icon = {"OK": "?", "WARN": "?", "FAIL": "?"}.get(issue["status"], "?")
        print(f"  [{issue['status']}] {icon} {issue['check']}: {issue['message']}")
    print()
    print(f"Summary: {len(issues)} checks, {fail_count} FAIL, {warn_count} WARN")
    
    if overall == "ERROR":
        sys.exit(1)

if __name__ == "__main__":
    main()



