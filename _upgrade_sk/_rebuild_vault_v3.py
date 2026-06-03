# -*- coding: utf-8 -*-
from pathlib import Path
base = Path.home() / '.codex' / 'skills' / 'hk-ipo'
vault = base / 'vault'
today = '2026-05-25'

def w(rel, c):
    p = base / rel if not rel.startswith('vault') else vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(c.strip()+'\n', encoding='utf-8')
    print(f'  {rel}: {len(c.encode(\"utf-8\"))}b')

# zk-categories
w('zk-categories.md', '---\ntitle: ZK \u5206\u7c7b\u7801\u6620\u5c04\u8868 - hk-ipo\n...')

# Test single file first
w('vault/knowledge/test-encoding.md', '---\ntitle: \u6d4b\u8bd5\u7f16\u7801\ndate: 2026-05-25\n---\n\n# \u6d4b\u8bd5\u7f16\u7801\n\n\u4e2d\u6587\u6b63\u786e\u663e\u793a\u6d4b\u8bd5')
print('test file written')