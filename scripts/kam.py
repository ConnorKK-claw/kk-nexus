#!/usr/bin/env python3
"""
kam.py — Super KAM Unified CLI

Usage:
    python kam.py <command> [args]
    python kam.py --help

See 'python kam.py <command> --help' for per-command details.
"""

import argparse
import os
import json
import subprocess
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────
SCRIPTS = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS.parent

# ── Vault aliases (shortcuts for common vault paths) ─────────────
VAULT_ALIASES = {
    "ei": os.path.expanduser("~/.codex/skills/my-domain/vault"),
    "tax": os.path.expanduser("~/.codex/skills/tax-compliance-expert/vault"),
    "my-domain": os.path.expanduser("~/.codex/skills/my-domain/vault"),
    "tax-compliance": os.path.expanduser("~/.codex/skills/tax-compliance-expert/vault"),
}

VERSION = "1.0.0"


def resolve_vault(path: str) -> str:
    """Resolve vault alias to full path, or return path as-is."""
    if path in VAULT_ALIASES:
        return VAULT_ALIASES[path]
    return path


def resolve_all_vaults() -> list:
    """Load all active vault paths from ontology."""
    onto_path = Path.home() / ".codex" / "memories" / "ontology" / "graph.jsonl"
    vaults = []
    if not onto_path.exists():
        return vaults
    for line in onto_path.read_text(encoding="utf-8-sig").split(chr(10)):
        line = line.strip()
        if not line or 'Vault' not in line:
            continue
        try:
            obj = json.loads(line)
            ent = obj.get("entity", {})
            if ent.get("type") != "Vault":
                continue
            props = ent.get("properties", {})
            vpath = props.get("path", "")
            vname = props.get("name", Path(vpath).name)
            vdomain = props.get("domain", "")
            vstatus = props.get("status", "active")
            vaults.append({"name": vname, "path": vpath, "domain": vdomain, "status": vstatus})
        except Exception:
            continue
    return vaults
def run_script(name: str, args: list[str], **kwargs) -> int:
    """Run a script from scripts/ directory."""
    script_path = SCRIPTS / name
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(script_path)] + args
    if kwargs.get("dry_run"):
        print(f"[DRY-RUN] {' '.join(cmd)}")
        return 0
    result = subprocess.run(cmd, capture_output=False, timeout=300)
    return result.returncode
# ── Command handlers ─────────────────────────────────────────────
def cmd_ingest(args):
    """Import a file into vault."""
    script_args = [args.file, "--vault", resolve_vault(args.vault)]
    if args.tags:
        script_args += ["--tags", args.tags]
    if args.source:
        script_args += ["--source", args.source]
    if args.dry_run:
        script_args.append("--dry-run")
    return run_script("vault_ingest.py", script_args, dry_run=args.dry_run)
def cmd_build_index(args):
    """Rebuild vault knowledge/index.md."""
    script_args = [resolve_vault(args.vault)]
    if args.dry_run:
        script_args.append("--dry-run")
    return run_script("build_index.py", script_args, dry_run=args.dry_run)
def cmd_validate(args):
    """Validate vault schema and naming."""
    script_args = [resolve_vault(args.vault)]
    if args.strict:
        script_args.append("--strict")
    if args.fix:
        script_args.append("--fix")
    return run_script("validate_vault.py", script_args, dry_run=args.dry_run)
def cmd_health(args):
    """Run vault health check."""
    if args.vault:
        script_args = [resolve_vault(args.vault)]
        if args.raw_days:
            script_args += ["--raw-days", str(args.raw_days)]
        if args.knowledge_months:
            script_args += ["--knowledge-months", str(args.knowledge_months)]
        return run_script("health_check.py", script_args, dry_run=args.dry_run)
    else:
        # No vault specified: run cross-vault weekly health check
        return run_script("health_check.py", ["--mode", "weekly"], dry_run=args.dry_run)
def cmd_unified_index(args):
    """Generate or refresh the unified index."""
    script_args = []
    if args.refresh:
        script_args.append("--refresh")
    if args.check_stale:
        script_args.append("--check-stale")
    return run_script("unified_index.py", script_args, dry_run=args.dry_run)
def cmd_heartbeat(args):
    """Run full HEARTBEAT protocol."""
    return run_script("auto_heartbeat.py", [], dry_run=args.dry_run)
def cmd_bootstrap(args):
    """Create vault directory structure for a skill."""
    script_args = [args.skill_dir]
    if args.all:
        script_args.append("--all")
    if args.dry_run:
        script_args.append("--dry-run")
    return run_script("bootstrap_vault.py", script_args, dry_run=args.dry_run)
