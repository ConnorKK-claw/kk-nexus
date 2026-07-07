
# ============================================================
# 域适用范围：通用蒸馏脚本
# 除 005 financial-analysis 使用 distill_fa.py 外，其余域统一使用本脚本。
# ============================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""auto_distill_vault.py — 规则驱动的 raw-knowledge 自动蒸馏。

扫描 vault/raw/ 下 status:raw 的 .md 文件，按文件名分类，
生成 ZK 知识节点到 knowledge/，更新 raw/ 状态。

分类码后缀语义（详见 AGENTS.md）：
  - X0（如 aa0/bb0/gg0）：人工精化的参考级节点，跨公司跨案例的通用知识
  - X（如 aa/bb/dd/gg）：自动蒸馏节点，可能被 cases/ 案例覆盖后标记为 archived
"""
import argparse, hashlib, re, subprocess, sys
from datetime import datetime
from pathlib import Path


# === Domain 推断映射表（vault 路径 → domain 码）===
_VAULT_DOMAIN_MAP = {
    "equity-incentive": "ei",
    "tax-compliance-expert": "tax",
    "weekly-report": "wr",
    "hk-ipo": "hk",
    "financial-analysis": "fa",  # 注意：005 实际用 distill_fa.py，这里仅为完整性
    "serenity-a-share-investor": "asi",
    "trading-agents-007": "ta",
}


def infer_domain_from_vault(vault_path) -> str:
    """根据 vault 路径中包含的 skill 名推断 domain 码。

    参数:
        vault_path: Path 对象或字符串，vault 根目录路径

    返回:
        domain 码字符串（如 "ei"/"tax"/"wr"/"hk"/"asi"/"ta"）
        若路径不匹配任何 skill 名，返回 "ei" 并打印警告（向后兼容）
    """
    path_str = str(vault_path).replace("\\", "/").lower()
    for skill_name, domain in _VAULT_DOMAIN_MAP.items():
        if skill_name in path_str:
            return domain
    print(f"[警告] 无法从 vault 路径推断 domain: {vault_path}，回退到 'ei'")
    return "ei"


# Domain 码 → 显示名映射（用于 frontmatter domain 字段）
_DOMAIN_DISPLAY_MAP = {
    "ei": "equity-incentive",
    "tax": "tax-compliance-expert",
    "wr": "weekly-report",
    "hk": "hk-ipo",
    "fa": "financial-analysis",
    "asi": "serenity-a-share-investor",
    "ta": "trading-agents-007",
}


def get_domain_display(domain_code: str) -> str:
    """domain 码 → 显示名（用于 frontmatter）。"""
    return _DOMAIN_DISPLAY_MAP.get(domain_code, "equity-incentive")


def find_zk_categories(vault_path) -> "Path | None":
    """查找 vault 的 zk-categories.md 文件。

    依次查找以下位置（兼容 9 个 vault 的非标准位置）：
    1. <vault>/zk-categories.md
    2. <vault>/knowledge/zk-categories.md
    3. <skill_root>/zk-categories.md（vault 的父目录）

    返回:
        找到的 Path 对象，或 None
    """
    from pathlib import Path
    vault = Path(vault_path)
    candidates = [
        vault / "zk-categories.md",
        vault / "knowledge" / "zk-categories.md",
        vault.parent / "zk-categories.md",  # skill 根目录
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def load_categories_from_md(zk_cat_path) -> dict:
    """解析 zk-categories.md 中的「分类码 → 标签」映射。

    支持两种格式：
    1. markdown 表格：`| code | label |`
    2. 行格式：`code: label` 或 `code = label`

    返回:
        dict: {分类码: 标签}，如 {"aa0": "法规类", "bb0": "案例类"}
        解析失败返回空 dict
    """
    from pathlib import Path
    result = {}
    try:
        with open(zk_cat_path, "r", encoding="utf-8") as f:
            content = f.read()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 尝试 markdown 表格行：| code | label |
            if line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                # parts[0] 和 parts[-1] 为空（首尾 |）
                parts = [p for p in parts if p]
                if len(parts) >= 2 and parts[0] not in ("code", "码", "-"):
                    # 跳过分隔行 |---|---| 和表头
                    if parts[0].replace("-", "").replace(":", "").strip():
                        continue
                    code, label = parts[0], parts[1]
                    if code and not code.startswith("-"):
                        result[code] = label
                continue
            # 尝试 code: label 或 code = label
            for sep in (":", "="):
                if sep in line:
                    idx = line.index(sep)
                    code = line[:idx].strip()
                    label = line[idx+1:].strip()
                    if code and label and not code.startswith("#"):
                        result[code] = label
                    break
    except Exception as e:
        print(f"[警告] 解析 zk-categories.md 失败: {e}")
    return result


# 公告碎片关键词（严格版）：匹配后将被跳过蒸馏
FRAGMENT_KEYWORDS = [
    "法律意见书", "律师意见",
    "自查报告",
    "通知债权人", "催告",
    "回购注销实施公告",
    "核查意见",
    "公示情况说明", "公示情况",
]

# 股票代码正则
STOCK_CODE_RE = re.compile(r"(\d{6})")


def is_fragment_announcement(meta: dict, filename: str) -> bool:
    """判断 raw 文件是否为公告碎片（已有案例覆盖的冗余公告）。"""
    if not meta:
        return False
    title = meta.get("title", "")
    search_text = f"{filename} {title}"
    if not any(kw in search_text for kw in FRAGMENT_KEYWORDS):
        return False
    return bool(STOCK_CODE_RE.search(filename))


def has_case_coverage(vault, filename: str, meta: dict | None = None) -> str | None:
    """检查 cases/ 目录是否已有同名/同代码案例覆盖。"""
    cases_dir = vault / "cases"
    if not cases_dir.is_dir():
        return None
    code_match = STOCK_CODE_RE.search(filename)
    stock_code = code_match.group(1) if code_match else None
    company_name = None
    if stock_code:
        m = re.search(rf"{stock_code}-[a-z]{{2}}-(.+?)-", filename)
        if m:
            company_name = m.group(1)
    if not stock_code and not company_name:
        return None
    for case_file in sorted(cases_dir.glob("*.md")):
        cn = case_file.stem
        if stock_code and stock_code in cn:
            return case_file.name
        if company_name and company_name in cn:
            return case_file.name
    return None


def resolve_vault(args_vault):
    if args_vault:
        return Path(args_vault).resolve()
    hv = Path.home() / ".codex" / "skills" / "equity-incentive" / "vault"
    if hv.is_dir():
        return hv
    for p in [Path.cwd()] + list(Path.cwd().parents):
        if (p / "vault").is_dir():
            return p / "vault"
    return hv


def next_zk_id(vault: Path, domain: str, catseq: str) -> int:
    knowledge_dir = vault / "knowledge"
    if not knowledge_dir.is_dir():
        return 0
    pattern = re.compile(rf"^zk-{re.escape(domain)}-{re.escape(catseq)}-(\d+)-.+\.md$")
    max_seq = -1
    for f in knowledge_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            seq = int(m.group(1))
            if seq > max_seq:
                max_seq = seq
    return max_seq + 1


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = text.strip("-_")
    return text[:60]


def parse_frontmatter(content: str):
    """Return (meta_dict, body_text)."""
    content = content.strip()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            meta = {}
            for line in fm_text.split(chr(10)):
                line = line.strip()
                if chr(58) in line:
                    key, _, val = line.partition(chr(58))
                    key = key.strip()
                    val = val.strip()
                    if val.startswith(chr(91)) and val.endswith(chr(93)):
                        items = val[1:-1].split(chr(44))
                        cleaned = []
                        for v in items:
                            v = v.strip()
                            v = v.strip(chr(34)).strip(chr(39))
                            if v:
                                cleaned.append(v)
                        meta[key] = cleaned
                    else:
                        meta[key] = val.strip(chr(34)).strip(chr(39))
            return meta, body
    return {}, content


def classify_filename(name: str, zk_categories: dict = None):
    """Classify raw filename - (target_subdir, catseq).

    优先级：
    1. zk_categories（来自 zk-categories.md 专属蒸馏协议）：按标签关键字匹配
    2. 硬编码规则（向后兼容）

    Args:
        name: 原始文件名
        zk_categories: dict {分类码: 标签}，如 {"aa": "法规类", "aa0": "法规框架(证监会/联交所)"}
            None 或空 dict 时走硬编码逻辑。

    Returns:
        ("knowledge" or "templates", catseq_string)
    """
    # Remove extension and suffixes like -user, -agent
    basename = name.replace(".md", "")
    for suffix in ["-user", "-agent", "-distilled"]:
        if basename.endswith(suffix):
            basename = basename[: -len(suffix)]

    # Rule 0: zk-categories.md 专属蒸馏协议（优先）
    # 按 zk-categories.md 中标签的关键字匹配文件名，命中则用该分类码
    if zk_categories:
        for code, label in zk_categories.items():
            # catseq 去掉末尾数字（"aa0" -> "aa"，保留 "aa" 不变）
            catseq = re.sub(r"\d+$", "", code)
            if not catseq:
                continue
            # 从 label 中提取关键字候选：
            # 优先匹配括号内关键字（如 "法规框架(证监会/联交所)" -> "证监会/联交所"）
            m = re.search(r"[（(]([^）)]+)[）)]", label)
            kw_str = m.group(1) if m else label
            # 按斜杠/顿号分隔关键字
            for kw in re.split(r"[/／、]", kw_str):
                kw = kw.strip()
                # 关键字长度 >=3 才匹配，避免"数据"等过宽词误匹配
                if len(kw) >= 3 and kw in basename:
                    return ("knowledge", catseq)

    # Rule 1: Templates (硬编码回退)
    if "template" in basename.lower() or chr(27169) in basename:  # 模板
        return ("templates", "")

    # Rule 2: Regulations - aa
    reg_keywords = [chr(27861), chr(21150), chr(25351), chr(24333),  # 法规办法指引
                    chr(36890), chr(34701), chr(38382), chr(35299),  # 通知规则问答
                    chr(35299), chr(21063), chr(20934),              # 规则准则
                    ]
    if any(kw in basename for kw in reg_keywords):
        return ("knowledge", "aa")

    # Rule 3: Case/market stats - dd (行业对标)
    case_keywords = [chr(26680), chr(20363), chr(24066), chr(35722),  # 案例市场反应
                     chr(32479), chr(35745)]                          # 统计
    if any(kw in basename for kw in case_keywords):
        return ("knowledge", "dd")

    # Rule 4: Executive compensation - dd
    comp_keywords = [chr(39640), chr(31649), chr(34218), chr(32937),  # 高管薪酬持股
                     chr(25345)]                                      # 持
    if any(kw in basename for kw in comp_keywords):
        return ("knowledge", "dd")

    # Rule 5: Assessment/calculation - bb (操作实务)
    calc_keywords = [chr(32771), chr(26680), chr(27979), chr(31639),  # 考核测算
                     chr(25351), chr(26631)]                          # 指标
    if any(kw in basename for kw in calc_keywords):
        return ("knowledge", "bb")

    # Rule 6: Company name + plan/draft - bb
    company_chars = set(chr(x) for x in range(19968, 40908))  # CJK Unified
    has_cjk = any(c in basename for c in [chr(22269), chr(22823), chr(19978)])  # 国 大 上
    plan_keywords = [chr(33609), chr(26680), chr(35336), chr(27861)]  # 草案方案计划
    if has_cjk and any(kw in basename for kw in plan_keywords):
        return ("knowledge", "bb")

    # Rule 7: Company name + announcement/legal - bb
    notice_keywords = [chr(20844), chr(21578), chr(24037), chr(24471),  # 公告批复法律
                       chr(24863), chr(30465), chr(23457),              # 意见自查报告
                       chr(25253), chr(21512), chr(26680),              # 名单登记
                       chr(23454), chr(32463)]                          # 上市
    if has_cjk and any(kw in basename for kw in notice_keywords):
        return ("knowledge", "bb")

    # Default: gg (外部知识)
    return ("knowledge", "gg")


def build_frontmatter(orig_meta: dict, body: str, vault: Path, target: str, catseq: str) -> str:
    """Build ZK knowledge node frontmatter + full body."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Generate ZK ID
    domain = infer_domain_from_vault(vault)
    seq = 0
    if target == "knowledge":
        seq = next_zk_id(vault, domain, catseq)
    title = orig_meta.get("title", "untitled")
    slug = slugify(title)
    zk_id = f"zk-{domain}-{catseq}-{seq}-{slug}"

    tags = orig_meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if "auto-distilled" not in tags:
        tags.append("auto-distilled")

    source_hash = orig_meta.get("source_hash", hashlib.md5(body.encode("utf-8")).hexdigest()[:16])
    original_source = orig_meta.get("original_source", orig_meta.get("source", "user"))
    orig_date = orig_meta.get("date", datetime.now().strftime("%Y-%m-%d"))

    lines = ["---"]
    lines.append(f"title: {title}")
    lines.append(f"date: {orig_date}")
    lines.append(f"source: distilled")
    lines.append(f"original_source: {original_source}")
    lines.append(f"domain: {get_domain_display(domain)}")
    lines.append(f"tags: [{', '.join(tags)}]")
    lines.append(f"status: distilled")
    lines.append(f"imported_by: auto_distill_vault.py")
    lines.append(f"imported_at: {now}")
    lines.append(f"original_status: raw")
    lines.append(f"source_hash: {source_hash}")
    lines.append(f"distilled_zk_id: {zk_id}")
    lines.append("---")
    lines.append("")
    lines.append(body)

    return chr(10).join(lines), zk_id


