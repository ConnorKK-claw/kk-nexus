"""
enhance_skillmd.py — 自动增强 SKILL.md，加入 vault 上下文注入块 (v1.1)

修复: 增强的去重检测，防止重复注入导致 SKILL.md 损坏

用法:
    python enhance_skillmd.py <skill-dir>              # 增强（自动备份）
    python enhance_skillmd.py <skill-dir> --dry-run    # 预览变更
    python enhance_skillmd.py <skill-dir> --uninstall  # 移除注入块
    python enhance_skillmd.py <skill-dir> --update     # 更新注入块为新模板

前置条件：skill 目录下已有 vault/ 结构（可先运行 bootstrap_vault.py）
"""

import argparse
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime

TEMPLATE_FILE = Path(__file__).resolve().parent.parent / "templates" / "skill-header.md"
MARKER = "## Vault 知识库"

# 用于检测完整注入块的多个关键标记（防止只匹配到部分内容）
VAULT_KEY_SECTIONS = [
    MARKER,
    "### 启动时检索",
    "### 知识蒸馏 SOP",
    "### 知识使用追踪",
]


def load_template(skill_name: str) -> str:
    """加载模板并替换占位符。"""
    if not TEMPLATE_FILE.exists():
        print(f"[错误] 模板文件不存在: {TEMPLATE_FILE}")
        sys.exit(1)
    content = TEMPLATE_FILE.read_text(encoding="utf-8")
    content = content.replace("<skill-vault-name>", skill_name)
    return content


