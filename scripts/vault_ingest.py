"""
vault_ingest.py — 文件转化导入 vault

用法:
    python vault_ingest.py <文件> --vault <vault-path> --source user|agent
    python vault_ingest.py --dir <目录> --vault <vault-path> --source user|agent
    python vault_ingest.py <文件> --vault <path> --source user --dry-run

支持格式: PDF, DOCX, PPTX, XLSX, XLS, MD, HTML, CSV, TXT
依赖: markitdown (已安装)

流程:
  1. 文件 → markitdown → Markdown 文本
  2. 添加 YAML frontmatter（自动填充元数据）
  3. 按命名规范保存到 vault/raw/{source}/
  4. 原文件归档到 vault/raw/original/
  5. 自动触发 build_index.py 重建索引
  可选参数:
    --tags "标签1,标签2"    为导入文件添加标签
    --domain "domain-name"   覆盖自动推导的 domain
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

SUPPORTED_EXT = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".md", ".html", ".csv", ".txt"}


def compute_md5(filepath: Path) -> str:
    """计算文件 MD5 哈希。"""
    return hashlib.md5(filepath.read_bytes()).hexdigest()


def check_duplicate(vault_dir: Path, filepath: Path) -> Path | None:
    """检查 vault 中是否已有相同 MD5 或相同文件名的文件。
    返回已存在的路径，无重复返回 None。
    """
    raw_dir = vault_dir / "raw"
    if not raw_dir.is_dir():
        return None

    target_md5 = compute_md5(filepath)

    # 扫描 raw/ 下所有 .md 查找重复
    for md_file in raw_dir.glob("**/*.md"):
        if md_file.name == "index.md":
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            if f"source_hash: {target_md5}" in content:
                return md_file
        except Exception:
            pass

    # 也检查 original/ 下同名文件
    original_dir = vault_dir / "raw" / "original"
    if original_dir.is_dir():
        for orig in original_dir.iterdir():
            if orig.name == filepath.name:
                if compute_md5(orig) == target_md5:
                    return orig

    return None


def convert_to_markdown(filepath: Path) -> str | None:
    """使用 markitdown 将文件转为 Markdown 文本。
    对 .md 文件直接读取，.txt 直接读取，其他格式走 markitdown。
    """
    ext = filepath.suffix.lower()

    if ext in {".md", ".txt"}:
        return filepath.read_text(encoding="utf-8")

    try:
        result = subprocess.run(
            ["markitdown", str(filepath)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"  [错误] markitdown 转换失败: {result.stderr[:200]}")
            return None
        return result.stdout
    except FileNotFoundError:
        print("  [错误] markitdown 未安装，请运行: pip install markitdown")
        return None
    except subprocess.TimeoutExpired:
        print(f"  [错误] markitdown 转换超时: {filepath.name}")
        return None
    except Exception as e:
        print(f"  [错误] markitdown 异常: {e}")
        return None


def slugify(text: str) -> str:
    """将中文/英文文本转为 slug。"""
    result = []
    for ch in text.lower():
        if ch.isalnum():
            result.append(ch)
        elif ch in " _-—":
            result.append("-")
        elif ord(ch) > 127:
            result.append(ch)
    slug = "".join(result)
    # 合并连字符
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def build_target_filename(filepath: Path, source: str, content: str) -> str:
    """按 raw 层命名规范生成目标文件名：YYYY-MM-DD-{slug}-{source}.md"""
    today = datetime.now().strftime("%Y-%m-%d")
    # 从原文件名取 slug（去掉扩展名）
    stem = filepath.stem
    slug = slugify(stem)
    if not slug:
        slug = "unnamed"
    if len(slug) > 60:
        slug = slug[:60]
    return f"{today}-{slug}-{source}.md"


def build_frontmatter(filepath: Path, source: str, vault_dir: Path = None,
                      tags: list[str] | None = None,
                      domain: str | None = None) -> str:
    """生成 YAML frontmatter。
    
    参数:
        tags: 标签列表，传入后替换默认空数组
        domain: 领域名称，优先级高于从 vault 父目录推导
    """
    now = datetime.now()
    md5_hash = compute_md5(filepath)
    domain_val = domain or (vault_dir.parent.name if vault_dir else "")
    tags_str = ""
    if tags:
        quoted = [f"{t}" for t in tags]
        tags_str = "[" + ", ".join(quoted) + "]"
    else:
        tags_str = "[]"

    return f"""---
