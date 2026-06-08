# HEARTBEAT.md - Periodic Self-Improvement

> This project uses automated heartbeat checks.
> Configured via Windows Task Scheduler and Python scripts.

---

## Automation Backbone

This project has two automated health check scripts:

### `python scripts/auto_health.py`
**Schedule:** Daily 09:00 + 21:00 (Task: KAM-VaultHealthCheck)

Checks:
- ✅ Vault validation (validate_vault.py)
- ✅ Knowledge expiry (health_check.py)
- ✅ Raw file pending count (WARN if >20)
- ✅ Index freshness (UNIFIED_INDEX.md < 24h?)
- ✅ Memory maintenance (recent memory/ files?)
- ✅ WAL integrity (SESSION-STATE.md recent?)
- ✅ Wiki-to-KAM distillation trigger
- ✅ Tag consistency (Mondays only)

### `python scripts/auto_heartbeat.py`
**Schedule:** Daily 21:00 (recommended)

Extended checks:
- Runs auto_health.py
- Checks .learnings/ERRORS.md for new entries
- Scans memory/ for maintenance reminders
- Reports to logs/heartbeat_YYYY-MM-DD.md
- Writes vault/journal/ entry on issues

---

## Per-Session Startup Checklist

When starting a new session:

1. Read `UNIFIED_INDEX.md` — Cross-system knowledge discovery
2. Read `SESSION-STATE.md` — Resume previous context
3. Read `memory/working-buffer.md` — Recent decisions and corrections
4. Check `memory/YYYY-MM-DD.md` (today) — Session continuity
5. Check `vaults/*/journal/YYYY-MM-DD.md` — Any auto-generated notes

---

## Manual Health Check

```powershell
# Quick vault status
python scripts/validate_vault.py ~/.codex/skills/equity-incentive/vault
python scripts/validate_vault.py ~/.codex/skills/tax-compliance-expert/vault

# Full heartbeat
python scripts/auto_heartbeat.py

# Rebuild unified index
python scripts/unified_index.py --refresh
```

---

*Customize this checklist for your workflow.*