def backup_skillmd(skillmd: Path) -> Path:
    """备份 SKILL.md 为 SKILL.md.bak.{timestamp}。"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    bak = skillmd.with_suffix(f".md.bak.{ts}")
    shutil.copy2(skillmd, bak)
    print(f"  备份: {bak.name}")
    return bak


def is_enhanced(skillmd: Path) -> bool:
    """检查是否已包含完整的 vault 上下文注入块。
    检测多个关键标记防止重复注入；同时检测重复标记以识别损坏。
    """
    content = skillmd.read_text(encoding="utf-8")

    # 检查所有关键标记是否都存在
    missing = [s for s in VAULT_KEY_SECTIONS if s not in content]
    if missing:
        return False

    # 检测重复标记（识别损坏的 SKILL.md）
    marker_count = content.count(MARKER)
    if marker_count > 1:
        print(f"  [警告] 发现 {marker_count} 个 `{MARKER}` 标记，SKILL.md 可能已损坏！")
        print(f"  建议先运行 --uninstall 移除旧注入块，再重新增强")

    return True


def find_vault_block(content: str) -> tuple[int, int] | None:
    """找到注入块的起止位置，返回 (start, end) 或 None。

    从 ## Vault 知识库 开始，到 ## 配置需求 的 checklist 结束
    （即下一个 ## 标题之前）。

    如果文件中存在多个 ## Vault 知识库，只处理第一个实例。
    """
    start = content.find(MARKER)
    if start == -1:
        return None

    # 找到 ## 配置需求 作为块结束标记
    config_pos = content.find("## 配置需求", start)
    if config_pos == -1:
        # 找不到结束标记，取到下一个 ## 标题或文件尾
        rest = content[start + len(MARKER):]
        end_match = re.search(r"\n##\s", rest)
        if end_match:
            return start, start + len(MARKER) + end_match.start()
        return start, len(content)

    # 从 ## 配置需求 找到下一个 ## 标题或文件尾
    after_config = content[config_pos + len("## 配置需求"):]
    next_heading = re.search(r"\n##\s", after_config)
    if next_heading:
        end = config_pos + len("## 配置需求") + next_heading.start()
    else:
        end = len(content)

    return start, end


def enhance(skill_dir: Path, dry_run: bool = False) -> bool:
    """增强 SKILL.md，返回 True 表示已修改。"""
    skill_dir = skill_dir.resolve()
    skillmd = skill_dir / "SKILL.md"

    if not skillmd.exists():
        print(f"[跳过] 无 SKILL.md: {skill_dir.name}")
        return False

    if is_enhanced(skillmd):
        print(f"[跳过] 已增强: {skill_dir.name}")
        print(f"  使用 --update 更新注入块，--uninstall 移除注入块")
        return False

    vault_dir = skill_dir / "vault"
    if not vault_dir.is_dir():
        print(f"[警告] 无 vault/ 目录: {skill_dir.name}（建议先运行 bootstrap_vault.py）")

    template = load_template(skill_dir.name)
    original = skillmd.read_text(encoding="utf-8")

    # 插入到第一个 ## 标题之前
    match = re.search(r"^##\s", original, re.MULTILINE)
    if match:
        insert_pos = match.start()
        new_content = original[:insert_pos] + template + "\n" + original[insert_pos:]
    else:
        new_content = original + "\n\n" + template + "\n"

    if dry_run:
        print(f"\n=== [DRY RUN] {skill_dir.name} ===")
        preview = new_content[:600]
        print(preview + ("..." if len(new_content) > 600 else ""))
        return False

    backup_skillmd(skillmd)
    skillmd.write_text(new_content, encoding="utf-8")
    print(f"[OK] 已增强: {skill_dir.name}")
    return True


def uninstall(skill_dir: Path, dry_run: bool = False) -> bool:
    """移除 vault 注入块。"""
    skillmd = skill_dir / "SKILL.md"

    if not skillmd.exists():
        print(f"[跳过] 无 SKILL.md: {skill_dir.name}")
        return False

    if not is_enhanced(skillmd):
        print(f"[跳过] 未增强: {skill_dir.name}")
        return False

    content = skillmd.read_text(encoding="utf-8")
    block = find_vault_block(content)
    if block is None:
        print(f"[错误] 找不到注入块: {skill_dir.name}")
        return False

    start, end = block
    new_content = content[:start] + content[end:]

    if dry_run:
        removed = content[start:end]
        print(f"\n=== [DRY RUN] 将移除 ===")
        print(removed[:200] + ("..." if len(removed) > 200 else ""))
        return False

    backup_skillmd(skillmd)
    skillmd.write_text(new_content, encoding="utf-8")
    # 清理空行
    _clean_blank_lines(skillmd)
    print(f"[OK] 已移除注入块: {skill_dir.name}")
    return True


def _clean_blank_lines(skillmd: Path):
    """移除卸载后产生的多余空行。"""
    content = skillmd.read_text(encoding="utf-8")
    # 压缩连续 3+ 空行为 2 个空行
    cleaned = re.sub(r"\n{3,}", "\n\n", content)
    skillmd.write_text(cleaned, encoding="utf-8")


def update(skill_dir: Path, dry_run: bool = False) -> bool:
    """更新注入块为新模板。等价于 uninstall + enhance。"""
    skillmd = skill_dir / "SKILL.md"

    if not skillmd.exists():
        print(f"[跳过] 无 SKILL.md: {skill_dir.name}")
        return False

    if not is_enhanced(skillmd):
        print(f"[提示] 未增强，将执行首次 enhance: {skill_dir.name}")
        return enhance(skill_dir, dry_run=dry_run)

    if dry_run:
        print(f"\n=== [DRY RUN] 将更新注入块: {skill_dir.name} ===")
        return False

    # 先卸载再增强
    backup_skillmd(skillmd)
    content = skillmd.read_text(encoding="utf-8")

    # 找到所有注入块并移除（防止有重复块时只移除一个）
    while True:
        block = find_vault_block(content)
        if block is None:
            break
        start, end = block
        content = content[:start] + content[end:]

    # 清理多余空行
    content = re.sub(r"\n{3,}", "\n\n", content)

    template = load_template(skill_dir.name)
    match = re.search(r"^##\s", content, re.MULTILINE)
    if match:
        insert_pos = match.start()
        content = content[:insert_pos] + template + "\n" + content[insert_pos:]
    else:
        content = content + "\n\n" + template + "\n"

    skillmd.write_text(content, encoding="utf-8")
    print(f"[OK] 已更新注入块: {skill_dir.name}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="增强/卸载/更新 SKILL.md vault 上下文")
    parser.add_argument("skill_dir", type=Path, help="Skill 目录路径")
    parser.add_argument("--dry-run", action="store_true", help="预览变更，不实际修改")
    parser.add_argument("--uninstall", action="store_true", help="移除 vault 注入块")
    parser.add_argument("--update", action="store_true", help="更新注入块为新模板")
    args = parser.parse_args()

    if args.uninstall:
        uninstall(args.skill_dir, dry_run=args.dry_run)
    elif args.update:
        update(args.skill_dir, dry_run=args.dry_run)
    else:
        enhance(args.skill_dir, dry_run=args.dry_run)
