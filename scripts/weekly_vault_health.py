"""
weekly_vault_health.py - 每周 vault 健康检查

检查项:
1. 双重 BOM 头文件
2. 重复 URL 的文章
3. 文件总数和覆盖缺口
4. 编码异常

静默运行，有问题才输出到控制台。
"""
import os, re, sys
from collections import defaultdict

VAULT = r"C:\Users\hexk\.codex\skills\financial-analysis\vault\raw\user"
REPORT_FILE = os.path.join(os.path.dirname(VAULT), "..", "..", "health-report.md")

def check_double_bom():
    """检查双重 BOM 文件"""
    bad = []
    for fn in os.listdir(VAULT):
        if not fn.endswith(".md"): continue
        fpath = os.path.join(VAULT, fn)
        with open(fpath, "rb") as f:
            raw = f.read(6)
        if raw[:6] == b"\xef\xbb\xbf\xef\xbb\xbf":
            bad.append(fn)
    return bad

def check_duplicate_urls():
    """检查重复 URL"""
    url_map = defaultdict(list)
    for fn in sorted(os.listdir(VAULT)):
        if not fn.endswith(".md"): continue
        fpath = os.path.join(VAULT, fn)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        m = re.search(r"^url[\uff1a:]\s*(https?://\S+)", content, re.MULTILINE)
        if m:
            url_map[m.group(1)].append(fn)
    return {url: files for url, files in url_map.items() if len(files) > 1}

def check_encoding():
    """检查编码异常文件"""
    bad = []
    for fn in os.listdir(VAULT):
        if not fn.endswith(".md"): continue
        fpath = os.path.join(VAULT, fn)
        with open(fpath, "rb") as f:
            raw = f.read()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            bad.append((fn, "not valid UTF-8"))
            continue
    return bad

def get_coverage_summary():
    """统计覆盖情况"""
    pub_monthly = defaultdict(int)
    undated = 0
    for fn in sorted(os.listdir(VAULT)):
        if not fn.endswith(".md"): continue
        fpath = os.path.join(VAULT, fn)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Check signature date
        m = re.search(r"(?:\u539f\u521b.*?\*|_)(\d{4})\u5e74(\d{1,2})\u6708(\d{1,2})\u65e5", content)
        if m:
            pub_monthly["%s-%02d" % (m.group(1), int(m.group(2)))] += 1
            continue
        # Check YAML date
        if content.startswith("---") or content.lstrip("\ufeff").startswith("---"):
            clean = content.lstrip("\ufeff")
            end = clean.find("---", 3)
            if end > 0:
                yaml = clean[3:end]
                m = re.search(r"^date[\uff1a:]\s*(\d{4})-(\d{1,2})", yaml, re.MULTILINE)
                if m:
                    pub_monthly["%s-%02d" % (m.group(1), int(m.group(2)))] += 1
                    continue
        undated += 1
    
    # Check missing months (past 2 years)
    missing = []
    for y in [2025, 2026]:
        for mo in range(1, 13):
            ym = "%d-%02d" % (y, mo)
            if ym > "2026-06":
                break
            if ym not in pub_monthly:
                missing.append(ym)
    
    return {
        "total": len([f for f in os.listdir(VAULT) if f.endswith(".md")]),
        "with_dates": sum(pub_monthly.values()),
        "undated": undated,
        "covered_months": len(pub_monthly),
        "missing_months": missing,
        "monthly_breakdown": dict(sorted(pub_monthly.items())),
    }

# ---- Run checks ----
issues = []

print("=== Weekly Vault Health Check ===")
print()

# 1. Double BOM
bom = check_double_bom()
if bom:
    issues.append("Double BOM files: %d" % len(bom))
    print("ISSUE: %d files have double BOM" % len(bom))
    for f in bom[:5]:
        print("  - " + f)
    if len(bom) > 5:
        print("  ... and %d more" % (len(bom) - 5))
else:
    print("OK: No double BOM files")

# 2. Duplicate URLs
dupes = check_duplicate_urls()
if dupes:
    issues.append("Duplicate articles: %d URLs" % len(dupes))
    print("ISSUE: %d URLs have duplicate files" % len(dupes))
    for url, files in list(dupes.items())[:3]:
        print("  URL: %s" % url[:60])
        for f in files:
            print("    - " + f)
else:
    print("OK: No duplicate URLs")

# 3. Encoding
encoding_issues = check_encoding()
if encoding_issues:
    issues.append("Encoding issues: %d files" % len(encoding_issues))
    print("ISSUE: %d files have encoding problems" % len(encoding_issues))
    for f, reason in encoding_issues[:5]:
        print("  - %s (%s)" % (f, reason))
else:
    print("OK: No encoding issues")

# 4. Coverage
cov = get_coverage_summary()
print("\nCoverage: %d total files, %d with dates, %d undated" % (cov["total"], cov["with_dates"], cov["undated"]))
missing = cov["missing_months"]
if missing:
    issues.append("Missing months: %d months" % len(missing))
    print("Missing months: %s" % ", ".join(missing))
else:
    print("All months covered!")

print("\n---")
if issues:
    print("FOUND %d ISSUES:" % len(issues))
    for i, iss in enumerate(issues, 1):
        print("  %d. %s" % (i, iss))
    sys.exit(1)
else:
    print("All checks passed.")
    sys.exit(0)


