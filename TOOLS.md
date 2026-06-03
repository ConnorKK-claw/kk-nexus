# TOOLS.md - Tool Configuration & Gotchas

> Document tool-specific configurations, gotchas, and credentials here.

---

## tushare (A-Share Stock Data)

**Status:** ✅ Working

**Gotchas:**
- Windows system proxy (localhost:15236) blocks tushare API connections
- Fix: Always call `os.environ.pop("HTTP_PROXY", None)` and `os.environ.pop("HTTPS_PROXY", None)` before API calls
- Running as script file is more reliable than command-line one-liners
- Token: Stored in Python scripts (not in .env)

**Common Usage:**
- `pro.daily(ts_code=..., start_date=..., end_date=...)` for historical prices
- `pro.query('trade_cal', ...)` for trading calendar

---

## cninfo API (Announcement Search)

**Status:** ✅ Working

**Gotchas:**
- POST to `cninfo.com.cn/new/hisAnnouncement/query` with stock parameter has format issues
- Preferred: Use `fulltextSearch/full` endpoint with `searchkey` parameter
- PDF download via: `https://static.cninfo.com.cn/{adjunctUrl}`

---

## eastmoney API (Stock K-Line)

**Status:** ✅ Working

**Gotchas:**
- Same proxy issue as tushare — clear HTTP_PROXY before use
- URL format: `push2his.eastmoney.com/api/qt/stock/kline/get`

---

## pdfplumber (PDF Table Extraction)

**Status:** ✅ Preferred

**Notes:**
- Best tool for extracting 激励对象分配情况 tables from PDF 草案
- More reliable than markitdown for structured tables
- Works directly on original PDF files, not MD conversions

---

## markitdown (Document Conversion)

**Status:** ⚠️ Partial

**Notes:**
- PDF→MD: Works for text content
- DOCX→MD: Occasionally fails (degrade to plain text extraction)
- XLSX→MD: Works for simple tables

---

## Vault Scripts

All core scripts in `scripts/`:

| Script | Purpose |
|--------|---------|
| `vault_ingest.py` | File import with YAML frontmatter + dedup |
| `build_index.py` | Scan vault → generate knowledge/index.md |
| `validate_vault.py` | YAML schema + naming convention check |
| `health_check.py` | Expiry, duplicates, raw-pending detection |
| `unified_index.py` | Cross-vault + llm-wiki unified index |
| `wiki_to_kam.py` | Distill llm-wiki content into KAM knowledge nodes |
| `auto_health.py` | Scheduled vault health + heartbeat checks |
| `auto_heartbeat.py` | Full HEARTBEAT protocol execution |

Supported arguments: `--dry-run` (preview), `--help` (usage)

---

## Credentials

- **tushare token:** Set via environment variable TUSHARE_TOKEN or in local config
- **No .env file configured** — tokens are script-embedded (consider migrating)

---

*Add discovered gotchas here as they arise.*