def update_raw_status(raw_path: Path, status: str = "distilled"):
    """Update status field in raw file frontmatter."""
    content = raw_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False
    end = content.find("---", 3)
    if end == -1:
        return False
    fm = content[3:end]
    # Replace or add status line
    if re.search(r"^status:", fm, re.M):
        fm = re.sub(r"^status:.*$", f"status: {status}", fm, flags=re.M)
    else:
        fm = fm.rstrip() + chr(10) + f"status: {status}"
    new_content = "---" + fm + "---" + content[end + 3:]
    raw_path.write_text(new_content, encoding="utf-8")
    return True


def run_build_index(vault: Path):
    """Rebuild knowledge/index.md."""
    script = Path(__file__).parent / "build_index.py"
    if script.exists():
        subprocess.run([sys.executable, str(script), str(vault)], capture_output=True)


def main():
    parser = argparse.ArgumentParser(description="Auto-distill raw vault files to knowledge nodes")
    parser.add_argument("--vault", help="Vault path (default: auto-detect)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview only")
    parser.add_argument("--limit", type=int, default=0, help="Max files to process (0 = all)")
    args = parser.parse_args()

    if args.vault:
        vault = Path(args.vault).resolve()
    else:
        vault = resolve_vault(args.vault)

    raw_dirs = [
        vault / "raw" / "user",
        vault / "raw" / "agent",
    ]

    # 尝试从 zk-categories.md 读取分类规则（仅用于日志提示，不强制改分类逻辑）
    zk_cat = find_zk_categories(vault)
    zk_categories = load_categories_from_md(zk_cat) if zk_cat else {}
    if zk_categories:
        print(f"[信息] 已加载 zk-categories.md: {zk_cat.name}（{len(zk_categories)} 个分类）")

    # Collect all status:raw .md files
    raw_files = []
    for rd in raw_dirs:
        if rd.is_dir():
            for f in sorted(rd.rglob("*.md")):
                if f.name == ".gitkeep":
                    continue
                try:
                    content = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                meta, _ = parse_frontmatter(content)
                if meta.get("status", "raw") == "raw":
                    raw_files.append((f, meta))

    if not raw_files:
        print(f"[distill-vault] No raw files to distill in {vault}")
        return 0

    # Fragment detection (pre-classification)
    fragment_skips = []
    for f, meta in raw_files:
        if is_fragment_announcement(meta, f.name):
            case_file = has_case_coverage(vault, f.name, meta)
            if case_file:
                fragment_skips.append((f, meta, case_file))

    # Classify (after removing fragments)
    # 传入 zk_categories 让 classify_filename 优先按专属蒸馏协议匹配
    rf_filtered = [(f, m) for f, m in raw_files if f.name not in {x[0].name for x in fragment_skips}]
    classified = []
    counts = {}
    zk_hit_count = 0  # 统计 zk-categories.md 命中数
    for f, meta in rf_filtered:
        target, catseq = classify_filename(f.name, zk_categories)
        classified.append((f, meta, target, catseq))
        key = f"{target}/{catseq}" if catseq else target
        counts[key] = counts.get(key, 0) + 1
        # 检测是否命中 zk_categories（用于摘要统计）
        if zk_categories and target == "knowledge":
            for code, label in zk_categories.items():
                zk_catseq = re.sub(r"\d+$", "", code)
                if zk_catseq == catseq:
                    m = re.search(r"[（(]([^）)]+)[）)]", label)
                    kw_str = m.group(1) if m else label
                    for kw in re.split(r"[/／、]", kw_str):
                        kw = kw.strip()
                        if len(kw) >= 3 and kw in f.name.replace(".md", ""):
                            zk_hit_count += 1
                            break
                    break

    print(f"[distill-vault] {len(rf_filtered)} raw files to distill")
    print(f"  Classification:")
    for key in sorted(counts.keys()):
        print(f"    {key}: {counts[key]}")
    if fragment_skips:
        print(f"  [碎片过滤] {len(fragment_skips)} 个公告碎片将被跳过（已有案例覆盖）")
        for f, _, case_file in fragment_skips:
            print(f"    SKIP {f.name[:60]} -> 已整合到 {case_file}")

    if args.limit > 0:
        classified = classified[:args.limit]
        print(f"  (limit={args.limit})")

    if args.dry_run:
        print(f"  [DRY-RUN] Would process {len(classified)} files")
        for f, meta, target, catseq in classified[:10]:
            title = meta.get("title", f.name)[:50]
            print(f"    {target}/{catseq} -> {title}")
        if fragment_skips:
            print(f"  [碎片过滤] {len(fragment_skips)} 个公告碎片将被跳过（dry-run 仅预览）")
            for f, _, case_file in fragment_skips:
                print(f"    SKIP {f.name[:60]} -> 已整合到 {case_file}")
        if len(classified) > 10:
            print(f"    ... and {len(classified)-10} more")
        return 0

    # Process
    created = 0
    skipped = 0
    errors = 0  # 蒸馏失败计数（用于 [summary] 行）

    # Archive fragment raw files
    now_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for f, meta, case_file in fragment_skips:
        try:
            raw_content = f.read_text(encoding="utf-8")
            if re.search(r"^status:", raw_content, re.M):
                raw_content = re.sub(r"^status:.*$", "status: archived", raw_content, flags=re.M)
            end = raw_content.find("---", 3)
            if end != -1:
                arch_note = f"\narchived_reason: 公告碎片，已整合到 cases/{case_file}" + f"\narchived_at: {now_ts}"
                raw_content = raw_content[:end] + arch_note + raw_content[end:]
            f.write_text(raw_content, encoding="utf-8")
            print(f"  [ARCHIVED-RAW] {f.name[:60]} -> (标记 archived)")
            skipped += 1
        except Exception as e:
            print(f"  [ERR] 标记碎片失败 {f.name}: {e}")
            errors += 1

    # Normal distillation loop
    for f, meta, target, catseq in classified:
        try:
            content = f.read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)
            new_content, zk_id = build_frontmatter(meta, body, vault, target, catseq)

            # Write to target directory
            if target == "templates":
                target_dir = vault / "templates"
                out_name = f"{slugify(meta.get('title', 'untitled'))}.md"
            else:
                target_dir = vault / "knowledge"
                out_name = f"{zk_id}.md"

            target_dir.mkdir(parents=True, exist_ok=True)
            out_path = target_dir / out_name

            # Skip if already exists
            if out_path.exists():
                print(f"  [SKIP] {out_path.name} already exists")
                skipped += 1
                continue

            out_path.write_text(new_content, encoding="utf-8")

            # Update raw status
            update_raw_status(f)

            created += 1
            print(f"  [OK] {f.name[:50]:50s} -> {out_path.name[:55]}")

        except Exception as e:
            print(f"  [ERR] {f.name}: {e}")
            skipped += 1
            errors += 1

    # Rebuild index
    if created > 0 or fragment_skips:
        run_build_index(vault)

    print(f"\n[distill-vault] Done: {created} created, {skipped} skipped/archived")
    # 显式摘要行（供 distill_runner 解析，键名 processed/generated/skipped/errors）
    print(f"[summary] processed={len(rf_filtered)} generated={created} skipped={skipped} errors={errors}")
    if zk_categories:
        print(f"[info] zk-categories 命中: {zk_hit_count}/{len(rf_filtered)} 文件使用专属蒸馏协议")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# === 蒸馏溯源记录 (CODEX E1) ===

def _write_distilled_trace(vault_path, source_rel, nodes, script_name="auto_distill_vault.py"):
    """Write .distilled.json trace record after distillation."""
    import json
    from datetime import datetime
    trace_dir = Path(vault_path) / ".distilled"
    trace_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(source_rel).stem
    trace_file = trace_dir / f"{safe_name}.json"
    record = {
        "source": source_rel,
        "distilled_at": datetime.now().isoformat(),
        "nodes": nodes[:50],
        "script": script_name,
        "status": "success"
    }
    trace_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
