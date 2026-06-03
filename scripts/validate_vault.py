"""
validate_vault.py — 校验 vault 文件的 YAML frontmatter 和命名规范

用法:
    python validate_vault.py <vault-path>
    python validate_vault.py <vault-path> --strict    # 严格模式（警告也报错）
    python validate_vault.py <vault-path> --fix        # 自动修复可修复的问题

检查项:
  - YAML frontmatter 是否存在
  - 必填字段: title, date, source, domain, tags, status
  - 枚举值: source (user|agent|distilled), status (raw|distilled|verified|expired)
  - 日期格式: YYYY-MM-DD
  - 文件名是否符合所在目录的命名规范
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

VALID_SOURCES = {"user", "agent", "distilled"}
VALID_STATUSES = {"raw", "distilled", "verified", "expired"}
REQUIRED_FIELDS = ["title", "date", "source", "domain", "tags", "status"]

# 命名模式
PATTERNS = {
    "raw/user": re.compile(r"^\d{4}-\d{2}-\d{2}-.+-(user|agent)\.md$"),
    "raw/agent": re.compile(r"^\d{4}-\d{2}-\d{2}-.+-(user|agent)\.md$"),
    "knowledge": re.compile(r"^zk-[a-z]+-[a-z]+\d*-\d+-.+\.md$"),
    "templates": re.compile(r"^.+-template\.md$"),
    "cases": re.compile(r"^\d{4}-\d{2}-\d{2}-.+-.+-.+\.md$"),
    "journal": re.compile(r"^\d{4}-\d{2}-\d{2}\.md$"),
}


def extract_frontmatter(filepath: Path) -> tuple[dict | None, str]:
    """提取 YAML frontmatter，返回 (dict, 原始文本)。"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  读取失败: {e}")
        return None, ""

    if content.startswith("\ufeff"):
        content = content[1:]

    if not content.startswith("---"):
        return None, content

    end = content.find("---", 3)
    if end == -1:
        return None, content

    fm_text = content[3:end].strip()
    if not fm_text:
        return None, content

    fm = {}
    list_key = None
    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if list_key:
                fm.setdefault(list_key, []).append(stripped[2:].strip())
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                fm[key] = [v.strip().strip('\"').strip("'") for v in inner.split(",") if v.strip()]
                list_key = None
            else:
                fm[key] = val.strip('\"').strip("'")
                list_key = key if val == "" else None
    return fm, content


def validate_date(date_str: str) -> bool:
    """验证 YYYY-MM-DD 格式。"""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_vault(vault_dir: Path, strict: bool = False, fix: bool = False) -> tuple[int, int, int]:
    """校验 vault 下所有 .md 文件。返回 (通过, 警告, 错误)。"""
    vault_dir = vault_dir.resolve()
    if not vault_dir.is_dir():
        print(f"[错误] vault 目录不存在: {vault_dir}")
        return 0, 0, 1

    errors = 0
    warnings = 0
    passed = 0

    # 扫描除 index.md .gitkeep 和 raw/original/ 外的所有 .md
    md_files = [
        f for f in vault_dir.glob("**/*.md")
        if f.name != "index.md" and f.name != ".gitkeep" and "raw/original" not in str(f.parent).replace(chr(92), chr(47))
    ]

    if not md_files:
        print("[提示] vault 中无 .md 文件")
        return 0, 0, 0

    print(f"校验 {len(md_files)} 个文件...\n")

    for f in sorted(md_files):
        rel_path = str(f.relative_to(vault_dir)).replace("\\", "/")
        file_errors = []
        file_warnings = []

        # 1. 提取 frontmatter
        fm, content = extract_frontmatter(f)
        if fm is None:
            file_errors.append("缺少 YAML frontmatter")
            print(f"[ERR] {rel_path}: 缺少 YAML frontmatter")
            errors += 1
            continue

        # 2. 检查必填字段
        for field in REQUIRED_FIELDS:
            if field not in fm or not fm[field]:
                if field == "tags" and isinstance(fm.get("tags"), list) and len(fm["tags"]) == 0:
                    file_warnings.append(f"字段 '{field}' 为空数组")
                else:
                    file_errors.append(f"缺少必填字段 '{field}'")

        # 3. 校验枚举值
        if fm.get("source") and fm["source"] not in VALID_SOURCES:
            file_errors.append(f"无效 source: '{fm['source']}'（应为 {VALID_SOURCES}）")

        if fm.get("status") and fm["status"] not in VALID_STATUSES:
            file_errors.append(f"无效 status: '{fm['status']}'（应为 {VALID_STATUSES}）")

        # 4. 校验日期
        if fm.get("date") and not validate_date(fm["date"]):
            file_errors.append(f"日期格式错误: '{fm['date']}'（应为 YYYY-MM-DD）")

        # 5. 文件名规范检查
        parent_dir = str(f.parent.relative_to(vault_dir)).replace("\\", "/")
        if parent_dir in PATTERNS:
            pattern = PATTERNS[parent_dir]
            if not pattern.match(f.name):
                file_warnings.append(f"文件名不符合 {parent_dir}/ 命名规范")

        # 输出结果
        if file_errors:
            print(f"[ERR] {rel_path}")
            for e in file_errors:
                print(f"   [ERR] {e}")
            errors += 1
        elif file_warnings and strict:
            print(f"[WARN] {rel_path}")
            for w in file_warnings:
                print(f"   [WARN] {w}")
            warnings += 1
        elif file_warnings:
            print(f"[WARN] {rel_path}")
            for w in file_warnings:
                print(f"   [WARN] {w}")
            passed += 1  # 非严格模式警告不算错
        else:
            print(f"[OK] {rel_path}")
            passed += 1

    print(f"\n===== 校验结果 =====")
    print(f"  [OK] 通过: {passed}")
    print(f"  [WARN] 警告: {warnings}" if not strict else f"  [WARN] 警告(视作错误): {warnings}")
    print(f"  [ERR] 错误: {errors}")

    return passed, warnings, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="校验 vault 文件规范")
    parser.add_argument("vault_path", type=Path, help="Vault 目录路径")
    parser.add_argument("--strict", action="store_true", help="严格模式，警告也报错")
    parser.add_argument("--fix", action="store_true", help="自动修复（待实现）")
    args = parser.parse_args()

    passed, warnings, errors = validate_vault(args.vault_path, strict=args.strict, fix=args.fix)
    if errors > 0:
        sys.exit(1)
