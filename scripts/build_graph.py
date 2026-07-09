#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_graph.py — P1-5: 扫描 vault knowledge/ 节点的 related 字段生成 mermaid 知识图谱。

用法:
    python scripts/build_graph.py
    python scripts/build_graph.py --output KNOWLEDGE_GRAPH.md
    python scripts/build_graph.py --vault <vault-path>  # 单 vault

输出 mermaid graph 代码块，可嵌入 Markdown（Obsidian/VSCode 预览可渲染）。
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_frontmatter_simple(content: str) -> dict:
    """简易 frontmatter 解析（只提取标量字段和 related JSON）。"""
    meta = {}
    if not content.startswith("---"):
        return meta
    parts = content.split("---", 2)
    if len(parts) < 3:
        return meta
    fm_text = parts[1].strip()
    for line in fm_text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key == "related" and val:
            # related 是 JSON 字符串
            try:
                meta[key] = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                meta[key] = []
        else:
            meta[key] = val
    return meta


def discover_vaults() -> list:
    """从 UNIFIED_INDEX.md 发现所有 vault 路径。"""
    from txtai_utils import vault_paths
    return vault_paths()


def scan_vault_nodes(vault_path: Path) -> tuple:
    """扫描单个 vault 的 knowledge/ 节点，返回 (nodes, edges)。

    Returns:
        nodes: {node_id: {tags, domain, title}}
        edges: [(source, target, label)]
    """
    nodes = {}
    edges = []
    knowledge_dir = vault_path / "knowledge"
    if not knowledge_dir.is_dir():
        return nodes, edges
    for f in sorted(knowledge_dir.glob("zk-*.md")):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        meta = parse_frontmatter_simple(content)
        node_id = f.stem
        tags_raw = meta.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        nodes[node_id] = {
            "tags": tags,
            "domain": meta.get("domain", ""),
            "title": meta.get("title", node_id),
        }
        related = meta.get("related", [])
        if isinstance(related, str):
            try:
                related = json.loads(related)
            except (json.JSONDecodeError, ValueError):
                related = []
        if isinstance(related, list):
            for r in related:
                if isinstance(r, dict) and r.get("id"):
                    edges.append((node_id, r["id"], r.get("type", "")))
    return nodes, edges


def build_mermaid_graph(vaults: list) -> str:
    """扫描所有 vault，生成 mermaid graph 代码。

    为避免节点过多导致图表不可读，限制最多 200 个节点。
    """
    all_nodes = {}
    all_edges = []
    for vp in vaults:
        vault_path = Path(vp)
        if not vault_path.exists():
            continue
        nodes, edges = scan_vault_nodes(vault_path)
        all_nodes.update(nodes)
        all_edges.extend(edges)

    # 限制节点数（避免 mermaid 渲染崩溃）
    max_nodes = 200
    if len(all_nodes) > max_nodes:
        print(f"[WARN] 节点数 {len(all_nodes)} 超过上限 {max_nodes}，仅渲染前 {max_nodes} 个", file=sys.stderr)
        # 保留有边的节点优先
        connected = set()
        for src, tgt, _ in all_edges:
            connected.add(src)
            connected.add(tgt)
        keep = set(list(connected)[:max_nodes])
        all_nodes = {k: v for k, v in all_nodes.items() if k in keep}
        all_edges = [(s, t, l) for s, t, l in all_edges if s in keep and t in keep]

    lines = ["```mermaid", "graph LR"]
    for nid, info in all_nodes.items():
        # 截断过长的节点 ID 用于显示
        display = info.get("title", nid)[:30]
        # 转义 mermaid 特殊字符
        display = display.replace('"', "'").replace("[", "(").replace("]", ")")
        lines.append(f'  {nid[:40]}["{display}"]')
    for src, tgt, label in all_edges:
        label = label.replace("|", "/") if label else ""
        if label:
            lines.append(f'  {src[:40]} -->|{label}| {tgt[:40]}')
        else:
            lines.append(f'  {src[:40]} --> {tgt[:40]}')
    lines.append("```")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="P1-5: 生成知识图谱 mermaid 代码")
    parser.add_argument("--output", type=Path, default=None,
                        help="输出文件路径（默认追加到 UNIFIED_INDEX.md 末尾）")
    parser.add_argument("--vault", type=Path, default=None,
                        help="单个 vault 路径（默认扫描所有 vault）")
    args = parser.parse_args()

    if args.vault:
        vaults = [str(args.vault.resolve())]
    else:
        vaults = discover_vaults()

    if not vaults:
        print("[ERROR] 未发现任何 vault 路径", file=sys.stderr)
        sys.exit(1)

    print(f"扫描 {len(vaults)} 个 vault...", file=sys.stderr)
    mermaid_code = build_mermaid_graph(vaults)

    if args.output:
        args.output.write_text(f"# 知识图谱\n\n{mermaid_code}\n", encoding="utf-8")
        print(f"图谱已写入: {args.output}", file=sys.stderr)
    else:
        # 追加到 UNIFIED_INDEX.md 末尾
        index_path = PROJECT_ROOT / "UNIFIED_INDEX.md"
        if index_path.exists():
            existing = index_path.read_text(encoding="utf-8")
            # 移除旧的图谱块
            existing = re.sub(r'\n*## 知识图谱.*?```$', '', existing, flags=re.S)
            index_path.write_text(existing + f"\n\n## 知识图谱\n\n{mermaid_code}\n", encoding="utf-8")
            print(f"图谱已追加到: {index_path}", file=sys.stderr)
        else:
            print(mermaid_code)


if __name__ == "__main__":
    main()