def cmd_enhance(args):
    """Inject vault context into SKILL.md."""
    script_args = [args.skill_dir]
    if args.uninstall:
        script_args.append("--uninstall")
    if args.update:
        script_args.append("--update")
    if args.dry_run:
        script_args.append("--dry-run")
    return run_script("enhance_skillmd.py", script_args, dry_run=args.dry_run)
def cmd_distill_wiki(args):
    """Distill llm-wiki content into KAM knowledge nodes."""
    script_args = []
    if args.vault:
        script_args += ["--vault", resolve_vault(args.vault)]
    if args.wiki:
        script_args += ["--wiki", args.wiki]
    if args.reverse:
        script_args.append("--reverse")
    return run_script("wiki_to_kam.py", script_args, dry_run=args.dry_run)
def cmd_query(args):
    """Query ontology graph."""
    script_args = []
    if args.type:
        script_args += ["--type", args.type]
    if args.domain:
        script_args += ["--domain", args.domain]
    if args.company:
        script_args += ["--company", args.company]
    if args.keyword:
        script_args += ["--keyword", args.keyword]
    return run_script("query_ontology.py", script_args, dry_run=args.dry_run)
def cmd_update_cases(args):
    """Batch update case files."""
    script_args = []
    if args.field:
        script_args += ["--field", args.field]
    if args.value:
        script_args += ["--value", args.value]
    return run_script("update_cases.py", script_args, dry_run=args.dry_run)
def cmd_search(args):
    """Search vault files for keyword (cross-vault if no --vault given)."""
    keyword = args.keyword
    vaults_to_search = []
    if args.vault:
        # Single vault mode (original behavior)
        vaults_to_search.append((args.vault, Path(resolve_vault(args.vault))))
    else:
        # Cross-vault mode
        all_vaults = resolve_all_vaults()
        vaults_to_search = [(v["name"], Path(v["path"])) for v in all_vaults if v["status"] == "active"]
    if not vaults_to_search:
        print("[ERR] No vaults to search")
        return 1
    if args.dry_run:
        print(f"[DRY-RUN] Would search {len(vaults_to_search)} vaults for '{keyword}'")
        for name, vpath in vaults_to_search:
            print(f"  {name}: {vpath}")
        return 0
    limit = getattr(args, 'limit', 0) or 0
    total_matches = 0
    print("[CROSS-VAULT] \u641c\u7d22: " + keyword)
    print(f"  找到 {len(vaults_to_search)} vaults")
    print()
    for name, vpath in vaults_to_search:
        if not vpath.is_dir():
            print(f"  [SKIP] {name}: vault not found at {vpath}")
            continue
        script_path = SCRIPTS / "vault_search.py"
        try:
            r = subprocess.run(
                [sys.executable, str(script_path), str(vpath), keyword],
                capture_output=True, text=True, timeout=60,
                encoding="utf-8", errors="replace"
            )
            output = (r.stdout + r.stderr).strip()
        except subprocess.TimeoutExpired:
            output = "[ERR] Timeout"
        except Exception as e:
            output = f"[ERR] {e}"
        # Parse count from "[OK] 找到 N 条匹配"
        match_count = 0
        if "找到" in output:
            try:
                count_str = output.split("找到")[1].split()[0]
                match_count = int(count_str)
            except (IndexError, ValueError):
                match_count = 0
        total_matches += match_count
        # Print summary line
        icon = "[OK]" if match_count > 0 else "[--]"
        print(f"  {icon} {name} ({match_count} 条)")
        # Print up to limit matches per vault
        if match_count > 0 and limit != 0:
            lines = output.split(chr(10))
            shown = 0
            for line in lines:
                if line.startswith("  ") or line.startswith("# ") or "L" in line[:10]:
                    if "条匹配" in line or "OK" in line:
                        continue
                    print(f"    {line.strip()[:100]}")
                    shown += 1
                    if limit > 0 and shown >= limit:
                        print(f"    ... (限制 {limit} 条)")
                        break
    print()
    print(f"[CROSS-VAULT] 共计: {total_matches} 条匹配在 {len(vaults_to_search)} vaults 中")
    return 0
def cmd_auto_distill(args):
    """Run auto-distillation on raw vault files (delegates to auto_distill_vault.py)."""
    extra = []
    if args.vault: extra += ["--vault", args.vault]
    if args.dry_run: extra.append("--dry-run")
    if args.limit: extra += ["--limit", str(args.limit)]
    return run_script("auto_distill_vault.py", extra, dry_run=False)
def cmd_distill_vault(args):
    """Auto-distill raw vault files to knowledge nodes."""
    extra = []
    if args.vault: extra += ["--vault", args.vault]
    if args.dry_run: extra.append("--dry-run")
    if args.limit: extra += ["--limit", str(args.limit)]
    return run_script("auto_distill_vault.py", extra, dry_run=False)
