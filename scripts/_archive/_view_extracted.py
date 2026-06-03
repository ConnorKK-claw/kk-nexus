import json
d = json.load(open(r'C:\Users\hexk\OneDrive\文档\New project 6\scripts\_exec_grants.json','r',encoding='utf-8'))
for k,v in d.items():
    print(f'=== {k} ({len(v["execs"])} execs, {len(v["cats"])} cats) ===')
    for e in v['execs']:
        print('  '+' | '.join(e))
    if v['total']:
        print('  TOTAL: '+' | '.join(v['total']))
    print()
