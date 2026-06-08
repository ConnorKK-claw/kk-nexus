import sys, os
sys.stdout.reconfigure(encoding='utf-8')

KNOWLEDGE = os.path.join(os.path.dirname(__file__), '..', 'vault', 'knowledge')
INDEX = os.path.join(KNOWLEDGE, 'index.md')
TODAY = '2026-06-06'

new_nodes = [
    'zk-asi-company-registry.md',
    'zk-asi-pool-index.md',
    'zk-asi-layer-index.md',
    'zk-asi-data-inventory.md',
    'zk-asi-kk0-0-pools-scan-2026-06-06.md',
]

if os.path.exists(INDEX):
    content = open(INDEX, 'r', encoding='utf-8').read()
else:
    content = f'---\\ntitle: \u77e5\u8bc6\u7d22\u5f15\\ndate: {TODAY}\\nsource: agent\\n---\\n\\n# ASI \u77e5\u8bc6\u7d22\u5f15\\n\\n'

section_marker = '## \u81ea\u52a8\u751f\u6210\u8282\u70b9'
if section_marker not in content:
    content += f'\\n{section_marker}\\n\\n'

for node in new_nodes:
    if node not in content:
        content += f'- [{node}]({node})\\n'
        print(f'  Added: {node}')
    else:
        print(f'  Exists: {node}')

with open(INDEX, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'\\nUpdated: {INDEX}')

# Also update SESSION-STATE.md
SS = os.path.join(os.path.dirname(__file__), '..', 'SESSION-STATE.md')
ss_content = f'# Session State - {TODAY} (Full Crawl Complete)\
\\n## Completed\\
- L1+L2+L3+L4 crawl for all 13 layers, 228 stocks\\
- Pool classification v3 (core-moat: 108, low-val: 0, high-growth: 104, sector-leader: 26, power-upstream: 4)\\n- Index nodes: company-registry, pool-index, layer-index, data-inventory\\
- Valuation CSV (228, 177 with L3 proxy)\\n- Guidance CSV (228, 20 with PE<=3y digest)\\n\\n## Pending\\
- L5 (AKShare research) - not yet implemented in pipeline\\
- Individual case analysis for pool stocks\\
- Manual moat verification for core-moat pool (replace proxy)\\n- Wind expansion verification (228 stocks, 13 layers)\\n\\n---\\nData sources: 2026-06-06-asi-* CSVs in vault/raw/agent/\\nLatest crawl: {TODAY} 22:00\\n'
with open(SS, 'w', encoding='utf-8') as f:
    f.write(ss_content)
print(f'Updated: SESSION-STATE.md')
print('Done!')
