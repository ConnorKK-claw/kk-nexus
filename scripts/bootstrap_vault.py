"""
bootstrap_vault.py — 在 skill 目录下创建 vault 目录结构 + 注册 ontology

用法:
    python bootstrap_vault.py <skill-dir>
    python bootstrap_vault.py --all                    # 为所有 skill 创建 vault
    python bootstrap_vault.py --dry-run <skill-dir>    # 预览
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

DEFAULT_SKILLS_DIR = Path.home() / ".codex" / "skills"

VAULT_STRUCTURE = [
    "raw/user",
    "raw/agent",
    "raw/original",
    "knowledge",
    "templates",
    "cases",
    "journal",
    "auto-update",
]

ONTOLOGY_DIR = Path.home() / ".codex" / "memories" / "ontology"
ONTOLOGY_FILE = ONTOLOGY_DIR / "graph.jsonl"


def has_vault(vault_dir: Path) -> bool:
    return vault_dir.is_dir()



def _generate_zk_categories(vault_dir: Path, skill_dir: Path):
    """在 vault 根目录生成 zk-categories.md（分类码映射表）。
    如果文件已存在则跳过。
    """
    zk_path = vault_dir / "zk-categories.md"
    if zk_path.exists():
        return

    skill_name = skill_dir.name
    domain_desc = skill_name_to_domain(skill_name)
    now = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
title: ZK 分类码映射表 — {skill_name}
date: {now}
source: agent
domain: {skill_name}
tags: [元数据, 分类]
status: verified
imported_by: bootstrap_vault.py
imported_at: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
---

# ZK 分类码映射表 — {skill_name}

{domain_desc} 领域的知识节点分类体系。

| 分类码 | 含义 | 说明 |
|--------|------|------|
| aa | 法规框架 (Regulatory Framework) | 相关法规、管理办法、指导意见 |
| bb | 操作实务 (Operational Practice) | 方案设计、测算方法、实务流程 |
| cc | 案例方法 (Case Methodology) | 公司案例、市场数据、实施经验 |

> 知识节点命名: `zk-{{domain}}-{{catseq}}-{{docseq}}-{{title}}.md`
> 其中 {{catseq}} = 分类码 + 组序号（如 aa0），{{docseq}} = 组内文档 0-based 序号
> 首次创建时扫描 knowledge/ 取最大序号 +1
"""
    zk_path.write_text(content, encoding="utf-8")
    print(f"  [zk-categories] 已生成: {zk_path.name}")


def register_in_ontology(skill_dir: Path):
    """在 ontology 中注册 Vault 实体。"""
    vault_path = str(skill_dir / "vault")
    vault_name = skill_dir.name

    # 从 SKILL.md 提取 domain 描述
    skillmd = skill_dir / "SKILL.md"
    domain_desc = skill_name_to_domain(vault_name)
    if skillmd.exists():
        content = skillmd.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("description:"):
                domain_desc = line.split(":", 1)[1].strip()
                break

    entity = {
        "op": "create",
        "entity": {
            "id": f"vault_{vault_name}",
            "type": "Vault",
            "properties": {
                "name": vault_name,
                "path": vault_path,
                "domain": domain_desc,
                "created_at": datetime.now().isoformat(),
                "status": "active",
            }
        }
    }

    ONTOLOGY_DIR.mkdir(parents=True, exist_ok=True)
    with open(ONTOLOGY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entity, ensure_ascii=False) + "\n")
    print(f"  [ontology] Vault 实体已注册: vault_{vault_name}")


def skill_name_to_domain(name: str) -> str:
    """将 skill 名称映射为 domain 描述。"""
    mapping = {
        "equity-incentive": "股权激励方案设计与法规",
        "a-share-research": "A 股市场研究",
        "tax-compliance-expert": "税务合规",
        "trading-analysis": "交易分析",
        "hedge-fund-masters": "对冲基金策略",
        "deep-research": "深度研究",
        "6.skill": "量化交易+股权激励",
    }
    return mapping.get(name, name)


def bootstrap_vault(skill_dir: Path, dry_run: bool = False) -> bool:
    """为指定 skill 创建 vault 目录结构。"""
    skill_dir = skill_dir.resolve()
    vault_dir = skill_dir / "vault"

    if not skill_dir.is_dir():
        print(f"[错误] 目录不存在: {skill_dir}")
        return False

    if has_vault(vault_dir):
        print(f"[跳过] vault 已存在: {skill_dir.name}")
        return False

    if dry_run:
        print(f"\n=== [DRY RUN] {skill_dir.name} ===")
        print(f"  将创建: {vault_dir}")
        for sub in VAULT_STRUCTURE:
            print(f"    vault/{sub}/")
        print(f"  将注册 ontology: vault_{skill_dir.name}")
        return False

    # 创建目录
    vault_dir.mkdir(parents=True, exist_ok=True)
    for sub in VAULT_STRUCTURE:
        (vault_dir / sub).mkdir(parents=True, exist_ok=True)

        # 占位文件
    for sub in VAULT_STRUCTURE:
        placeholder = vault_dir / sub / ".gitkeep"
        if not placeholder.exists():
            placeholder.write_text("", encoding="utf-8")

    # 生成 zk-categories.md（分类码映射表）
    _generate_zk_categories(vault_dir, skill_dir)

    print(f"[OK] vault 已创建: {skill_dir.name} -> vault/")

    # 注册 ontology
    try:
        register_in_ontology(skill_dir)
    except Exception as e:
        print(f"  [警告] ontology 注册失败: {e}")

    return True


def find_all_skills(base_dir: Path) -> list[Path]:
    if not base_dir.is_dir():
        print(f"[错误] skills 目录不存在: {base_dir}")
        return []
    return sorted([p for p in base_dir.iterdir() if p.is_dir()])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建 vault 目录结构")
    parser.add_argument("skill_dir", nargs="?", type=Path, default=None,
                        help="Skill 目录路径（不指定时需使用 --all）")
    parser.add_argument("--all", action="store_true",
                        help=f"为 {DEFAULT_SKILLS_DIR} 下所有 skill 批量创建")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览变更，不实际创建")
    args = parser.parse_args()

    if args.all:
        skills = find_all_skills(DEFAULT_SKILLS_DIR)
        if not skills:
            sys.exit(1)
        for s in skills:
            bootstrap_vault(s, dry_run=args.dry_run)
    elif args.skill_dir:
        bootstrap_vault(args.skill_dir, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)
