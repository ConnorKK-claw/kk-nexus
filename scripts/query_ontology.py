"""
query_ontology.py — 查询 ontology 图谱

用法:
    python query_ontology.py                          # 列出所有 vault
    python query_ontology.py --type Company            # 列出所有公司
    python query_ontology.py --type Regulation         # 列出所有法规
    python query_ontology.py --domain equity-incentive # 按领域过滤
    python query_ontology.py --keyword 上海            # 跨类型属性搜索
    python query_ontology.py --json                   # JSON 输出

数据源: ~/.codex/memories/ontology/graph.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

ONTOLOGY_FILE = Path.home() / ".codex" / "memories" / "ontology" / "graph.jsonl"


def load_entities() -> list[dict]:
    """加载所有 ontology 实体。"""
    if not ONTOLOGY_FILE.exists():
        print(f"[提示] ontology 文件不存在: {ONTOLOGY_FILE}")
        return []

    entities = []
    with open(ONTOLOGY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entities.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entities


def list_entities(type_name: str | None = None, domain: str | None = None,
                  company: str | None = None, keyword: str | None = None) -> list[dict]:
    """
    列出匹配的实体。
    返回 list[dict]，每个 dict 包含 entity['type'] 和 entity['properties']。
    """
    raw_entities = load_entities()
    results = []

    for raw in raw_entities:
        entity = raw.get("entity", raw)
        t = entity.get("type", "")
        props = entity.get("properties", {})

        # 类型过滤
        if type_name and t != type_name:
            continue

        # 领域过滤
        if domain:
            v = props.get("domain", "")
            if domain not in v:
                continue

        # 公司匹配
        if company:
            comp = props.get("company", props.get("name", ""))
            if company not in comp:
                continue

        # 关键词模糊搜索（跨所有属性）
        if keyword:
            all_vals = " ".join(str(v) for v in props.values())
            if keyword not in all_vals:
                continue

        results.append({
            "type": t,
            "id": entity.get("id", "?"),
            "properties": props
        })

    return results


def format_results(results: list[dict]) -> str:
    """格式化输出。"""
    if not results:
        return "(无匹配结果)"

    lines = [f"找到 {len(results)} 个匹配实体:\n"]

    for r in results:
        t = r["type"]
        p = r["properties"]
        eid = r["id"]

        if t == "Company":
            lines.append(f"  [{t}] {p.get('name', '?')}")
            lines.append(f"    代码: {p.get('code', '—')}")
            lines.append(f"    行业: {p.get('industry', '—')}")
            lines.append(f"    状态: {p.get('status', '—')}")

        elif t == "Regulation":
            lines.append(f"  [{t}] {p.get('abbr', '?')}")
            lines.append(f"    名称: {p.get('name', '—')}")
            lines.append(f"    年份: {p.get('year', '—')}")
            lines.append(f"    发文: {p.get('issuer', '—')}")
            lines.append(f"    领域: {p.get('domain', '—')}")

        elif t == "Document":
            lines.append(f"  [{t}] {p.get('title', '?')}")
            lines.append(f"    领域: {p.get('domain', '—')}")
            lines.append(f"    状态: {p.get('status', '—')}")

        elif t == "Vault":
            lines.append(f"  [{t}] {p.get('name', '?')}")
            lines.append(f"    领域: {p.get('domain', '—')}")
            lines.append(f"    路径: {p.get('path', '—')}")
            if p.get("company"):
                lines.append(f"    公司: {p['company']}")

        else:
            lines.append(f"  [{t}] {p.get('name', p.get('title', eid))}")
            for k, v in p.items():
                lines.append(f"    {k}: {v}")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查询 ontology 图谱")
    parser.add_argument("--type", default=None, help="实体类型 (Company/Regulation/Document/Vault)")
    parser.add_argument("--domain", default=None, help="按领域过滤")
    parser.add_argument("--company", default=None, help="按公司匹配")
    parser.add_argument("--keyword", default=None, help="跨所有属性模糊搜索")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    results = list_entities(
        type_name=args.type,
        domain=args.domain,
        company=args.company,
        keyword=args.keyword
    )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(format_results(results))