title: {filepath.stem}
date: {now.strftime('%Y-%m-%d')}
source: {source}
original_source: {source}
source_path: original/{filepath.name}
domain: {domain_val}
tags: {tags_str}
status: raw
imported_by: vault_ingest.py
imported_at: {now.strftime('%Y-%m-%dT%H:%M:%S')}
source_hash: {md5_hash}
---
"""


def ingest_file(
    filepath: Path,
    vault_dir: Path,
    source: str,
    tags: list[str] | None = None,
    domain: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """导入单个文件到 vault。返回 True 表示成功。"""
    if not filepath.exists():
        print(f"[错误] 文件不存在: {filepath}")
        return False

    ext = filepath.suffix.lower()
    if ext not in SUPPORTED_EXT:
        print(f"[跳过] 不支持的格式 {ext}: {filepath.name}")
        return False

    # 去重检测
    dup = check_duplicate(vault_dir, filepath)
    if dup and not force:
        print(f"[跳过] 重复文件（已存在: {dup.name}）: {filepath.name}")
        print(f"  使用 --force 强制重新导入")
        return False

    # 创建目标目录
    raw_source_dir = vault_dir / "raw" / source
    original_dir = vault_dir / "raw" / "original"

    if dry_run:
        print(f"[DRY RUN] 将导入: {filepath.name}")
        print(f"  目标: {raw_source_dir / build_target_filename(filepath, source, '')}")
        print(f"  归档: {original_dir / filepath.name}")
        return True

    dup = check_duplicate(vault_dir, filepath)
    if dup and not force:
        print(f"  [跳过] 已存在相同文件: {dup.name}")
        return True

    raw_source_dir.mkdir(parents=True, exist_ok=True)
    original_dir.mkdir(parents=True, exist_ok=True)

    # 转换
    print(f"  转换: {filepath.name}")
    md_content = convert_to_markdown(filepath)
    if md_content is None:
        return False

    # 组装输出
    frontmatter = build_frontmatter(filepath, source, vault_dir, tags=tags, domain=domain)
    target_name = build_target_filename(filepath, source, md_content)

    # 写入 vault
    target_path = raw_source_dir / target_name
    # 处理同名冲突
    if target_path.exists() and not force:
        base = target_path.stem
        counter = 1
        while target_path.exists():
            target_path = raw_source_dir / f"{base}-{counter}.md"
            counter += 1

    target_path.write_text(frontmatter + "\n" + md_content, encoding="utf-8")

    # 归档原文件
    archive_path = original_dir / filepath.name
    if archive_path.exists() and not force:
        base = archive_path.stem
        ext_suffix = archive_path.suffix
        counter = 1
        while archive_path.exists():
            archive_path = original_dir / f"{base}-{counter}{ext_suffix}"
            counter += 1
    shutil.copy2(filepath, archive_path)

    print(f"  [OK] {target_path.name}")
    return True


def ingest_directory(
    dirpath: Path,
    vault_dir: Path,
    source: str,
    tags: list[str] | None = None,
    domain: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> tuple[int, int]:
    """批量导入目录下所有支持的文件。返回 (成功数, 失败数)。"""
    if not dirpath.is_dir():
        print(f"[错误] 目录不存在: {dirpath}")
        return 0, 0

    files = sorted(
        f for f in dirpath.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXT
    )

    if not files:
        print(f"[跳过] 目录下无可导入文件: {dirpath}")
        return 0, 0

    success = 0
    failed = 0
    for f in files:
        print(f"\n[{success + failed + 1}/{len(files)}] {f.name}")
        if ingest_file(f, vault_dir, source, tags=tags, domain=domain, dry_run=dry_run, force=force):
            success += 1
        else:
            failed += 1

    return success, failed


def rebuild_index(vault_dir: Path) -> None:
    """调用 build_index.py 重建索引。"""
    script_dir = Path(__file__).resolve().parent
    build_index_script = script_dir / "build_index.py"
    if not build_index_script.exists():
        print("  [提示] build_index.py 不存在，跳过索引重建")
        return
    try:
        subprocess.run(
            ["python", str(build_index_script), str(vault_dir)],
            check=True,
            timeout=30,
        )
    except Exception as e:
        print(f"  [警告] 索引重建失败: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="文件转化导入 vault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python vault_ingest.py 文件.pdf --vault ~/.codex/skills/equity-incentive/vault --source user --tags "法规,国资" --domain equity-incentive
  python vault_ingest.py --dir ./素材/ --vault ~/.codex/skills/equity-incentive/vault --source agent
  python vault_ingest.py 文件.pdf --vault ./vault --source user --dry-run
        """,
    )
    parser.add_argument("file", nargs="?", type=Path, default=None, help="要导入的文件路径")
    parser.add_argument("--dir", type=Path, default=None, help="批量导入目录")
    parser.add_argument("--vault", type=Path, required=True, help="目标 vault 目录路径")
    parser.add_argument("--tags", type=str, default=None,
                        help='标签列表，逗号分隔，如 "法规,国资,股权激励"')
    parser.add_argument("--domain", type=str, default=None,
                        help='领域名称，覆盖自动从 vault 父目录推导的值')
    parser.add_argument("--source", choices=["user", "agent"], required=True, help="来源: user 或 agent")
    parser.add_argument("--dry-run", action="store_true", help="预览，不实际写入")
    parser.add_argument("--force", action="store_true", help="强制重新导入（覆盖去重检测）")
    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.error("必须指定 <文件> 或 --dir <目录>")

    vault_dir = args.vault.resolve()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    if args.dir:
        success, failed = ingest_directory(
            args.dir, vault_dir, args.source, tags=tags, domain=args.domain,
            dry_run=args.dry_run, force=args.force,
        )
        print(f"\n===== 导入完成 =====")
        print(f"  成功: {success}")
        print(f"  失败: {failed}")
    else:
        success = ingest_file(
            args.file, vault_dir, args.source, tags=tags, domain=args.domain,
            dry_run=args.dry_run, force=args.force,
        )
        if not success:
            sys.exit(1)

    if success and not args.dry_run:
        print(f"\n  重建索引...")
        rebuild_index(vault_dir)
