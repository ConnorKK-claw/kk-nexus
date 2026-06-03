import sys, re, shutil
from pathlib import Path
from collections import defaultdict

base = Path(r'C:\Users\hexk\OneDrive\文档\New project 6\_upgrade_sk')
skills_home = Path.home() / '.codex' / 'skills'

def categorize_node(filename):
    stem = filename.stem
    parts = stem.split('-')
    return parts[3] if len(parts) >= 4 else 'unknown'

def get_freshness(cat):
    return 6 if cat[:2] in ('aa',) else 12

def process_vault(name):
    src = skills_home / name / 'vault'
    kdir = src / 'knowledge'
    dst_kdir = base / f'vault_{name}' / 'knowledge'
    dst_kdir.mkdir(parents=True, exist_ok=True)

    nodes = sorted(kdir.glob('zk-*.md'))
    print(f'  {name}: {len(nodes)} nodes')

    # Copy all nodes to workspace first
    for n in nodes:
        content = n.read_text(encoding='utf-8')
        (dst_kdir / n.name).write_text(content, encoding='utf-8')

    # Build tag groups
    tag_groups = defaultdict(list)
    node_info = {}
    for n in nodes:
        content = n.read_text(encoding='utf-8')
        tags_match = re.search(r'^tags:\s*\[(.+?)\]', content, re.MULTILINE)
        tags = []
        if tags_match:
            tags = [t.strip().strip('"').strip("'") for t in tags_match.group(1).split(',')]
        cat = categorize_node(n)
        node_info[n.name] = {'tags': tags, 'category': cat}
        for tag in tags:
            tag_groups[tag].append(n.name)

    updated = 0
    for n in nodes:
        content = n.read_text(encoding='utf-8')
        if 'freshness_months:' in content:
            # Already has it, just copy to workspace
            (dst_kdir / n.name).write_text(content, encoding='utf-8')
            continue

        info = node_info[n.name]
        cat = info['category']
        freshness = get_freshness(cat)
        tags = info['tags']

        related_ids = []
        seen = set()
        for tag in tags:
            for peer in tag_groups.get(tag, []):
                if peer != n.name and peer not in seen:
                    peer_info = node_info.get(peer, {})
                    peer_cat = peer_info.get('category', '')
                    rel_type = '同级' if peer_cat == cat else ('引用' if peer_cat[:2] == 'aa' else '补充')
                    related_ids.append((peer.replace('.md', ''), rel_type))
                    seen.add(peer)
                    if len(related_ids) >= 5:
                        break
            if len(related_ids) >= 5:
                break

        add_lines = []
        if related_ids:
            add_lines.append('related:')
            for rid, rtype in related_ids:
                add_lines.append(f'  - id: "{rid}"')
                add_lines.append(f'    type: "{rtype}"')
        add_lines.append(f'freshness_months: {freshness}')

        yaml_end = content.find('---', 3)
        if yaml_end != -1:
            yaml_section = content[3:yaml_end]
            pos = yaml_section.rfind('imported_by')
            if pos == -1:
                pos = len(yaml_section)
            else:
                pos = yaml_section.rfind('\n', 0, pos) + 1
            addition = '\n' + '\n'.join(add_lines) + '\n'
            new_yaml = yaml_section[:pos] + addition + yaml_section[pos:]
            new_content = content[:3] + new_yaml + content[yaml_end:]
            (dst_kdir / n.name).write_text(new_content, encoding='utf-8')
            updated += 1

    print(f'  Processed {updated}/{len(nodes)} nodes with new fields')
    return updated

u1 = process_vault('equity-incentive')
u2 = process_vault('tax-compliance-expert')
print(f'\nTotal processed: {u1 + u2}')
print('Files ready in _upgrade_sk/vault_*/')