def cmd_learning_bridge(args):
    """Consolidate .learnings/ entries into MEMORY.md."""
    extra = []
    if args.dry_run: extra.append("--dry-run")
    if args.all_vaults: extra.append("--all-vaults")
    return run_script("consolidate_learnings.py", extra, dry_run=False)
# ── Argument parser ──────────────────────────────────────────────
def cmd_compact_buffer(args):
    """Compress working-buffer."""
    extra = []
    if args.dry_run: extra.append("--dry-run")
    return run_script("compact_buffer.py", extra, dry_run=False)
def cmd_session_status(args):
    """Show session status summary."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    ss_file = root / "SESSION-STATE.md"
    buf_file = root / "memory" / "working-buffer.md"
    if ss_file.exists():
        ss = ss_file.read_text(encoding="utf-8")
        print("[SESSION] SESSION-STATE.md: FOUND")
        for line in ss.split(chr(10)):
            if line.startswith("- last_session:"):
                print(f"  last_session: {line.split(':', 1)[1].strip()}")
            if line.startswith("- session_count:"):
                print(f"  session_count: {line.split(':', 1)[1].strip()}")
            if line.startswith("- vaults_active:"):
                print(f"  vaults_active: {line.split(':', 1)[1].strip()}")
    else:
        print("[SESSION] SESSION-STATE.md: NOT FOUND")
    if ss_file.exists():
        import re
        in_p = False
        pending = 0
        for line in ss.split(chr(10)):
            if "### Pending" in line: in_p = True
            elif "### Completed" in line or line.startswith("## "): in_p = False
            elif in_p and line.strip().startswith("- ["): pending += 1
        print(f"  pending tasks: {pending}")
    if buf_file.exists():
        lines = buf_file.read_text(encoding="utf-8").split(chr(10))
        total = len(lines)
        status = "OK" if total <= 50 else "WARN"
        print(f"[SESSION] working-buffer: {total} lines ({status})")
    else:
        print("[SESSION] working-buffer: NOT FOUND")
    return 0
def build_parser():
    parser = argparse.ArgumentParser(
        prog="kam.py",
        description="Super KAM Unified CLI — manage knowledge vaults",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kam.py validate ei
  python kam.py build-index ei
  python kam.py ingest doc.pdf --vault ei --source user
  python kam.py unified-index --refresh
  python kam.py heartbeat
  python kam.py search '股权激励'
        """,
    )
    parser.add_argument("--version", "-V", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command", help="Available commands")
    # ── Core commands ──
    p_ingest = sub.add_parser("ingest", help="Import file into vault")
    p_ingest.add_argument("file", help="File to import")
    p_ingest.add_argument("--vault", default="ei", help="Vault path or alias (default: ei)")
    p_ingest.add_argument("--tags", help="Comma-separated tags")
    p_ingest.add_argument("--source", choices=["user", "agent"], default="user", help="Source type")
    p_ingest.add_argument("--dry-run", "-n", action="store_true", help="Preview only")
    p_build = sub.add_parser("build-index", aliases=["idx"], help="Rebuild knowledge index")
    p_build.add_argument("vault", nargs="?", default="ei", help="Vault path or alias (default: ei)")
    p_build.add_argument("--dry-run", "-n", action="store_true")
    p_val = sub.add_parser("validate", aliases=["val"], help="Validate vault schema")
    p_val.add_argument("vault", nargs="?", default="ei", help="Vault path or alias (default: ei)")
    p_val.add_argument("--strict", action="store_true", help="Strict validation")
    p_val.add_argument("--fix", action="store_true", help="Auto-fix issues")
    p_val.add_argument("--dry-run", "-n", action="store_true")
    p_health = sub.add_parser("health", help="Run vault health check")
    p_health.add_argument("vault", nargs="?", help="Vault path or alias (omit for all vaults)")
    p_health.add_argument("--raw-days", type=int, help="Days threshold for raw files")
    p_health.add_argument("--knowledge-months", type=int, help="Months threshold for knowledge expiry")
    p_health.add_argument("--dry-run", "-n", action="store_true")
    p_uni = sub.add_parser("unified-index", aliases=["ui"], help="Generate unified index")
    p_uni.add_argument("--refresh", action="store_true", help="Force refresh")
    p_uni.add_argument("--check-stale", action="store_true", help="Check if index is stale")
    p_uni.add_argument("--dry-run", "-n", action="store_true")
    p_hb = sub.add_parser("heartbeat", aliases=["hb"], help="Run HEARTBEAT protocol")
    p_hb.add_argument("--dry-run", "-n", action="store_true")
    p_boot = sub.add_parser("bootstrap", help="Create vault for a skill")
    p_boot.add_argument("skill_dir", help="Skill directory path")
    p_boot.add_argument("--all", action="store_true", help="Bootstrap all skills")
    p_boot.add_argument("--dry-run", "-n", action="store_true")
    p_enh = sub.add_parser("enhance", help="Inject vault context into SKILL.md")
    p_enh.add_argument("skill_dir", help="Skill directory path")
    p_enh.add_argument("--uninstall", action="store_true", help="Remove vault injection")
    p_enh.add_argument("--update", action="store_true", help="Update injection to latest template")
    p_enh.add_argument("--dry-run", "-n", action="store_true")
    p_dw = sub.add_parser("distill-wiki", aliases=["dw"], help="Distill llm-wiki to KAM")
    p_dw.add_argument("--vault", help="Vault path or alias (default: ei)")
    p_dw.add_argument("--wiki", help="llm-wiki wiki path")
    p_dw.add_argument("--reverse", action="store_true", help="Create reverse references KAM->wiki")
    p_dw.add_argument("--dry-run", "-n", action="store_true")
    # ── Utility commands ──
    p_q = sub.add_parser("query", help="Query ontology")
    p_q.add_argument("--type", help="Entity type filter")
    p_q.add_argument("--domain", help="Domain filter")
    p_q.add_argument("--company", help="Company filter")
    p_q.add_argument("--keyword", help="Keyword search")
    p_q.add_argument("--dry-run", "-n", action="store_true")
    p_uc = sub.add_parser("update-cases", help="Batch update case files")
    p_uc.add_argument("--field", help="Field to update")
    p_uc.add_argument("--value", help="Value to set")
    p_uc.add_argument("--dry-run", "-n", action="store_true")
    p_s = sub.add_parser("search", help="Search vault files")
    p_s.add_argument("keyword", help="Search keyword")
    p_s.add_argument("--vault", help="Vault path or alias (omit for cross-vault search)")
    p_s.add_argument("--limit", type=int, default=3, help="Max matches per vault (0=unlimited)")
    p_s.add_argument("--dry-run", "-n", action="store_true")
    p_ad = sub.add_parser("auto-distill", help="Run auto-distillation on raw vault files")
    p_ad.add_argument("--dry-run", "-n", action="store_true")
    p_ad.add_argument("--limit", type=int, default=0, help="Max files to process (0=all)")
    p_ad.add_argument("--vault", help="Vault path or alias")
    p_ad2 = sub.add_parser("distill-vault", aliases=["dv"], help="Auto-distill raw vault files to knowledge")
    p_ad2.add_argument("--dry-run", "-n", action="store_true")
    p_ad2.add_argument("--limit", type=int, default=0, help="Max files to process (0=all)")
    p_ad2.add_argument("--vault", help="Vault path")
    p_cb = sub.add_parser("compact-buffer", help="Compress working-buffer to memory/")
    p_cb.add_argument("--dry-run", "-n", action="store_true")
    p_ss = sub.add_parser("session-status", help="Show session state summary")
    p_lb = sub.add_parser("learning-bridge", help="Consolidate .learnings/ into MEMORY.md")
    p_lb.add_argument("--dry-run", "-n", action="store_true", help="Preview only")
    p_lb.add_argument("--all-vaults", action="store_true", help="Scan all employee vaults")
    return parser
def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(f"kam.py version {VERSION}")
        return 0
    if not args.command:
        parser.print_help()
        return 1
    # Route to command handler
    handlers = {
        "ingest": cmd_ingest,
        "build-index": cmd_build_index,
        "idx": cmd_build_index,
        "validate": cmd_validate,
        "val": cmd_validate,
        "health": cmd_health,
        "unified-index": cmd_unified_index,
        "ui": cmd_unified_index,
        "heartbeat": cmd_heartbeat,
        "hb": cmd_heartbeat,
        "bootstrap": cmd_bootstrap,
        "enhance": cmd_enhance,
        "distill-wiki": cmd_distill_wiki,
        "dw": cmd_distill_wiki,
        "query": cmd_query,
        "update-cases": cmd_update_cases,
        "search": cmd_search,
        "auto-distill": cmd_auto_distill,
        "distill-vault": cmd_distill_vault,
        "dv": cmd_distill_vault,
        "compact-buffer": cmd_compact_buffer,
        "session-status": cmd_session_status,
        "learning-bridge": cmd_learning_bridge,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"[ERROR] Unknown command: {args.command}", file=sys.stderr)
        print(f"  Run 'python kam.py --help' for available commands")
        return 1
if __name__ == "__main__":
    sys.exit(main())