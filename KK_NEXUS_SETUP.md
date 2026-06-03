# KK Nexus Setup

See AGENTS.md for full documentation.

## Quick Start

```
pip install txtai
python scripts/txtai_index.py --full
```

## Vault Locations

| # | Employee | Path |
|---|----------|------|
| 001 | equity-incentive | ~/.codex/skills/equity-incentive |
| 002 | tax-compliance-expert | ~/.codex/skills/tax-compliance-expert |
| 003 | weekly-report | ~/.codex/skills/weekly-report |
| 004 | hk-ipo | ~/.codex/skills/hk-ipo |
| 005 | financial-analysis | ~/.codex/skills/financial-analysis |

## Ontology

- Source: ~/.codex/memories/ontology/graph.jsonl
- Backup: backup/ontology.jsonl
- Run `python scripts/unified_index.py --refresh` after restore
