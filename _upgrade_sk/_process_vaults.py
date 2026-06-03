import sys, re, shutil
from pathlib import Path
from collections import defaultdict

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
    if not kdir.is_dir():
        return 0

    nodes = sorted(kdir.glob('zk-*.md'))
    print(f'  {name}: {len(nodes)} nodes')

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
            n.write_text(new_content, encoding='utf-8')
            updated += 1
            if updated <= 3:
                rcount = len(related_ids)
                print(f'    {n.name}: freshness={freshness}, related={rcount}')

    print(f'  Updated {updated}/{len(nodes)} nodes')
    return updated

u1 = process_vault('equity-incentive')
u2 = process_vault('tax-compliance-expert')
print(f'\nTotal updated: {u1 + u2}')
